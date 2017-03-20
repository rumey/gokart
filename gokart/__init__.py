import bottle
import dotenv
import os
import pytz
import shutil
import subprocess
import tempfile
import uwsgi
import requests
from datetime import datetime,timedelta
import re
import smtplib
import json
import pytesseract
import hashlib
import base64
try:
    from PIL import Image
except:
    import Image
from datetime import datetime,timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

dotenv.load_dotenv(dotenv.find_dotenv())

from . import s3
from .ftp import BomFTP

bottle.TEMPLATE_PATH.append('./gokart')
bottle.debug(True)

BASE_PATH = os.path.dirname(__file__)

BASE_DIST_PATH = os.path.join(os.path.dirname(BASE_PATH),"dist")


ENV_TYPE = (os.environ.get("ENV_TYPE") or "prod").lower()

gdalinfo = subprocess.check_output(["gdalinfo", "--version"])

# serve up map apps
@bottle.route('/<app>')
def index(app):
    print([x for x in bottle.request.headers.items()])
    print(bottle.request.headers.get('X-email', 'ohnoes'))
    return bottle.template('index.html', app=app,envType=ENV_TYPE)

# WMS shim for Himawari 8
# Landgate tile servers, round robin
FIREWATCH_TZ = pytz.timezone('Australia/Perth')
FIREWATCH_SERVICE = "/mapproxy/firewatch/service"
FIREWATCH_GETCAPS = FIREWATCH_SERVICE + "?service=wms&request=getcapabilities"
HTTPS_VERIFY = os.environ.get("HTTPS_VERIFY") or "True"
HTTPS_VERIFY = True if HTTPS_VERIFY.lower() in ["true","on","yes"] else (False if HTTPS_VERIFY.lower() in ["False","off","no"] else HTTPS_VERIFY )


profile_re = re.compile("gokartProfile\s*=\s*(?P<profile>\{.+\})\s*;?\s*exports.+default.+gokartProfile",re.DOTALL)
@bottle.route("/profile/<app>/<dist>")
def profile(app,dist):
    #get app profile
    profile = None
    appPath = os.path.join(BASE_DIST_PATH,dist,"{}.js".format(app))
    if not os.path.exists(appPath):
        raise Exception("Application({}<{}>) not found".format(app,dist))

    key = "{}_{}_profile".format(app,dist)
    
    if uwsgi.cache_exists(key):
        profile = uwsgi.cache_get(key)
    
    if profile:
        profile = json.loads(profile)
        if repr(os.path.getmtime(appPath)) != profile["mtime"] or os.path.getsize(appPath) != profile["size"]:
            profile = None

    if not profile:
        with open(appPath,"rb") as f:
            m = profile_re.search(f.read())
            profile = m.group("profile") if m else "{}"

        profile = {
            'mtime':repr(os.path.getmtime(appPath)),
            'size':os.path.getsize(appPath),
            'profile':json.loads(profile)
        }
        uwsgi.cache_set(key, json.dumps(profile))

    #get vendor md5
    vendorPath = os.path.join(BASE_DIST_PATH,dist,"vendor.js")
    if not os.path.exists(vendorPath):
        raise Exception("Vendor library({}) not found".format(dist))
    key = "{}_{}_profile".format("vendor",dist)

    vendorProfile = None
    if uwsgi.cache_exists(key):
        vendorProfile = uwsgi.cache_get(key)
    
    if vendorProfile:
        vendorProfile = json.loads(vendorProfile)
        if repr(os.path.getmtime(vendorPath)) != vendorProfile["mtime"] or os.path.getsize(vendorPath) != vendorProfile["size"]:
            vendorProfile = None

    if not vendorProfile:
        m = hashlib.md5()
        with open(vendorPath,"rb") as f:
            m.update(f.read())
        vendorProfile = {
            'mtime':repr(os.path.getmtime(vendorPath)),
            'size':os.path.getsize(vendorPath),
            'vendorMD5':base64.b64encode(m.digest())
        }
        uwsgi.cache_set(key, json.dumps(vendorProfile))

    profile["profile"]["build"]["vendorMD5"] = vendorProfile["vendorMD5"]

    bottle.response.set_header("Content-Type", "application/json")
    return profile["profile"]

