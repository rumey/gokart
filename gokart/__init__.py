import bottle
import dotenv
import sys
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
import pyproj
import shapely
import traceback
import shapely.ops as ops
import threading
from shapely.geometry import shape
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.collection import GeometryCollection
from functools import partial
from jinja2 import Template
from logging import Logger
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

bottle.TEMPLATE_PATH.append('./gokart')
bottle.debug(True)

BASE_PATH = os.path.dirname(__file__)

BASE_DIST_PATH = os.path.join(os.path.dirname(BASE_PATH),"dist")


ENV_TYPE = (os.environ.get("ENV_TYPE") or "prod").lower()

gdalinfo = subprocess.check_output(["gdalinfo", "--version"])

bottle.BaseRequest.MEMFILE_MAX = 20 * 1024 * 1024

@bottle.route('/client')
def server_static():
    return bottle.static_file('client.html', root=BASE_PATH)

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
sso_cookie_name = os.environ.get("SSO_COOKIE_NAME") or "dbca_wa_gov_au_sessionid"

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


basetime_url = os.environ.get("BOM_BASETIME_URL") or "https://kmi.dbca.wa.gov.au/geoserver/bom/wms?service=WMS&version=1.1.0&request=GetMap&styles=&bbox=70.0,-55.0,195.0,20.0&width=768&height=460&srs=EPSG:4283&format=image%2Fgif&layers={}"
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

    if not timeline:
        raise "Missing some of http parameters 'basetimelayer', 'timelinesize', 'layertimespan'."

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

