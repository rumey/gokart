import json
import hashlib
import re
import uwsgi
import base64
import os
import pytz
import subprocess
import tempfile
import requests
from datetime import datetime,timedelta
import pytesseract
try:
    from PIL import Image
except:
    import Image

import bottle

from .settings import *
from .spatial import *
from .gdal import *
from .raster import *


@bottle.route('/client')
def server_static():
    return bottle.static_file('client.html', root=BASE_PATH)

# serve up map apps
@bottle.route('/<app>')
def index(app):
    print([x for x in bottle.request.headers.items()])
    print(bottle.request.headers.get('X-email', 'ohnoes'))
    return bottle.template('index.html', app=app,envType=ENV_TYPE)

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

# WMS shim for Himawari 8
# Landgate tile servers, round robin
FIREWATCH_SERVICE = "/mapproxy/firewatch/service"
FIREWATCH_GETCAPS = FIREWATCH_SERVICE + "?service=wms&request=getcapabilities"
FIREWATCH_HTTPS_VERIFY = Setting.getBool("FIREWATCH_HTTPS_VERIFY",True)

@bottle.route("/hi8/<target>")
def himawari8(target):
    baseUrl = bottle.request.url[0:bottle.request.url.find("/hi8")]
    if uwsgi.cache_exists("himawari8"):
        getcaps = uwsgi.cache_get("himawari8")
    else:
        getcaps = requests.get("{}{}".format(baseUrl,FIREWATCH_GETCAPS),verify=FIREWATCH_HTTPS_VERIFY).content
        uwsgi.cache_set("himawari8", getcaps, 60*10)  # cache for 10 mins
    getcaps = getcaps.decode("utf-8")
    layernames = re.findall("\w+HI8\w+{}\.\w+".format(target), getcaps)
    layers = []
    for layer in layernames:
        layers.append([PERTH_TIMEZONE.localize(datetime.strptime(re.findall("\w+_(\d+)_\w+", layer)[0], "%Y%m%d%H%M")).isoformat(), layer])
    result = {
        "servers": [baseUrl + FIREWATCH_SERVICE],
        "layers": layers
    }
    return result



basetime_url = os.environ.get("BOM_BASETIME_URL") or "https://kmi.dbca.wa.gov.au/geoserver/bom/wms?service=WMS&version=1.1.0&request=GetMap&styles=&bbox=70.0,-55.0,195.0,20.0&width=768&height=460&srs=EPSG:4283&format=image%2Fgif&layers={}"
basetime_re = re.compile("(\d{4})-(\d{2})-(\d{2})\s*(\d{2})\D*(\d{2})\s*(UTC)")
def getTimelineFromWmsLayer(target,current_timeline):
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
        import ipdb;ipdb.set_trace()
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


    timeline = getTimelineFromWmsLayer(target,current_timeline)

    if not timeline:
        raise "Missing some of http parameters 'basetimelayer', 'timelinesize', 'layertimespan'."

    if not current_timeline or id(timeline) != id(current_timeline):
        uwsgi.cache_set(target, json.dumps(timeline), 0) 

    if timeline["updatetime"] == last_updatetime:
        bottle.response.status = 290
        return "{}"
    else:
        return {"layers":timeline["layers"],"updatetime":timeline["updatetime"]}


application = bottle.default_app()