@bottle.route("/hi8/<target>")
def himawari8(target):
    baseUrl = bottle.request.url[0:bottle.request.url.find("/hi8")]
    if uwsgi.cache_exists("himawari8"):
        getcaps = uwsgi.cache_get("himawari8")
    else:
        getcaps = requests.get("{}{}".format(baseUrl,FIREWATCH_GETCAPS),verify=HTTPS_VERIFY).content
        uwsgi.cache_set("himawari8", getcaps, 60*10)  # cache for 10 mins
    getcaps = getcaps.decode("utf-8")
    layernames = re.findall("\w+HI8\w+{}\.\w+".format(target), getcaps)
    layers = []
    for layer in layernames:
        layers.append([FIREWATCH_TZ.localize(datetime.strptime(re.findall("\w+_(\d+)_\w+", layer)[0], "%Y%m%d%H%M")).isoformat(), layer])
    result = {
        "servers": [baseUrl + FIREWATCH_SERVICE],
        "layers": layers
    }
    return result


session_key_header = "X-Session-Key"
sso_cookie_name = os.environ.get("SSO_COOKIE_NAME") or "oim_dpaw_wa_gov_au_sessionid"

def get_session_cookie():
    """ 
    Get the session cookie from user request for sso
    if not found, return None
    """
    try:
        #import ipdb;ipdb.set_trace()
        session_key = bottle.request.get_header(session_key_header)
        if session_key:
            return session_key
        else:
            raise bottle.HTTPError(status=401)
    except:
        raise bottle.HTTPError(status=401)

def get_file_md5(f):
    get_md5 = subprocess.Popen(["md5sum",f], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    get_md5_output = get_md5.communicate()

    if get_md5.returncode != 0:
        raise bottle.HTTPError(status=500,body="Generate file md5 failed.{}".format(get_md5_output[1]))

    return get_md5_output[0].split()[0]


basetime_url = os.environ.get("BOM_BASETIME_URL") or "https://kmi.dpaw.wa.gov.au/geoserver/bom/wms?service=WMS&version=1.1.0&request=GetMap&styles=&bbox=70.0,-55.0,195.0,20.0&width=768&height=460&srs=EPSG:4283&format=image%2Fgif&layers={}"
basetime_re = re.compile("(\d{4})-(\d{2})-(\d{2})\s*(\d{2})\D*(\d{2})\s*(UTC)")
def getTimelineFromLayer(target,current_timeline):
    basetimeLayer = bottle.request.query.get("basetimelayer")
    timelineSize = bottle.request.query.get("timelinesize")
    layerTimespan = bottle.request.query.get("layertimespan") # in seconds
    if not basetimeLayer or not timelineSize or not layerTimespan:
        return None

    timelineSize = int(timelineSize)
    layerTimespan = int(layerTimespan)

    #import ipdb;ipdb.set_trace()
    localfile = None
    try:
        localfile = tempfile.NamedTemporaryFile(mode='w+b',delete=False,prefix=basetimeLayer.replace(":","_"),suffix=".gif").name
        subprocess.check_call(["curl","-G","--cookie","{}={}".format(sso_cookie_name,get_session_cookie()),basetime_url.format(basetimeLayer),"--output",localfile])
        md5 = get_file_md5(localfile)
        
        if current_timeline and current_timeline["md5"] == md5:
            return current_timeline
        else:
            img = Image.open(localfile)
            img.load()
            basetimestr = pytesseract.image_to_string(img,lang="bom")
            m = basetime_re.search(basetimestr,re.I)
            if not m:
                raise bottle.HTTPError(status=500,body="Can't extract the base time from base time layer.")
            basetime = datetime(int(m.group(1)),int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)),0,0,tzinfo=pytz.timezone(m.group(6)))
            now = datetime.now(pytz.timezone('UTC'))
            if basetime > now:
                raise bottle.HTTPError(status=500,body="Extract the wrong base time from base time layer.")
            
            if (now - basetime).seconds > 86400:
                raise bottle.HTTPError(status=500,body="Extract the wrong base time from base time layer.")

            if basetime.year != int(m.group(1))  or basetime.month != int(m.group(2)) or  basetime.day != int(m.group(3)) or basetime.hour != int(m.group(4)) or basetime.minute != int(m.group(5)):
                raise bottle.HTTPError(status=500,body="Extract the wrong base time from base time layer.")

            basetime = basetime.astimezone(pytz.timezone("Australia/Perth"))

            layers = []
            layertime = None
            layerId = None
            for i in xrange(0,timelineSize):
                layertime = basetime + timedelta(seconds=layerTimespan * i)
                layerId = (target + "{0:0>3}").format(i)

                layers.append([layertime.strftime("%a %b %d %Y %H:%M:%S AWST"),layerId,None])
            return {"refreshtime":datetime.now().strftime("%a %b %d %Y %H:%M:%S"),"layers":layers,"md5":md5,"updatetime":basetime.strftime("%a %b %d %Y %H:%M:%S AWST")}
    finally:
        if localfile:
            os.remove(localfile)


