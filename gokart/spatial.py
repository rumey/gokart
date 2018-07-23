import bottle
import sys
import requests
import json
import pyproj
import traceback
import threading
import math
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
                result = [geom for geom in result.geoms]
                if isinstance(g,Polygon): 
                    result.append(g)
                    result = MultiPolygon(result)
                else:
                    for geom in g.geoms:
                        result.append(geom)
                    result = MultiPolygon(result)
            else:
                if isinstance(g,Polygon): 
                    result = MultiPolygon([result,g])
                else:
                    result = [result]
                    for geom in g.geoms:
                        result.append(geom)
                    result = MultiPolygon(result)
        return result
    else:
        return None

def checkOverlap(session_cookies,feature,options):
    # needs gdal 1.10+
    layers = options["layers"]

    geometry = extractPolygons(feature["geometry"])

    if not geometry :
        return
    
    features = {}
    overlaps = []
    #retrieve all related features from layers
    for layer in layers:
        features[layer["id"]] = json.loads(requests.get(
            "{}&outputFormat=json&bbox={},{},{},{}".format(layer["url"],geometry.bounds[1],geometry.bounds[0],geometry.bounds[3],geometry.bounds[2]),
            verify=False,
            cookies=session_cookies
        ).content).get("features") or []

        for layer_feature in features[layer["id"]]:
            layer_geometry = shape(layer_feature["geometry"])
            layer_feature["layer_id"] = layer["id"]
            layer_feature["geometry"] = layer_geometry

    #check whether the features from different layers are overlap or not
    layer_index1 = 0
    while layer_index1 < len(layers) - 1:
        layer1 = layers[layer_index1]
        layer_features1 = features[layer1["id"]]

        #check whether layer's features are overlap or not.
        feature_index1 = 0
        while feature_index1 < len(layer_features1):
            feature1 = layer_features1[feature_index1]
            feature_geometry1 = feature1["geometry"]
            if not isinstance(feature_geometry1,Polygon) and not isinstance(feature_geometry1,MultiPolygon):
                feature_index1 += 1
                continue

            layer_index2 = layer_index1 + 1
            while layer_index2 < len(layers):
                layer2 = layers[layer_index2]
                layer_features2 = features[layer2["id"]]
                feature_index2 = 0

                while feature_index2 < len(layer_features2):
                    feature2 = layer_features2[feature_index2]
                    feature_geometry2 = feature2["geometry"]
                    feature_geometry1 = feature1["geometry"]
                    if not isinstance(feature_geometry2,Polygon) and not isinstance(feature_geometry2,MultiPolygon):
                        feature_index2 += 1
                        continue
                    intersections = extractPolygons(feature_geometry1.intersection(feature_geometry2))
                    if not intersections:
                        feature_index2 += 1
                        continue

                    overlaps.append((feature1,feature2,intersections))

                    feature_index2 += 1
                layer_index2 += 1
            feature_index1 += 1
        layer_index1 += 1
    return overlaps
                

def calculateArea(session_cookies,results,features,options):
    # needs gdal 1.10+
    layers = options["layers"]
    unit = options["unit"] or "ha"
    overlap = options["layer_overlap"] or False
    merge_result = options.get("merge_result",False)

    total_area = 0
    total_layer_area = 0
    geometry = None
    index = 0

    areas_map = {} if merge_result else None
    area_key = None
    while index < len(features):
        feature = features[index]
        result = results[index]
        total_area = 0
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
            if merge_result:
                areas_map.clear()

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
                    
                    layer_feature_area_data = None
                    #try to get the area data from map
                    if merge_result:
                        area_key = []
                        for key,value in layer["properties"].iteritems():
                            area_key.append(layer_feature["properties"][value])
                        
                        area_key = tuple(area_key)
                        layer_feature_area_data = areas_map.get(area_key)

                    if not layer_feature_area_data:
                         #map is not enabled,or data does not exist in map,create a new one
                        layer_feature_area_data = {"area":0}
                        for key,value in layer["properties"].iteritems():
                            layer_feature_area_data[key] = layer_feature["properties"][value]
                        layer_area_data.append(layer_feature_area_data)

                        if merge_result:
                            #save it into map
                            areas_map[area_key] = layer_feature_area_data

                    feature_area = getGeometryArea(intersections,unit)
                    layer_feature_area_data["area"] += feature_area
                    total_layer_area  += feature_area
    
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
    
        if not overlap :
            area_data["other_area"] = area_data["total_area"] - total_area
            if options.get("failed_if_overlap",True) and area_data["other_area"] < -0.01: #tiny difference is allowed.
                #some layers are overlap
                bottle.response.status = 490
                if not settings.CHECK_OVERLAP_IF_CALCULATE_AREA_FAILED:
                    raise Exception("The sum({0}) of the burning areas in individual layers are ({2}) greater than the total burning area({1}).\r\n The Features from layers({3}) are overlaped, please check.".format(round(total_area,2),round(area_data["total_area"],2),round(math.fabs(area_data["other_area"]),2),", ".join([layer["id"] for layer in layers])))
                else:
                    overlaps = checkOverlap(session_cookies,feature,options)
                    if overlaps:
                        msg = []
                        for overlap in overlaps:
                            #try to get the primary key from options
                            layer1_id = overlap[0]["layer_id"]
                            layer2_id = overlap[1]["layer_id"]
                            layer1 = None
                            for layer in layers:
                                if layer["id"] == layer1_id:
                                    layer1 = layer
                                    break

                            for layer in layers:
                                if layer["id"] == layer2_id:
                                    layer2 = layer
                                    break

                            layer1_pk = layer1.get("primary_key")
                            layer2_pk = layer2.get("primary_key")

                            if layer1_pk:
                                if isinstance(layer1_pk,basestring):
                                    feature1 = "{}({}={})".format(layer1_id,layer1_pk,overlap[0]["properties"][layer1_pk])
                                else:
                                    feature1 = "{}()".format(layer1_id,", ".join(["{}={}".format(k,v) for k,v in overlap[0]["properties"].iteritems() if k in layer1_pk ]))
                            else:
                                feature1 = "{}({})".format(layer1_id,json.dumps(overlap[0]["properties"]))

                            if layer2_pk:
                                if isinstance(layer2_pk,basestring):
                                    feature2 = "{}({}={})".format(layer2_id,layer2_pk,overlap[1]["properties"][layer2_pk])
                                else:
                                    feature2 = "{}()".format(layer2_id,", ".join(["{}={}".format(k,v) for k,v in overlap[1]["properties"].iteritems() if k in layer2_pk ]))
                            else:
                                feature2 = "{}({})".format(layer2_id,json.dumps(overlap[1]["properties"]))

                            msg.append("intersect({}, {}) = {} ".format( feature1,feature2, overlap[2] ))
                        with open("/tmp/overlap_{}.log".format(feature["properties"].get("id","feature")),"w") as f:
                            f.write("\n".join(msg))
                        raise Exception("Features are overlaped.\r\n{}".format("\r\n".join(msg)))


    
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
    
