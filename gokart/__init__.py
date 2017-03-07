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
HTTPS_VERIFY = True if HTTPS_VERIFY.lower() in ["true","on","yes"] else (False if HTTPS_VERIFY.lower() in ["false","off","no"] else HTTPS_VERIFY )


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


basetime_url = os.environ.get("BOM_BASETIME_URL")
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
def featureCount(jsonfile,featureType):
    info = subprocess.check_output(["ogrinfo", "-al","-so","-ro", "-where", "OGR_GEOMETRY='{}'".format(featureType), jsonfile])
    m = feature_count_re.search(info)
    return (m and int(m.group('count'))) or 0
    


# Vector translation using ogr
@bottle.route("/ogr/<fmt>", method="POST")
def ogr(fmt):
    # needs gdal 1.10+
    json = bottle.request.files.get("json")
    workdir = tempfile.mkdtemp()
    #if json.filename contains '.', only use the left part of the first '.' as the layername
    layername =  json.filename if (json.filename.find('.') < 0) else json.filename[:json.filename.find('.')]
    json.save(workdir)
    jsonfile = os.path.join(workdir, json.filename)
    extra = []
    split = False
    if fmt == "shp" and False:
        #Disable now
        f = "ESRI Shapefile"
        ct = "application/zip"
    elif fmt == 'sqlite':
        f = "SQLite"
        ct = "application/x-sqlite3"
        dst_datasource = os.path.splitext(jsonfile)[0] + ".sqlite"
    elif fmt == 'gpkg':
        f = "GPKG"
        ct = "application/x-sqlite3"
        dst_datasource = os.path.splitext(jsonfile)[0] + ".gpkg"
        split = True
    elif fmt == 'csv':
        f = "CSV"
        ct = "text/csv"
        dst_datasource = os.path.splitext(jsonfile)[0] + ".csv"
    else:
        bottle.response.status = 400
        return "Not supported format({})".format(fmt)

    if split:
        mode = "-overwrite"
        for t in ["POINT","LINESTRING","POLYGON","MULTIPOINT","MULTILINESTRING","MULTIPOLYGON"]:
            if featureCount(jsonfile,t):
                subprocess.check_call([
                    "ogr2ogr", mode, "-where", "OGR_GEOMETRY='{}'".format(t),
                    "-a_srs", "EPSG:4326", "-nln", layername+"_{}s".format(t.lower()), "-f", f, dst_datasource, jsonfile
                ])
                mode = "-update"
    else:
        subprocess.check_call([
            "ogr2ogr","-overwrite" ,"-a_srs","EPSG:4326","-nln",layername, "-f", f,dst_datasource, jsonfile]) 

    if fmt == "shp":
        shutil.make_archive(path.replace('geojson', 'zip'), 'zip', workdir, workdir)
        dst_datasource = path + ".zip"

    output = open(dst_datasource)
    shutil.rmtree(workdir)
    bottle.response.set_header("Content-Type", ct)
    bottle.response.set_header("Content-Disposition", "attachment;filename='{}'".format(os.path.basename(dst_datasource)))
    return output


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