def getTimelineFromFtp(target,current_timeline):
    remotefile = bottle.request.query.get("datafile")
    if not remotefile: 
        return None

    localfile = None
    mdtm = None
    try:
        with BomFTP() as bomFTP:
            mdtm = bomFTP.getMdtm(remotefile)

            if not current_timeline or current_timeline["mdtm"] != mdtm:
                #no cached timeline or timeline data is changed
                remotefilename = os.path.split(remotefile)[1]
                remotefile_ext = (lambda f,pos: (f[0:],"") if pos == -1 else (f[0:pos],f[pos:]))(remotefilename,remotefilename.index("."))

                localfile = tempfile.NamedTemporaryFile(mode='w+b',delete=False,prefix=remotefile_ext[0],suffix=remotefile_ext[1]).name
                bomFTP.get(remotefile,localfile)
            else:
                return current_timeline

        if remotefile_ext[1][len(remotefile_ext[1]) - 3:] == ".gz":
            subprocess.check_output(["gunzip","-f",localfile])
            localfile = os.path.splitext(localfile)[0]

        info = json.loads(subprocess.check_output(["gdalinfo","-json",localfile]))
        layers = []
        layertime = None
        layerId = None
        for layer in info["bands"]:
            layertime = start_date + timedelta(seconds=int(layer["metadata"][""]["NETCDF_DIM_time"]))
            layerId = (target + "{0:0>3}").format(layer["band"] - 1)

            layers.append([layertime.strftime("%a %b %d %Y %H:%M:%S AWST"),layerId,None])

        return {"refreshtime":datetime.now().strftime("%a %b %d %Y %H:%M:%S"),"layers":layers,"mdtm":mdtm,"updatetime":(start_date + timedelta(seconds=int(info["metadata"][""]["NC_GLOBAL#creationTime"]))).strftime("%a %b %d %Y %H:%M:%S AWST")}

    finally:
        if localfile:
            os.remove(localfile)


start_date = datetime(1970, 1, 1, 0, 0,tzinfo=pytz.timezone("UTC")).astimezone(pytz.timezone("Australia/Perth"))
@bottle.route("/bom/<target>")
def bom(target):
    last_updatetime = bottle.request.query.get("updatetime")
    current_timeline = None
    try:
        current_timeline = json.loads(uwsgi.cache_get(target))
    except:
        current_timeline = None

    bottle.response.set_header("Content-Type", "application/json")
    bottle.response.status = 200
    if current_timeline and datetime.now() - datetime.strptime(current_timeline["refreshtime"],"%a %b %d %Y %H:%M:%S") < timedelta(minutes=5):
        #data is refreshed within 5 minutes, use the result directly
        if current_timeline["updatetime"] == last_updatetime:
            #return 304 cause "No element found" error, so return a customized code to represent the same meaning as 304
            bottle.response.status = 290
            return "{}"
        else:
            return {"layers":current_timeline["layers"],"updatetime":current_timeline["updatetime"]}


    timeline = getTimelineFromLayer(target,current_timeline)
    timeline = timeline or getTimelineFromFtp(target,current_timeline)

    if not timeline:
        raise "Plase specify basetimelayer or remotefile to get timeline."

    if not current_timeline or id(timeline) != id(current_timeline):
        uwsgi.cache_set(target, json.dumps(timeline), 0) 

    if timeline["updatetime"] == last_updatetime:
        bottle.response.status = 290
        return "{}"
    else:
        return {"layers":timeline["layers"],"updatetime":timeline["updatetime"]}