def detectEpsg(filename):
    gdal_cmd = ['gdalsrsinfo', '-e', filename]
    gdal = subprocess.Popen(gdal_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    gdal_output = gdal.communicate()

    result = None
    for line in gdal_output[0].split('\n'):
        if line.startswith('EPSG') and line != 'EPSG:-1':
            result = line
            break

    return result


#initialize vrt template
with open(os.path.join(BASE_PATH,"unionlayers.vrt")) as f:
    UNIONLAYERS_TEMPLATE = Template(f.read())

# Vector translation using ogr
SUPPORTED_GEOMETRY_TYPES = ["POINT","LINESTRING","POLYGON","MULTIPOINT","MULTILINESTRING","MULTIPOLYGON"] 

#initialize supported spatial format
SPATIAL_FORMAT_LIST = [
    {
        "name"      : "shp",
        "format"    : "ESRI Shapefile",
        "multilayer": False,
        "multitype" : False,
        "fileext"   : ".shp"
    },
    {
        "name"      : "sqlite",
        "format"    : "SQLite",
        "mime"      : "application/x-sqlite3",
        "multilayer": True,
        "multitype" : False,
        "fileext"   : ".sqlite"
    },
    {
        "name"      : "gpkg",
        "format"    : "GPKG",
        "mime"      : "application/x-sqlite3",
        "multilayer": True,
        "multitype" : False,
        "fileext"   : ".gpkg"
    },
    {
        "name"      : "csv",
        "format"    : "CSV",
        "mime"      : "text/csv",
        "multilayer": False,
        "multitype" : True,
        "fileext"   : ".csv"
    },
    {
        "name"      : "geojson",
        "format"    : "GeoJSON",
        "mime"      : "application/vnd.geo+json",
        "multilayer": False,
        "multitype" : True,
        "fileext"   : ".geojson"
    },
    {
        "name"      : "json",
        "format"    : "GeoJSON",
        "mime"      : "application/vnd.geo+json",
        "multilayer": False,
        "multitype" : True,
        "fileext"   : ".json"
    },
    {
        "name"      : "gpx",
        "format"    : "GPX",
        "mime"      : "application/gpx+xml",
        "multilayer": True,
        "multitype" : False,
        "fileext"   : ".gpx"
    }
]
SPATIAL_FORMATS = {}
for f in SPATIAL_FORMAT_LIST:
    SPATIAL_FORMATS[f["name"]] = f
    SPATIAL_FORMATS[f["fileext"]] = f

#initialize supported compressed file format
COMPRESS_FILE_SETTINGS = {
    ".7z":lambda f,output:["7za","x",f,"-o{}".format(output)],
    ".zip":lambda f,output:["unzip",f,"-d",output],
    ".tar":lambda f,output:["tar","-x","-f",f,"-C",output],
    ".tar.gz":lambda f,output:["tar","-x","-z","-f",f,"-C",output],
    ".tgz":lambda f,output:["tar","-x","-z","-f",f,"-C",output],
    ".tar.xz":lambda f,output:["tar","-x","-J","-f",f,"-C",output],
    ".tar.bz2":lambda f,output:["tar","-x","-j","-f",f,"-C",output],
    ".tar.bz":lambda f,output:["tar","-x","-j","-f",f,"-C",output],
}
def getBaseDatafileName(f,includeDir=False):
    if not includeDir:
        f = os.path.split(f)[1]
    for fileext in COMPRESS_FILE_SETTINGS.iterkeys():
        if f.lower().endswith(fileext):
            return f[0:len(f) - len(fileext)]

    for fmt in SPATIAL_FORMAT_LIST:
        if f.lower().endswith(fmt["fileext"]):
            return f[0:len(f) - len(fmt["fileext"])]

    return os.path.splitext(f)[0]

#return list of spatial data files. each data file has absolute path and relative path
def getDatasourceFiles(workdir,datasourcefile):
    # needs gdal 1.10+
    datasourcefiles = []
    #import ipdb;ipdb.set_trace()
    #uncompress files, support recursive uncompress
    files = [datasourcefile]
    while len(files) > 0:
        f = files.pop()
        if os.path.isfile(f):
            for (fileext,cmd) in COMPRESS_FILE_SETTINGS.iteritems():
                if f.lower().endswith(fileext):
                    extractDir = f[0:len(f) - len(fileext)]
                    os.mkdir(extractDir)
                    subprocess.check_call(cmd(f,extractDir))
                    if f != datasourcefile:
                        os.remove(f)
                    else:
                        datasourcefile = extractDir
                    files.append(extractDir)
                    break
        else:
            files.extend([os.path.join(f,path) for path in os.listdir(f)])

    if os.path.isdir(datasourcefile):
        for f in os.walk(datasourcefile):
            for fileName in f[2]:
                if (fileName[0] == "."):
                    #ignore the file starts with "."
                    continue
                else:
                    if os.path.splitext(fileName)[1] in SPATIAL_FORMATS:
                        datasourcefiles.append((os.path.join(f[0],fileName),os.path.relpath(os.path.join(f[0],fileName),datasourcefile)))

    elif os.path.splitext(datasourcefile)[1] in SPATIAL_FORMATS:
        datasourcefiles = [(datasourcefile,os.path.relpath(datasourcefile,workdir))]

    return datasourcefiles

layer_re = re.compile("[\r\n]+Layer name:")
layer_info_re = re.compile("[\r\n]+(?P<key>[a-zA-Z0-9_\-][a-zA-Z0-9_\- ]*)[ \t]*:(?P<value>[^\r\n]*([\r\n]+(([ \t]+[^\r\n]*)|(GEOGCS[^\r\n]*)))*)")
extent_re = re.compile("\s*\(\s*(?P<minx>-?[0-9\.]+)\s*\,\s*(?P<miny>-?[0-9\.]+)\s*\)\s*\-\s*\(\s*(?P<maxx>-?[0-9\.]+)\s*\,\s*(?P<maxy>-?[0-9\.]+)\s*\)\s*")
def getLayers(datasource,layer=None,srs=None,defaultSrs=None,featureType=None):
    # needs gdal 1.10+
    infoIter = None

    srs = srs or detectEpsg(datasource) or defaultSrs

    #import ipdb;ipdb.set_trace()
    cmd = ["ogrinfo", "-al","-so","-ro"]
    if featureType:
        if featureType == "EMPTY":
            cmd.extend(["-where", "OGR_GEOMETRY IS NULL"])
        else:
            cmd.extend(["-where", "OGR_GEOMETRY='{}'".format(featureType)])

    cmd.append(datasource)

    if layer:
        cmd.append(layer)

    def getLayerInfo(layerInfo):
        info = {"fields":[],"srs":srs}
        for m in layer_info_re.finditer(layerInfo):
            key = m.group("key").lower()
            value = m.group("value").strip()
            if key in ("info","metadata","layer srs wkt","ogrinfo"): 
                continue
            if key == "layer name":
                info["layer"] = value
            elif key == "geometry":
                info["geometry"] = value.replace(" ","").upper()
            elif key == "feature count":
                try:
                    info["features"] = int(value)
                except:
                    info["features"] = 0
            elif key == "extent":
                try:
                    info["extent"] = [float(v) for v in extent_re.find(value).groups()]
                except:
                    pass
            else:
                info["fields"].append((key,value))
        return info
    info = subprocess.check_output(cmd)
    layers = []
    previousMatch = None
    layerIter = layer_re.finditer(info)
    for m in layerIter:
        if previousMatch is None:
            previousMatch = m
        else:
            layers.append(getLayerInfo(info[previousMatch.start():m.start()]))
            previousMatch = m
    if previousMatch:
        layers.append(getLayerInfo(info[previousMatch.start():]))

    return layers

def getFeatureCount(datasource,layer=None,featureType=None):
    layers = getLayers(datasource,layer,None,None,featureType)
    if len(layers) == 0:
        raise Exception("Layer({}) is not found in datasource({})".format(layer or "",datasource))
    elif len(layers) > 1:
        raise Exception("Multiple layers are found in datasource({})".format(datasource))
    else:
        return layers[0].get("features") or 0

def getOutputDatasource(workdir,fmt,layer,geometryType=None):
    if geometryType:
        geometryType = layer.get("type_mapping",{}).get(geometryType,geometryType)
    if fmt["multilayer"]:
        if geometryType:
            path = os.path.join(workdir,"{}-{}{}".format(layer["sourcename"],geometryType,fmt["fileext"]))
        else:
            path = os.path.join(workdir,"{}{}".format(layer["sourcename"],fmt["fileext"]))
    elif layer.get("sourcename",None):
        if geometryType:
            path = os.path.join(workdir,layer["sourcename"],"{}-{}{}".format(layer["layer"],geometryType,fmt["fileext"]))
        else:
            path = os.path.join(workdir,layer["sourcename"],"{}{}".format(layer["layer"],fmt["fileext"]))
    else:
        if geometryType:
            path = os.path.join(workdir,"{}-{}{}".format(layer["layer"],geometryType,fmt["fileext"]))
        else:
            path = os.path.join(workdir,"{}{}".format(layer["layer"],fmt["fileext"]))
    
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    return path

geojson_re = re.compile("^\s*\{\s*[\"\']type[\"\']\s*:\s*[\"\']FeatureCollection[\"\']\s*\,")
service_exception_re = re.compile("^.*(\<ServiceExceptionReport)",re.DOTALL)
def loadDatasource(session_cookie,workdir,loadedDatasources,options):
    """
    options:{
        name: datasource name, optional; if missing, derived from url or parameter
        type: "WFS" or "UPLOAD" or "FORM"  
            WFS: download the data from wfs server; 
            UPLOAD: download the data from http request
            FORM: get the data form http form
        url: wfs url if sourcetype is "WFS",
        parameter: http request parameter if sourcetype is"UPLOAD" or "FORM"
        srs: srs optional
        datasource: used if sourcetype is "UPLOAD" and uploaded file contains multiple datasources
        layer: layer name,required if datasource include multiple layers
        where: filter the features 
    }
    After loading, the following data are inserted into options
        name: add if missing
        file: the loaded file
        datasources: datasource list included in the datasource
        datasource: the datasource selected by user
        srs: if can be determined
        format: the source data file format, optional, can be deduced from datasource
        layer: layer name,required if datasource include multiple layers
        meta: the layer information: geometry type, feature count, etc, optional. can be deduced from datasource and name
    """
    #import ipdb;ipdb.set_trace()
    sourcetype = options.get("type","WFS")
    if sourcetype == "WFS":
        #load layer from wfs server
        if options["url"] not in loadedDatasources:
            datasource = os.path.join(workdir,"{}.gpkg".format(options["sourcename"]))
            if not os.path.exists(os.path.dirname(datasource)):
                os.makedirs(os.path.dirname(datasource))
            url = "{}&outputFormat=gpkg&srsName=EPSG:4326".format(options["url"])
            r = requests.get(url,
                verify=False,
                cookies=session_cookie
            )
            with open(datasource,"wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    f.write(chunk)
            failed = False
            with open(datasource,"r") as f:
                if service_exception_re.search(f.read(1024)):
                    failed = True
            if failed:
                with open(datasource,"r") as f:
                    raise Exception("{}\r\n{}".format(url,f.read()))

            loadedDatasources[options["url"]] = (datasource,getDatasourceFiles(os.path.dirname(datasource),datasource))
        options["srs"] = "EPSG:4326"
        options["file"] = loadedDatasources[options["url"]][0]
        options["datasources"] = loadedDatasources[options["url"]][1]

    elif sourcetype in ["UPLOAD","FORM"]:
        if options["parameter"] not in loadedDatasources:
            if sourcetype == "UPLOAD":
                #load layer from http request
                datasource = bottle.request.files.get(options["parameter"])
                datasource.save(workdir,overwrite=True)
                datasource =  os.path.join(workdir,datasource.filename)
                loadedDatasources[options["parameter"]] = (datasource,getDatasourceFiles(os.path.dirname(datasource),datasource))
    
            elif sourcetype == "FORM":
                #load layer from http request
                datasource = os.path.join(workdir,"{}.geojson".format(options.get("parameter")))
                if not os.path.exists(os.path.dirname(datasource)):
                    os.makedirs(os.path.dirname(datasource))
                with open(datasource,"wb") as f:
                    f.write(bottle.request.forms.get(options["parameter"]))
                loadedDatasources[options["parameter"]] = (datasource,getDatasourceFiles(os.path.dirname(datasource),datasource))
    
        options["file"] = loadedDatasources[options["parameter"]][0]
        options["datasources"] = loadedDatasources[options["parameter"]][1]

    if len(options["datasources"]) == 0:
        raise Exception("No spatial data are found in datasource  ({}).".format(options["sourcename"]))

    #get the datasource selected by user
    if options.get("datasource"):
        if options["datasource"] == "*":
            #include all datasource and layers; used when loading a datasource
            return
        else:
            #have selected datasource , find it
            datasource = None
            for d in options["datasources"]:
                if d[1] == options["datasource"]:
                    datasource = d
                    break

            if datasource:
                options["datasource"] = datasource
            else:
                raise Exception("Datasource({}) does not exist.".format(options["datasource"]))

    elif len(options["datasources"]) > 1:
        raise Exception("Multiple datasource({}) are found, please choose one".format(str([d[1] for d in options["datasources"]])))
    else:
        #only have one datasource,choose it
        options["datasource"] = options["datasources"][0]

    #detect srs
    if not options.get("srs"):
        options["srs"] = detectEpsg(options["datasource"][0])
    if not options.get("srs") and options.get("default_srs"):
        options["srs"] = options["default_srs"]

    if "format" not in options:
        options["format"] = SPATIAL_FORMATS.get(os.path.splitext(options["datasource"][1])[1].lower())
        if not options["format"]:
            raise Exception("Can't detect the format of the datasource ({}).".format(options["datasource"][1]))

    #filter the data if required
    if "where"  in options:
        filterdir = os.path.join(workdir,"filter")
        if not os.path.exists(filterdir):
            os.mkdir(filterdir)
    
        datasource = os.path.join(filterdir,"{}{}".format(options["sourcename"],options["format"]["fileext"]))
        if not os.path.exists(os.path.dirname(datasource)):
            os.makedirs(os.path.dirname(datasource))

        cmd = ["ogr2ogr","-preserve_fid" ,"-skipfailures",
            #"-where","\"{}\"".format(options["where"]),
            "-where",options["where"],
            "-f", options["format"]["format"],
            datasource, 
            options["datasource"][0],
        ]

        if "layer" in options:
            cmd.append(options["layer"])

        #print " ".join(cmd)
        subprocess.check_call(cmd)
        options["datasource"] = getDatasourceFiles(filterdir,datasource)[0]

        options["format"] = SPATIAL_FORMATS.get(os.path.splitext(options["datasource"][1])[1].lower())
        if not options["format"]:
            raise Exception("Can't detect the format of the datasource ({}).".format(options["datasource"][1]))

    #get layer meta data
    if "format" not in options:
        options["format"] = SPATIAL_FORMATS.get(os.path.splitext(options["datasource"][1])[1].lower())
        if not options["format"]:
            raise Exception("Can't detect the format of the datasource ({}).".format(options["datasource"][1]))

    if "meta" not in options:
        if options["format"]["multilayer"]:
            metas = getLayers(options["datasource"][0],options.get("layer"),options.get("srs"),options.get("default_srs"))
        else:
            metas = getLayers(options["datasource"][0],None,options.get("srs"),options.get("default_srs"))
        if len(metas) == 0:
            options["meta"] = None
            options["layer"] = None
        elif len(metas) == 1:
            options["meta"] = metas[0]
            options["layer"] = options["meta"]["layer"]
        else:
            raise Exception("Multiple layers are found in datasource({})".format(options["sourcename"]))
    
@bottle.route("/ogrinfo", method="POST")
def ogrinfo():
    # needs gdal 1.10+
    #import ipdb;ipdb.set_trace()
    datasource = bottle.request.files.get("datasource")
    workdir = tempfile.mkdtemp()
    try:
        datasource.save(workdir)
        datasourcefile = os.path.join(workdir, datasource.filename)

        datasources = []
        layerSize = 0
        datasourceSize = 0
        for filePath,relativeFilePath in getDatasourceFiles(workdir,datasourcefile):
            layers = getLayers(filePath)
            layers = [l for l in layers if l["geometry"] in SUPPORTED_GEOMETRY_TYPES or l["geometry"].upper().find("UNKNOWN") >= 0]
            if layers:
                datasources.append({"datasource":relativeFilePath,"layers": layers})
                layerSize += len(datasources[len(datasources) - 1]["layers"])
                datasourceSize += 1


        if layerSize == 0:
            raise Exception("No spatial data is found.")

        bottle.response.set_header("Content-Type", "application/json")
        return {"layerCount":layerSize,"datasourceCount":datasourceSize,"datasources":datasources}
    except Exception as ex:
        bottle.response.status = 500
        bottle.response.set_header("Content-Type", "text/plain")
        return  str(ex)

    finally:
        try:
            shutil.rmtree(workdir)
        except:
            pass

#get type name from url
typename_re = re.compile("typenames?=\s*(?P<name>[a-zA-Z0-9_\-\:\%]+)\s*",re.DOTALL)
def typename(url):
    m = typename_re.search(url.lower())
    return m.group('name').replace("%3a",":") if m else None

def getMd5(data):
    m = hashlib.md5()
    m.update(data)
    data = base64.urlsafe_b64encode(m.digest())
    if data[-3:] == "===":
        return data[0:-3]
    elif data[-2:] == "==":
        return data[0:-2]
    elif data[-1:] == "=":
        return data[0:-1]
    else:
        return data


@bottle.route("/download/<fmt>", method="POST")
def downloaod(fmt):
    """
    form data:
    layers: a layer or a list of layer
        {
            sourcename: output datasource name; if missing, derived from layer name or datasource
            layer: output layer name,if missing, using the datasource layer name
            default_geometry_type: The geometry type of the empty geometry 
            type_mapping: the mapping between geometry type and business name used in the datasource or layer name
            srs: srs optional, default is first's source layer's srs
            ignore_if_empty: empty layer will not be returned if true; default is false
            sourcelayers: a source layer or a list of source layers
            {
                type: "WFS" or "UPLOAD" or "FORM". deduced from other properties
                    WFS: download the data from wfs server; 
                    UPLOAD: download the data from http request
                    FORM: get the data form http form
                url: wfs url if sourcetype is "WFS",
                parameter: http request parameter if sourcetype is"UPLOAD" or "FORM"
                srs: srs optional
                defautl_srs:default srs; optional
                datasource: used if sourcetype is "UPLOAD" and uploaded file contains multiple datasources
                layer: layer name,required if datasource include multiple layers
                where: filter the features 
            },
        },
    datasources:a datasource or a list of datasource
        {
            type: "WFS" or "UPLOAD" or "FORM", if missing, try to deduced from other data source properties.
                  WFS: download the data from wfs server; 
                  UPLOAD: download the data from http request
                  FORM: get the data form http form
            url: wfs url if sourcetype is "WFS",
            parameter: http request parameter if sourcetype is"UPLOAD" or "FORM"
            srs: srs optional
            default_geometry_type: The geometry type of the empty geometry 
            defautl_srs:default srs; optional
            datasource: used if sourcetype is "UPLOAD" and uploaded file contains multiple datasources
            ignore_if_empty: empty layer will not be returned if true; default is false
        }
    
    filename:optional, used when multiple output datasources are downloaded
    srs: optional, output srs
    """
    # needs gdal 1.10+
    layers = bottle.request.forms.get("layers")
    output = bottle.request.forms.get("output")
    datasources = bottle.request.forms.get("datasources")
    filename = bottle.request.forms.get("filename")
    outputSrs = bottle.request.forms.get("srs")

    try:
        if layers:
            layers = json.loads(layers)

        if layers and not isinstance(layers,list):
            #convert  a layer to a list of layer
            layers = [layers]

        if datasources:
            datasources = json.loads(datasources)

        if datasources and not isinstance(datasources,list):
            #convert  a datasource to a list of datasource
            datasources = [datasources]

        if not layers and not datasources:
            raise Exception("Both layers parameter and datasources parameter are missing.")

        if layers is None:
            layers = []

        #if output format is not set, set to the default format "geojson"
        fmt = SPATIAL_FORMATS.get(fmt.lower())
        if not fmt:
            raise Exception("Unsupported spatial format({})".format(fmt))

        #If a source layer is not a union layer, changed it to a union layer which only have one sub layer
        if layers:
            for layer in layers:
                if not layer.get("sourcelayers"):
                    raise Exception("Missing 'sourcelayers' in layer ({})".format(json.dumps(layer)))
                elif not isinstance(layer["sourcelayers"],list):
                    layer["sourcelayers"] = [layer["sourcelayers"]]

        #set field strategy and ignore_if_empty for layers
        if layers:
            for layer in layers:
                if layer.get("fields") and not layer.get("fieldStrategy"):
                    layer["fieldStrategy"] = "Intersection"
                layer["ignore_if_empty"] = layer.get("ignore_if_empty") or False

        #set datasource's ignore_if_empty
        if datasources:
            for datasource in datasources:
                datasource["ignore_if_empty"] = datasource.get("ignore_if_empty") or False

    
        def setDatasourceType(ds):
            if "type" in ds:
                return
            if "url" in ds:
                ds["type"] = "WFS"
            elif "parameter" in ds:
                if bottle.request.forms.get(ds["parameter"]):
                    ds["type"] = "FORM"
                elif bottle.request.files.get(ds["parameter"]):
                    ds["type"] = "UPLOAD"
                else:
                    raise Exception("Can't locate the http request data ({})".format(ds["parameter"]))
            else:
                raise Exception("Can't deduce the type of the datasource ({})".format(json.dumps(ds)))

        def getDatasourceName(ds,unique=False):
            if "sourcename" in ds:
                name = ds["sourcename"]
                if unique and "where" in ds:
                    name = "{}-{}".format(name,getMd5(ds["where"]))
            elif ds["type"] == "WFS":
                name = typename(ds["url"])
                if not name:
                    name = getMd5(ds["url"])
                    if unique and "where" in ds:
                        name = "{}-{}".format(name,getMd5(ds["where"]))
                else:
                    name = name.replace(":","_")
                    if unique:
                        if "where" in ds:
                            name = "{}-{}-{}".format(name,getMd5(ds["url"]),getMd5(ds["where"]))
                        else:
                            name = "{}-{}".format(name,getMd5(ds["url"]))
            elif ds["type"] == "FORM":
                name = ds["parameter"]
                if unique and "where" in ds:
                    name = "{}-{}".format(name,getMd5(ds["where"]))
            elif ds["type"] == "UPLOAD":
                filename = bottle.request.files.get(ds["parameter"]).filename
                filename = os.path.split(filename)[1]
                name = None
                for fileext in COMPRESS_FILE_SETTINGS.iterkeys():
                    if filename.lower().endswith(fileext):
                        name = filename[:len(filename) - len(fileext)]
                        break
                if not name:
                    name = os.path.splitext(filename)[0]
                if unique and "where" in ds:
                    name = "{}-{}".format(name,getMd5(ds["where"]))


            return name

        #set datasource type if not set
        #import ipdb;ipdb.set_trace()
        if layers:
            for layer in layers:
                for sourcelayer in layer["sourcelayers"]:
                    setDatasourceType(sourcelayer)

        if datasources:
            for ds in datasources:
                setDatasourceType(ds)

        #set the datasource name for all source layers or source datasources, if not set.
        names = {}
        if layers:
            for layer in layers:
                for sourcelayer in layer["sourcelayers"]:
                    name = getDatasourceName(sourcelayer)
                    names[name] = names.get(name,0) + 1
                    sourcelayer["sourcename"] = name
        if datasources:
            for ds in datasources:
                name = getDatasourceName(ds)
                names[name] = names.get(name,0) + 1
                ds["sourcename"] = name

        if layers:
            for layer in layers:
                for sourcelayer in layer["sourcelayers"]:
                    if names.get(sourcelayer["sourcename"],1) > 1:
                        sourcelayer["sourcename"] = getDatasourceName(sourcelayer,True)
        if datasources:
            for ds in datasources:
                if names.get(ds["sourcename"],1) > 1:
                    ds["sourcename"] = getDatasourceName(ds,True)
        del names

        #import ipdb;ipdb.set_trace()
        #load data sources
        workdir = tempfile.mkdtemp()

        session_cookie = get_session_cookie()
        cookies={sso_cookie_name:session_cookie}

        loaddir = os.path.join(workdir,"load")
        os.mkdir(loaddir)

        loadedDatasources = {}
        if layers:
            for layer in layers:
                for sourcelayer in layer["sourcelayers"]:
                    loadDatasource(cookies,loaddir,loadedDatasources,sourcelayer)
        
        #import ipdb;ipdb.set_trace()
        #load data sources and add all layers in datasources to layers
        if datasources:
            for datasource in datasources:
                datasource["datasource"] = datasource.get("datasource") or "*"
                loadDatasource(cookies,loaddir,loadedDatasources,datasource)
                for dsfile in datasource["datasources"]:
                    if datasource.get("datasource") != "*" and datasource.get("datasource") != dsfile[0]:
                        continue
                    for metadata in getLayers(dsfile[0]):
                        sourcelayer = dict(datasource)
                        if "default_geometry_type" in sourcelayer:
                            del sourcelayer["default_geometry_type"]
                        sourcelayer["datasource"] = dsfile[1]
                        sourcelayer["meta"] = metadata
                        sourcelayer["layer"] = metadata["layer"]
                        loadDatasource(cookies,loaddir,loadedDatasources,sourcelayer)

                        layer = {
                            "sourcename":getBaseDatafileName(dsfile[1],True),
                            "sourcelayers":[sourcelayer],
                            "ignore_if_empty":datasource["ignore_if_empty"]
                        }
                        if sourcelayer["format"]["name"] in ["geojson","json"]:
                            layer["layer"] = getBaseDatafileName(sourcelayer["datasource"][1],False)
                        else:
                            layer["layer"] = metadata["layer"]

                        if "default_geometry_type" in datasource:
                            layer["default_geometry_type"] = datasource["default_geometry_type"]
                        layers.append(layer)

        del loadedDatasources

        #remove layers which do not include spatial data
        if layers:
            index1 = len(layers) - 1
            while index1 >= 0:
                index2 = len(layers[index1]["sourcelayers"]) - 1
                while index2 >= 0:
                    if not layers[index1]["sourcelayers"][index2].get("meta"):
                        #no spatial data
                        del layers[index1]["sourcelayers"][index2]
                    elif layers[index1]["ignore_if_empty"] and layers[index1]["sourcelayers"][index2]["meta"].get("features",0) == 0:
                        #no features
                        del layers[index1]["sourcelayers"][index2]
                    index2 -= 1
                if len(layers[index1]["sourcelayers"]) == 0:
                    #no spatial data
                    del layers[index1]
                index1 -= 1

        if not layers:
            raise Exception("No spatial data found.")

        #import ipdb;ipdb.set_trace()
        #determine the output layer name
        if fmt["multilayer"]:
            names = {}
            #first get the shortest name and check whether it is unique
            for layer in layers:
                if layer.get("layer"):
                    name = layer["layer"]
                else:
                    name = None
                    for srcLayer in layer["sourcelayers"]:
                        if srcLayer["meta"]["format"]["name"] not in ["geojson","json"]:
                            name = srcLayer["layer"]
                            break
                        elif not name:
                            #use the file name as the layer name if format is geojson or json
                            name = getBaseDatafileName(srcLayer["datasource"][1],False)
                
                names[name] = names.get(name,0) + 1
                layer["layer"] = name

            #append the file path to the name if shortest name is duplicate.
            for layer in layers:
                name = layer["layer"]
                if names.get(name,1) > 1:
                    sourcename = getBaseDatafileName(layer["sourcelayers"][0]["datasource"][1],True)
                    if sourcename.endswith(name):
                        sourcename = os.path.dirname(sourcename)
                    if sourcename and sourcename != "/":
                       sourcename = sourcename.replace("/","_")
                       layer["layer"] = "{}_from_{}".format(name,sourcename)

            del names
        else:
            for layer in layers:
                if not layer.get("layer"):
                    name = None
                    for srcLayer in layer["sourcelayers"]:
                        if srcLayer["meta"]["format"]["name"] not in ["geojson","json"]:
                            name = srcLayer["layer"]
                            break
                        elif not name:
                            #use the file name as the layer name if format is geojson or json
                            name = getBaseDatafileName(srcLayer["datasource"][1],False)
                    layer["layer"] = name

        #import ipdb;ipdb.set_trace()
        #determine the output datasource name
        if fmt["multilayer"]:
            for layer in layers:
                #target format support multiple layer, use the output file name or the first source layer's file name as the source name
                if filename:
                    layer["sourcename"] = filename
                else:
                    layer["sourcename"] = getBaseDatafileName(layer["sourcelayers"][0]["file"])
        else:
            names = {}
            #first get the prefered file name and check whether it is unique
            for layer in layers:
                if not layer.get("sourcename"):
                    layer["sourcename"] = getBaseDatafileName(layer["sourcelayers"][0]["datasource"][1],True)
                names[layer["sourcename"]] = names.get(layer["sourcename"],0) + 1

            #if all the sourcename are same, then no need to use separate folder, set the sourcename to None
            if len(names) <= 1:
                for layer in layers:
                    layer["sourcename"] = None


            #append the layer name to the file name if the prefered name is duplicate.
            #for layer in layers:
            #    if names[layer["sourcename"]] > 1:
            #        layer["sourcename"] = os.path.join(layer["sourcename"],layer["layer"])
            #        pass
            
            del names

        #determine the output srs
        srss = {}
        for layer in layers:
            if srss.get(layer["sourcename"]):
                layer["srs"] = srss[layer["sourcename"]]
            elif layer.get("srs"):
                srss[layer["sourcename"]] = layer["srs"]
            elif outputSrs:
                layer["srs"] = outputSrs
                srss[layer["sourcename"]] = layer["srs"]
            else:
                layer["srs"] = None
                for l in layer["sourcelayers"]:
                    if l["meta"]["srs"]:
                        layer["srs"] = l["meta"]["srs"]
                        srss[layer["sourcename"]] = layer["srs"]
                        break
        del srss

        #convert and union the layers
        outputdir = os.path.join(workdir,"output")
        os.mkdir(outputdir)

        unsupported_layers = []
        #print "{}".format(layers)
        for layer in layers:
            for sourcelayer in layer["sourcelayers"]:
                if sourcelayer["meta"]["geometry"] not in SUPPORTED_GEOMETRY_TYPES and sourcelayer["meta"]["geometry"].find("UNKNOWN") < 0:
                    unsupported_layers.append("{}({})".format(sourcelayer["layer"],sourcelayer["meta"]["geometry"]))

        if len(unsupported_layers) > 0:
            raise Exception("Unsupported geometry type ({}).".format(str(unsupported_layers)))

        outputFiles = []

        vrtdir = os.path.join(workdir,"vrt")
        os.mkdir(vrtdir)

        #import ipdb;ipdb.set_trace()
        for layer in layers:
            #populate the vrt file
            if layer.get("sourcename",None):
                vrtFile = os.path.join(vrtdir,layer["sourcename"],"{}.vrt".format(layer["layer"]))
            else:
                vrtFile = os.path.join(vrtdir,"{}.vrt".format(layer["layer"]))
            if not os.path.exists(os.path.dirname(vrtFile)):
                os.makedirs(os.path.dirname(vrtFile))
            vrt = UNIONLAYERS_TEMPLATE.render(layer)
            with open(vrtFile,"wb") as f:
                f.write(vrt)
            vrt = None
            if fmt["multitype"]:
                outputDatasource = getOutputDatasource(outputdir,fmt,layer)
                if outputDatasource in outputFiles:
                    cmd = ["ogr2ogr","-skipfailures","-update" ,"-t_srs",(layer.get("srs") or "EPSG:4326"), "-f", fmt["format"],outputDatasource, vrtFile]
                else:
                    cmd = ["ogr2ogr","-skipfailures" ,"-t_srs",(layer.get("srs") or "EPSG:4326"), "-f", fmt["format"],outputDatasource, vrtFile] 
                    outputFiles.append(outputDatasource)
                #print " ".join(cmd)
                subprocess.check_call(cmd) 
            else:
                #get all geometry types in the source layer list
                srcTypes = []
                index = len(layer["sourcelayers"]) - 1
                while index >= 0:
                    srcLayer = layer["sourcelayers"][index]
                    if srcLayer["meta"]["geometry"] in SUPPORTED_GEOMETRY_TYPES:
                        if srcLayer["meta"]["geometry"] not in srcTypes:
                            srcTypes.append(srcLayer["meta"]["geometry"])
                    else:
                        for t in SUPPORTED_GEOMETRY_TYPES:
                            if getFeatureCount(srcLayer["datasource"][0],srcLayer["meta"]["layer"],t) and t not in srcTypes:
                                srcTypes.append(t)

                    index -= 1

                if len(srcTypes) == 1:
                    if "default_geometry_type" in layer:
                        del layer["default_geometry_type"]
                else:
                    hasEmptyFeatures = False
                    index = len(layer["sourcelayers"]) - 1
                    while index >= 0:
                        srcLayer = layer["sourcelayers"][index]
                        index -= 1
                        if getFeatureCount(srcLayer["datasource"][0],srcLayer["meta"]["layer"],"EMPTY") > 0:
                            hasEmptyFeatures = True
                            break

                    if hasEmptyFeatures:
                        if layer.get("default_geometry_type") == "auto":
                            for t in SUPPORTED_GEOMETRY_TYPES:
                                if t in srcTypes:
                                    layer["default_geometry_type"] = t
                                    break
                        
                        elif layer.get("default_geometry_type"):
                            if layer.get("default_geometry_type") not in srcTypes:
                                srcTypes.append("default_geometry_type")
                        else:
                            srcTypes.append("EMPTY")
    
                    elif "default_geometry_type" in layer:
                        del layer["default_geometry_type"]


                if len(srcTypes) == 1:
                    #has only one geometry type
                    outputDatasource = getOutputDatasource(outputdir,fmt,layer)
                    if outputDatasource in outputFiles:
                        cmd = ["ogr2ogr","-skipfailures","-update" ,"-t_srs",(layer.get("srs") or "EPSG:4326"), "-f", fmt["format"],outputDatasource, vrtFile]
                    else:
                        cmd = ["ogr2ogr","-skipfailures","-t_srs",(layer.get("srs") or "EPSG:4326"), "-f", fmt["format"],outputDatasource, vrtFile]
                        outputFiles.append(outputDatasource)
                    #print " ".join(cmd)
                    subprocess.check_call(cmd) 
                else:
                    for t in srcTypes:
                        where = ("OGR_GEOMETRY IS NULL" if t == "EMPTY" else ("OGR_GEOMETRY='{}' OR OGR_GEOMETRY IS NULL" if layer.get("default_geometry_type") == t else "OGR_GEOMETRY='{}'")).format(t)
                        outputDatasource = getOutputDatasource(outputdir,fmt,layer,t)
                        if outputDatasource in outputFiles:
                            cmd = ["ogr2ogr","-skipfailures","-update","-where", where,"-t_srs",(layer.get("srs") or "EPSG:4326"), "-f", fmt["format"],outputDatasource, vrtFile]
                        else:
                            cmd = ["ogr2ogr","-skipfailures","-where", where,"-t_srs",(layer.get("srs") or "EPSG:4326"), "-f", fmt["format"],outputDatasource, vrtFile]
                            outputFiles.append(outputDatasource)
                        #print " ".join(cmd)
                        subprocess.check_call(cmd) 
        
        #import ipdb;ipdb.set_trace()
        outputfile = None
        checkfiles = [outputdir]
        while len(checkfiles) > 0:
            checkfile = checkfiles.pop()
            if os.path.isdir(checkfile):
                dirlist = os.listdir(checkfile)
                checkfiles.extend([os.path.join(checkfile,f) for f in dirlist])
            elif outputfile:
                outputfile = None
                break
            else:
                outputfile = checkfile
        del checkfiles

        #import ipdb;ipdb.set_trace()
        if outputfile:
            filemime = fmt["mime"]
            if filename:
                outputfilename = os.path.basename("{}{}".format(filename,fmt["fileext"]))
            else:
                outputfilename = os.path.basename(outputfile)
        else:
            ct = "application/zip"
            if filename:
                zipfile = os.path.join(workdir,filename)
            else:
                zipfile = os.path.join(workdir,getBaseDatafileName(layer["sourcelayers"][0]["file"]))
            zipfile = zipfile + fmt["fileext"]
            shutil.make_archive(zipfile, 'zip', outputdir)
            outputfile = "{}.zip".format(zipfile)
            filemime = "application/zip"
            outputfilename = os.path.basename(outputfile)

        output = open(outputfile)
        bottle.response.set_header("Content-Type", filemime)
        bottle.response.set_header("Content-Disposition", "attachment;filename='{}'".format(os.path.basename(outputfile)))
        return output
    except:
        bottle.response.status = 400
        bottle.response.set_header("Content-Type","text/plain")
        traceback.print_exc()
        return traceback.format_exception_only(sys.exc_type,sys.exc_value)
    finally:
        try:
            shutil.rmtree(workdir)
            pass
        except:
            pass

def getGeometryArea(geometry,unit):
    geometry_aea = ops.transform(
        partial(
            pyproj.transform,
            pyproj.Proj(init="EPSG:4326"),
            #pyproj.Proj(proj="aea",lat1=geometry.bounds[1],lat2=geometry.bounds[3])
            #use projection 'Albers Equal Conic Area for WA' to calcuate the area
            pyproj.Proj("+proj=aea +lat_1=-17.5 +lat_2=-31.5 +lat_0=0 +lon_0=121 +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs ",lat1=geometry.bounds[1],lat2=geometry.bounds[3])
        ),
        geometry
    )
    data = geometry_aea.area
    if unit == "ha" :
        return data / 10000.00 
    elif unit == "km2":
        return data / 1000000.00 
    else:
        return data
#extract error message from log
#for example: shapely is_valid will print error message in logger and return false to indicate the geometry is invalid; This class is used to extract the error message from log and return to client
class Loghandler(object):
    instances = {}
    def __new__(cls,level):
        if level not in cls.instances:
            instance = super(Loghandler,cls).__new__(cls)
            instance.originHandler = getattr(Logger,level)
            instance.key = "_{}_".format(level)
            instance.enabledKey = "_{}_enabled_".format(level)
            def _handler(log,msg,*args,**kwargs):
                instance(log,msg,*args,**kwargs)
            setattr(Logger,level,_handler)
            cls.instances[level] = instance
        return instance

    @classmethod
    def instance(cls,level):
        if level in cls.instances:
            return instance[level]
        else:
            return Loghandler(level)

    @property
    def enabled(self):
        return getattr(threading.currentThread(),self.enabledKey,False)

    def __call__(self,log,msg,*args,**kwargs):
        if self.enabled:
            message = (msg % args) if args else msg
            if getattr(threading.currentThread(),self.key,None):
                getattr(threading.currentThread(),self.key).append(message)
            else:
                setattr(threading.currentThread(),self.key,[message])

        self.originHandler(log,msg,*args,**kwargs)

    @property
    def messages(self):
        if self.enabled:
            return getattr(threading.currentThread(),self.key,None)
        else:
            return None

    def enable(self,enable):
        if enable:
            setattr(threading.currentThread(),self.enabledKey,enable)
        elif hasattr(threading.currentThread(),self.enabledKey):
            delattr(threading.currentThread(),self.enabledKey)

        if hasattr(threading.currentThread(),self.key):
            delattr(threading.currentThread(),self.key)

loghandlers = [Loghandler("critical"),Loghandler("error"),Loghandler("warning")]
#loghandlers = [Loghandler("critical"),Loghandler("error")]

#return polygon or multipolygons if have, otherwise return None
def extractPolygons(geom):
    if isinstance(geom,Polygon) or isinstance(geom,MultiPolygon):
        return geom
    elif isinstance(geom,GeometryCollection):
        result = None
        for g in geom:
            p = extractPolygons(g)
            if not p:
                continue
            elif not result:
                result = p
            elif isinstance(result,MultiPolygon):
                if isinstance(g,Polygon): 
                    result = MultiPolygon(result.geoms + [g])
                else:
                    result = MultiPolygon(result.geoms + g.geoms)
            else:
                if isinstance(g,Polygon): 
                    result = MultiPolygon([result,g])
                else:
                    result = MultiPolygon([result] + g.geoms)
        return result
    else:
        return None


def calculateArea(session_cookies,results,features,options):
    # needs gdal 1.10+
    layers = options["layers"]
    unit = options["unit"] or "ha"
    overlap = options["layer_overlap"] or False

    total_area = 0
    total_layer_area = 0
    geometry = None
    index = 0
    
    while index < len(features):
        feature = features[index]
        result = results[index]
        index += 1
        geometry = extractPolygons(feature["geometry"])

        if not geometry :
            continue
        #before calculating area, check the polygon first.
        #if polygon is invalid, throw exception
        result["valid"] = True
        result["valid_message"] = ""
        try:
            for handler in loghandlers:
                handler.enable(True)
            if not geometry.is_valid:
                msg = [message.strip() for handler in loghandlers if handler.messages for message in handler.messages]
                result["valid"] = False
                result["valid_message"] = msg
        finally:
            for handler in loghandlers:
                handler.enable(False)

        area_data = {"layers":{}}
        result[options.get("name","area")] = area_data
        if not layers:
            continue
        try:
            area_data["total_area"] = getGeometryArea(geometry,unit)
        except:
            traceback.print_exc()
            bottle.response.status = 490
            if not result["valid"] and result["valid_message"]:
                raise Exception("Calculate total area failed.{}".format("\r\n".join(result["valid_message"])))
            else:
                raise Exception("Calculate total area failed.{}".format(traceback.format_exception_only(sys.exc_type,sys.exc_value)))
            

        for layer in layers:
            try:
                layer_area_data = []
                total_layer_area = 0
                area_data["layers"][layer["id"]] = {"areas":layer_area_data}
    
                layer_features = json.loads(requests.get(
                    "{}&outputFormat=json&bbox={},{},{},{}".format(layer["url"],geometry.bounds[1],geometry.bounds[0],geometry.bounds[3],geometry.bounds[2]),
                    verify=False,
                    cookies=session_cookies
                ).content)
    
                for layer_feature in layer_features["features"]:
                    layer_geometry = shape(layer_feature["geometry"])
                    if not isinstance(layer_geometry,Polygon) and not isinstance(layer_geometry,MultiPolygon):
                        continue
                    intersections = extractPolygons(geometry.intersection(layer_geometry))
                    if not intersections:
                        continue
    
                    layer_feature_area_data = {}
                    for key,value in layer["properties"].iteritems():
                        layer_feature_area_data[key] = layer_feature["properties"][value]
    
                    layer_feature_area_data["area"] = getGeometryArea(intersections,unit)
                    total_layer_area  += layer_feature_area_data["area"]
                    layer_area_data.append(layer_feature_area_data)
    
                area_data["layers"][layer["id"]]["total_area"] = total_layer_area
                total_area += total_layer_area
                if not overlap and total_area >= area_data["total_area"] :
                    break


            except:
                traceback.print_exc()
                bottle.response.status = 490
                if not result["valid"] and result["valid_message"]:
                    raise Exception("Calculate intersection area between fire boundary and layer '{}' failed.{}".format(typename(layer["url"]) or layer["id"],"\r\n".join(result["valid_message"])))
                else:
                    raise Exception("Calculate intersection area between fire boundary and layer '{}' failed.{}".format(typename(layer["url"]) or layer["id"],traceback.format_exception_only(sys.exc_type,sys.exc_value)))
    
            if not overlap and total_area < area_data["total_area"]:
                area_data["other_area"] = area_data["total_area"] - total_area

    
@bottle.route("/spatial", method="POST")
def spatial():
    # needs gdal 1.10+
    try:
        features = json.loads(bottle.request.forms.get("features"))
        options = bottle.request.forms.get("options")
        if options:
            options = json.loads(options)
        else:
            options = {}

        session_cookie = get_session_cookie()
        cookies={sso_cookie_name:session_cookie}
        results = []

        features = features["features"] or []
        for feature in features:
            if feature["geometry"]["type"] == "GeometryCollection":
                feature["geometry"] = GeometryCollection([shape(g) for g in feature["geometry"]["geometries"]])
            else:
                feature["geometry"] = shape(feature["geometry"])
            results.append({})
    
        if "area" in options:
            calculateArea(cookies,results,features,options["area"])

        bottle.response.set_header("Content-Type", "application/json")
        return {"total_features":len(results),"features":results}
    except:
        if bottle.response.status < 400 :
            bottle.response.status = 400
        bottle.response.set_header("Content-Type","text/plain")
        traceback.print_exc()
        return traceback.format_exception_only(sys.exc_type,sys.exc_value)
    



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
