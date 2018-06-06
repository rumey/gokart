import bottle
import sys
import requests
import json
import pyproj
import traceback
import threading
from shapely.geometry import shape
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.collection import GeometryCollection
from shapely import ops
from functools import partial
from logging import Logger

import settings

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
                    raise Exception("Calculate intersection area between fire boundary and layer '{}' failed.{}".format(settings.typename(layer["url"]) or layer["id"],"\r\n".join(result["valid_message"])))
                else:
                    raise Exception("Calculate intersection area between fire boundary and layer '{}' failed.{}".format(settings.typename(layer["url"]) or layer["id"],traceback.format_exception_only(sys.exc_type,sys.exc_value)))
    
        if not overlap and total_area < area_data["total_area"]:
            area_data["other_area"] = area_data["total_area"] - total_area

    
def spatial():
    # needs gdal 1.10+
    try:
        features = json.loads(bottle.request.forms.get("features"))
        options = bottle.request.forms.get("options")
        if options:
            options = json.loads(options)
        else:
            options = {}

        session_cookie = settings.get_session_cookie()
        cookies={settings.sso_cookie_name:session_cookie}
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
    