# PDF renderer, accepts a JPG
@bottle.route("/gdal/<fmt>", method="POST")
def gdal(fmt):
    # needs gdal 1.10+
    extent = bottle.request.forms.get("extent").split(" ")
    bucket_key = bottle.request.forms.get("bucket_key")
    jpg = bottle.request.files.get("jpg")
    title = bottle.request.forms.get("title") or "Quick Print"
    sso_user = bottle.request.headers.get("X-email", "unknown")
    workdir = tempfile.mkdtemp()
    path = os.path.join(workdir, jpg.filename)
    output_filepath = path + "." + fmt
    jpg.save(workdir)
    legends_path = None
    
    extra = []
    if fmt == "tif":
        of = "GTiff"
        ct = "image/tiff"
        extra = ["-co", "COMPRESS=JPEG", "-co", "PHOTOMETRIC=YCBCR", "-co", "JPEG_QUALITY=95"]
    elif fmt == "pdf":
        of = "PDF"
        ct = "application/pdf"
        legends = bottle.request.files.get("legends")
        if legends:
            legends_path = os.path.join(workdir, legends.filename)
            legends.save(workdir)
            
    else:
        raise Exception("File format({}) Not Support".format(fmt))

    subprocess.check_call([
        "gdal_translate", "-of", of, "-a_ullr", extent[0], extent[3], extent[2], extent[1],
        "-a_srs", "EPSG:4326", "-co", "DPI={}".format(bottle.request.forms.get("dpi", 150)),
        "-co", "TITLE={}".format(title),
        "-co", "AUTHOR={}".format("Department of Parks and Wildlife"),
        "-co", "PRODUCER={}".format(gdalinfo),
        "-co", "SUBJECT={}".format(bottle.request.headers.get('Referer', "gokart")),
        "-co", "CREATION_DATE={}".format(datetime.strftime(datetime.utcnow(), "%Y%m%d%H%M%SZ'00'"))] + extra + [
        path, output_filepath
    ])
    output_filename = jpg.filename.replace("jpg", fmt)
    #merge map pdf and legend pdf
    if fmt == "pdf" and legends_path:
        #dump meta data
        metadata_file = output_filepath + ".txt"
        subprocess.check_call(["pdftk",output_filepath,"dump_data_utf8","output",metadata_file])
        #merge two pdfs
        merged_filepath = ".merged".join(os.path.splitext(output_filepath))
        subprocess.check_call(["pdftk",output_filepath,legends_path,"output",merged_filepath])
        #update meta data
        updated_filepath = ".updated".join(os.path.splitext(output_filepath))
        subprocess.check_call(["pdftk",merged_filepath,"update_info_utf8",metadata_file,"output",updated_filepath])
        output_filepath = updated_filepath

    meta = {
        'SSOUser': sso_user
    }

    #upload to s3
    if bucket_key:
        #only upload to s3 if bucket_key is not empty
        s3.upload_map(bucket_key, output_filepath, output_filename, ct, meta)
    output = open(output_filepath)
    shutil.rmtree(workdir)
    bottle.response.set_header("Content-Type", ct)
    bottle.response.set_header("Content-Disposition", "attachment;filename='{}'".format(output_filename))
    return output

feature_count_re = re.compile("^Feature Count:\s+(?P<count>\d+)",re.MULTILINE)
def featureCount(datasource,layer,feature_type):
    cmd = ["ogrinfo", "-al","-so","-ro"]
    if feature_type:
        if feature_type == "EMPTY":
            cmd.extend(["-where", "OGR_GEOMETRY IS NULL"])
        else:
            cmd.extend(["-where", "OGR_GEOMETRY='{}'".format(feature_type)])

    cmd.append(datasource)

    if layer:
        cmd.append(layer)

    info = subprocess.check_output(cmd)
    m = feature_count_re.search(info)
    return (m and int(m.group('count'))) or 0
    
layer_info_re = re.compile('[\r\n]+\s*Layer name:\s+(?P<name>[^\r\n]+)([\r\n]+\s*Geometry:\s+(?P<geometry>[^\r\n]+))?([\r\n]+Feature Count:\s+(?P<count>\d+))?[\r\n]+')
def layerinfo(datasource):
    cmd = ["ogrinfo", "-al","-so","-ro",datasource]

    info = subprocess.check_output(cmd)

    return [ (m.group('name'),m.group('geometry').replace(" ","").upper() if m.group('geometry') else None,int(m.group('count')) if m.group('count') else None) for m in layer_info_re.finditer(info)]

# Vector translation using ogr
SUPPORTED_GEOMETRY_TYPES = ["POINT","LINESTRING","POLYGON","MULTIPOINT","MULTILINESTRING","MULTIPOLYGON"] 
@bottle.route("/ogrinfo", method="POST")
def ogrinfo():
    # needs gdal 1.10+
    datasource = bottle.request.files.get("datasource")
    workdir = tempfile.mkdtemp()
    try:
        datasource.save(workdir)
        datasourcefile = os.path.join(workdir, datasource.filename)

        layers = layerinfo(datasourcefile)

        layers = [{"layer":l[0],"geometry":l[1],"featureCount":l[2]} for l in layers if l[1] in SUPPORTED_GEOMETRY_TYPES or l[1].find("UNKNOWN") >= 0]
        bottle.response.set_header("Content-Type", "application/json")
        return {"layers":layers}

    finally:
        try:
            shutil.rmtree(workdir)
        except:
            pass

@bottle.route("/ogr/<fmt>", method="POST")
def ogr(fmt):
    # needs gdal 1.10+
    datasource = bottle.request.files.get("datasource")
    layer = bottle.request.forms.get("layer")
    configure = bottle.request.forms.get("configure")
    if configure:
        configure = json.loads(configure)
    else:
        configure = {}

    workdir = tempfile.mkdtemp()
    try:
        outputdir = os.path.join(workdir,"output")
        os.mkdir(outputdir)
        #if datasource.filename contains '.', only use the left part of the first '.' as the layername
        sourcefmt = "" if (datasource.filename.rfind('.') < 0) else datasource.filename[datasource.filename.rfind('.') + 1:]
        defaultlayername =  datasource.filename if (datasource.filename.find('.') < 0) else datasource.filename[:datasource.filename.find('.')]
        datasource.save(workdir)
        datasourcefile = os.path.join(workdir, datasource.filename)
        extra = []
        dst_datasource_ext = ""

        multilayer = False
        multitype = False
        dst_datasource_pattern = None

        if fmt == "shp" :
            f = "ESRI Shapefile"
            ct = "application/zip"
            multilayer = False
            multitype = False
            dst_datasource_pattern = os.path.join(outputdir, datasource.filename if (datasource.filename.rfind('.') < 0) else datasource.filename[:datasource.filename.rfind('.')])
        elif fmt == 'sqlite':
            f = "SQLite"
            ct = "application/x-sqlite3"
            dst_datasource_ext = ".sqlite"
            multilayer = True
            multitype = False
        elif fmt == 'gpkg':
            f = "GPKG"
            ct = "application/x-sqlite3"
            dst_datasource_ext = ".gpkg"
            multilayer = True
            multitype = False
        elif fmt == 'csv':
            f = "CSV"
            ct = "text/csv"
            dst_datasource_ext = ".csv"
            multilayer = False
            multitype = True
        elif fmt in ('geojson','json'):
            f = "GeoJSON"
            ct = "application/vnd.geo+json"
            dst_datasource_ext = ".geojson"
            multilayer = False
            multitype = True
        elif fmt == 'gpx' and False:
            f = "GPX"
            ct = "application/gpx+xml"
            dst_datasource_ext = ".gpx"
            multilayer = True
            multitype = False
        else:
            bottle.response.status = 400
            return "Not supported format({})".format(fmt)

        layers = layerinfo(datasourcefile)

        if layer:
            layers = [l for l in layers if l[0] == layer]
            if len(layers) == 0:
                raise Exception("The layer({}) is not found.".found(layer))
        unsupported_layers = ["{}({})".format(l[0],l[1]) for l in layers if l[1] not in SUPPORTED_GEOMETRY_TYPES and l[1].find("UNKNOWN") < 0]
        if unsupported_layers:
            raise Exception("The geometry type of the layers({}) are not supported.".format(unsupported_layers))

        def get_dst_datasource(l,t=None):
            pattern = None
            if not dst_datasource_pattern:
                pattern = os.path.join(outputdir, datasource.filename if (datasource.filename.rfind('.') < 0) else datasource.filename[:datasource.filename.rfind('.')])
                if len(layers) > 1 and not multilayer:
                    pattern = pattern + "_{layer}"
                if t and not multilayer:
                    pattern = pattern + "_{geometry_type}"
                pattern = pattern + "{ext}"
            else:
                pattern = dst_datasource_pattern
            return pattern.format(layer=l,geometry_type=t,ext=dst_datasource_ext)

        geometry_types = None
        mode = "-overwrite"
        empty_geometry = None
        for layer in layers:
            layername =  defaultlayername if sourcefmt in ("geojson","json") else layer[0]

            empty_geometry = None
            if not multitype and layer[1] not in SUPPORTED_GEOMETRY_TYPES: 
                geometry_types = [t for t in SUPPORTED_GEOMETRY_TYPES if featureCount(datasourcefile,layer[0],t)]
                if len(geometry_types) > 1:
                    if featureCount(datasourcefile,layer[0],"EMPTY"):
                        if "EMPTY_GEOMETRY" not in configure:
                            geometry_types.append("EMPTY")
                        else:
                            empty_geometry = configure["EMPTY_GEOMETRY"]
                    
                    for t in geometry_types:
                        dst_datasource = get_dst_datasource(layer[0],t)
                        if t == "EMPTY" :
                            subprocess.check_call([
                                "ogr2ogr", mode,"-preserve_fid", "-where", "OGR_GEOMETRY IS NULL",
                                "-a_srs", "EPSG:4326", "-nln", layername + "_{}".format(configure[t] if (t in configure) else t.lower()), "-f", f, dst_datasource, datasourcefile,layer[0]
                            ])
                        elif empty_geometry == t:
                            subprocess.check_call([
                                "ogr2ogr", mode,"-preserve_fid", "-where", "OGR_GEOMETRY='{}' OR OGR_GEOMETRY IS NULL".format(t),
                                "-a_srs", "EPSG:4326", "-nln", layername + "_{}".format(configure[t] if (t in configure) else t.lower()),"-nlt",t, "-f", f, dst_datasource, datasourcefile,layer[0]
                            ])
                        else:
                            subprocess.check_call([
                                "ogr2ogr", mode,"-preserve_fid", "-where", "OGR_GEOMETRY='{}'".format(t),
                                "-a_srs", "EPSG:4326", "-nln", layername + "_{}".format(configure[t] if (t in configure) else t.lower()),"-nlt",t, "-f", f, dst_datasource, datasourcefile,layer[0]
                            ])
                        mode = "-update" if multilayer else "-overwrite"
                    continue

            dst_datasource = get_dst_datasource(layer[0])
            subprocess.check_call([
                "ogr2ogr","-overwrite","-preserve_fid" ,"-a_srs","EPSG:4326","-nln",layername, "-f", f,dst_datasource, datasourcefile,layer[0]]) 
            mode = "-update" if multilayer else "-overwrite"
    
        if len(os.listdir(outputdir)) > 1 or (len(os.listdir(outputdir)) == 1 and os.path.isdir(os.path.join(outputdir,os.listdir(outputdir)[0]))):
            ct = "application/zip"
            zipfile = dst_datasourcebase = os.path.join(workdir, datasource.filename if (datasource.filename.rfind('.') < 0) else datasource.filename[:datasource.filename.rfind('.')])
            zipfile = zipfile + "." + fmt
            shutil.make_archive(zipfile, 'zip', outputdir)
            dst_datasource = zipfile + ".zip"
    
        output = open(dst_datasource)
        bottle.response.set_header("Content-Type", ct)
        bottle.response.set_header("Content-Disposition", "attachment;filename='{}'".format(os.path.basename(dst_datasource)))
        return output
    finally:
        try:
            shutil.rmtree(workdir)
        except:
            pass



# saveas
@bottle.route("/saveas", method="POST")
def saveas():
    user = bottle.request.get_header("Remote-User","anonymous")

    f = bottle.request.files.get("file")
    filename = f.raw_filename
    f.raw_filename = "_{}_{}".format(user,bottle.request.remote_addr).join(os.path.splitext(f.raw_filename))
    workdir = os.path.join(BASE_PATH,"tmp")
    if not os.path.exists(workdir):
        #create dir if required.
        os.mkdir(workdir)

    
    path = os.path.join(workdir, f.filename)
    if os.path.exists(path):
        try:
            os.remove(path)
        except:
            pass
    f.save(workdir,overwrite=True)
    bottle.response.set_header("Content-Type", "text/plain")
    return bottle.request.url.replace("/saveas","/fetch") + "/" + f.filename + "?filename=" + filename;


application = bottle.default_app()
