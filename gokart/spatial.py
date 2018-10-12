import bottle
import sys
import requests
import json
import pyproj
import traceback
import threading
import math
import pyproj
from shapely.ops import transform

from shapely.geometry import shape,MultiPoint,Point
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.collection import GeometryCollection
from shapely import ops
from functools import partial
from logging import Logger

import settings
import kmi


proj_wgs84 = pyproj.Proj(init='epsg:4326')
def buffer(lon, lat, meters):
    """
    Create a buffer around a point
    """
    # Azimuthal equidistant projection
    aeqd_proj = '+proj=aeqd +lat_0={} +lon_0={} +x_0=0 +y_0=0'
    project = partial(
        pyproj.transform,
        pyproj.Proj(aeqd_proj.format(lat, lon)),
        proj_wgs84)
    buf = Point(0, 0).buffer(meters)  # distance in metres
    return transform(project, buf).exterior.coords[:]


def getGeometryArea(geometry,unit,init_proj="EPSG:4326"):
    """
    Get polygon's area using albers equal conic area
    """
    if init_proj == 'aea':
        geometry_aea = geometry
    else:
        geometry_aea = ops.transform(
            partial(
                pyproj.transform,
                pyproj.Proj(init=init_proj),
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

def getDistance(p1,p2,unit="m",p1_proj="EPSG:4326",p2_proj="EPSG:4326"):
    if p1_proj == 'aea':
        p1_aea = p1
    else:
        p1_aea = ops.transform(
            partial(
                pyproj.transform,
                pyproj.Proj(init=p1_proj),
                #pyproj.Proj(proj="aea",lat1=geometry.bounds[1],lat2=geometry.bounds[3])
                #use projection 'Albers Equal Conic Area for WA' to calcuate the area
                pyproj.Proj("+proj=aea +lat_1=-17.5 +lat_2=-31.5 +lat_0=0 +lon_0=121 +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs ",lat1=p1.bounds[1],lat2=p1.bounds[3])
            ),
            p1
        )

    if p2_proj == 'aea':
        p2_aea = p2
    else:
        p2_aea = ops.transform(
            partial(
                pyproj.transform,
                pyproj.Proj(init=p2_proj),
                #pyproj.Proj(proj="aea",lat1=geometry.bounds[1],lat2=geometry.bounds[3])
                #use projection 'Albers Equal Conic Area for WA' to calcuate the area
                pyproj.Proj("+proj=aea +lat_1=-17.5 +lat_2=-31.5 +lat_0=0 +lon_0=121 +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs ",lat1=p2.bounds[1],lat2=p2.bounds[3])
            ),
            p2
        )

    data = p1_aea.distance(p2_aea)
    if unit == "km" :
        return data / 1000.00 
    else:
        return data

#extract error message from log
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
                result = [geom1 for geom1 in result.geoms]
                if isinstance(p,Polygon): 
                    result.append(p)
                    result = MultiPolygon(result)
                else:
                    for geom1 in p.geoms:
                        result.append(geom1)
                    result = MultiPolygon(result)
            else:
                if isinstance(p,Polygon): 
                    result = MultiPolygon([result,p])
                else:
                    result = [result]
                    for geom1 in p.geoms:
                        result.append(geom1)
                    result = MultiPolygon(result)
        return result
    else:
        return None

def extractPoints(geom):
    if isinstance(geom,Point) or isinstance(geom,MultiPoint):
        return geom
    elif isinstance(geom,GeometryCollection):
        result = None
        for g in geom:
            p = extractPoints(g)
            if not p:
                continue
            elif not result:
                result = p
            elif isinstance(result,MultiPoint):
                result = [geom1 for geom1 in result.geoms]
                if isinstance(p,Point): 
                    result.append(p)
                    result = MultiPoint(result)
                else:
                    for geom1 in p.geoms:
                        result.append(geom1)
                    result = MultiPoint(result)
            else:
                if isinstance(p,Point): 
                    result = MultiPoint([result,p])
                else:
                    result = [result]
                    for geom1 in p.geoms:
                        result.append(geom1)
                    result = MultiPoint(result)
        return result
    else:
        return None

def retrieveFeatures(url,session_cookies):
        res = requests.get(url,verify=False,cookies=session_cookies)
        res.raise_for_status()
        return res.json()

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
        features[layer["id"]] = retrieveFeatures(
            "{}&outputFormat=json&bbox={},{},{},{}".format(layer["url"],geometry.bounds[1],geometry.bounds[0],geometry.bounds[3],geometry.bounds[2]),
            session_cookies
        )["features"]

        for layer_feature in features[layer["id"]]:
            layer_geometry = shape(layer_feature["geometry"])
            layer_feature["layer_id"] = layer["id"]
            layer_feature["geometry"] = layer_geometry

    #check whether the features from different layers are overlap or not
    layergroup_index1 = 0
    while layergroup_index1 < len(layers) - 1:
        layer1 = layers[layergroup_index1]
        layer_features1 = features[layer1["id"]]

        #check whether layer's features are overlap or not.
        feature_index1 = 0
        while feature_index1 < len(layer_features1):
            feature1 = layer_features1[feature_index1]
            feature_geometry1 = feature1["geometry"]
            if not isinstance(feature_geometry1,Polygon) and not isinstance(feature_geometry1,MultiPolygon):
                feature_index1 += 1
                continue

            layergroup_index2 = layergroup_index1 + 1
            while layergroup_index2 < len(layers):
                layer2 = layers[layergroup_index2]
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
                layergroup_index2 += 1
            feature_index1 += 1
        layergroup_index1 += 1
    return overlaps
                

def calculateArea(session_cookies,results,result_key,features,options):
    """
    feature area data:{
        status {
             "invalid" : invalid message; 
             "failed" : failed message; 
             "overlapped" : overlap message

        }
        data: {
            total_area: 100   //exist if status_code = 1
            other_area: 10    //exist if status_code = 1 and len(layers) > 0
            layers: {   //exist if status_code = 1 and len(layers) > 0 
                layer id: {
                    total_area: 12
                    areas:[
                        {area:1, properties:{
                            name:value
                        }}
                    ]
                }
            }
        }
    }
    """
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
        
        area_data = {}
        status = {}
        result = {"status":status,"data":area_data}
        results[index][result_key] = result
        total_area = 0
        index += 1
        geometry = extractPolygons(feature["geometry"])

        if not geometry :
            area_data["total_area"] = 0
            continue

        #before calculating area, check the polygon first.
        #if polygon is invalid, throw exception
        try:
            for handler in loghandlers:
                handler.enable(True)
            if not geometry.is_valid:
                msg = [message.strip() for handler in loghandlers if handler.messages for message in handler.messages]
                status["invalid"] = msg
        finally:
            for handler in loghandlers:
                handler.enable(False)

        #status["invalid"] = ["invalid geometry"]

        try:
            area_data["total_area"] = getGeometryArea(geometry,unit)
        except:
            traceback.print_exc()
            if "invalid" in status:
                status["failed"] = "Calculate total area failed.{}".format("\r\n".join(status["invalid"]))
            else:
                status["failed"] = "Calculate total area failed.{}".format(traceback.format_exception_only(sys.exc_type,sys.exc_value))

            continue

        if not layers:
            continue

        area_data["layers"] = {}

        for layer in layers:
            if merge_result:
                areas_map.clear()

            try:
                layer_area_data = []
                total_layer_area = 0
                area_data["layers"][layer["id"]] = {"areas":layer_area_data}
    
                layer_features = retrieveFeatures(
                    "{}/wfs?service=wfs&version=2.0&request=GetFeature&typeNames={}&outputFormat=json&bbox={},{},{},{}".format(layer["kmiservice"],layer["layerid"],geometry.bounds[1],geometry.bounds[0],geometry.bounds[3],geometry.bounds[2]),
                    session_cookies
                )["features"]
    
                for layer_feature in layer_features:
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
                status["failed"] = "Calculate intersection area between fire boundary and layer '{}' failed.{}".format(layer["layerid"] or layer["id"],traceback.format_exception_only(sys.exc_type,sys.exc_value))

                break

        if "failed" in status:
            #calcuating area failed
            continue
    
        if not overlap :
            area_data["other_area"] = area_data["total_area"] - total_area
            if area_data["other_area"] < -0.01: #tiny difference is allowed.
                #some layers are overlap
                if not settings.CHECK_OVERLAP_IF_CALCULATE_AREA_FAILED:
                    status["overlapped"] = "The sum({0}) of the burning areas in individual layers are ({2}) greater than the total burning area({1}).\r\n The features from layers({3}) are overlaped, please check.".format(round(total_area,2),round(area_data["total_area"],2),round(math.fabs(area_data["other_area"]),2),", ".join([layer["id"] for layer in layers]))
                    continue
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
                        status["overlapped"] = "Features from layers are overlaped.\r\n{}".format("\r\n".join(msg))
                        continue

def layermetadata(layer):
    if not layer.get("_layermetadata"):
        layer["_layermetadata"] = kmi.get_layermetadata(layer["layerid"],kmiserver=layer["kmiservice"])
    return layer["_layermetadata"]

def layerdefinition(layer):
    if not layer.get("layerdefinition"):
        layerdefinition = kmi.get_layerdefinition(layer["layerid"],kmiserver=layer["kmiservice"])
        layer["layerdefinition"] = layerdefinition
    else:
        layerdefinition = layer["layerdefinition"]

    if not layerdefinition["geometry_property"]:
        if layerdefinition["geometry_property_msg"]:
            raise Exception(layerdefinition["geometry_property_msg"])
        elif not layerdefinition["geometry_properties"]:
            raise Exception("The layer '{}' is not a spatial layer".format(layer["layerid"]))
        else:
            raise Exception("Failed to identify the geometry property of the layer '{}'".format(layer["layerid"]))

    return layerdefinition
    

def getFeature(session_cookies,results,result_key,features,options):
    """
    result_key: the key to put the result in results
    options:{
        format: properties or geojson//optional default is properties
        action: getFeature or getIntersectedFeatures or getClosestFeature
        layers:[
            {
                id:     //if missing, use 'layerid' as id
                layerid: //layerid in kmi, in most cases, layerid is equal with id, if missing, use 'id' as layerid
                kmiservice: //optinoal, 
                properties:{  //optional
                    name:column in dataset
                }
            },
            ...
        ]

    }
    getFeature result:[
        {
            id:
            layer: 
            failed:  message if failed; otherwise is null
            properties: {
                name:value
            }
        },
    ]
    """
    # needs gdal 1.10+
    layers = options["layers"]
    #check whether layers is not empty
    if not layers:
        raise Exception("Layers must not be empty.")
    #check whether layers is list
    if not isinstance(layers,(list,tuple)):
        raise Exception("Layers must be list type.")

    #layers must be list of layers
    if  not isinstance(layers,(list,tuple)):
        layers = [layers]
    for layer in layers:
        if "layerid" not in layer and "id" not in layer:
            raise Exception("Both 'id' and 'layerid' are missing in layer declaration")
        elif "layerid" not in layer:
            layer["layerid"] = layer["id"]
        elif "id" not in layer:
            layer["id"] = layer["layerid"]
        if not layer.get("kmiservice"):
            layer["kmiservice"] = "https://kmi.dbca.wa.gov.au/geoserver"

    index = 0
    while index < len(features):
        feature = features[index]
        get_feature_data = {"id":None,"layer":None,"failed":None}
        results[index][result_key] = get_feature_data
        index += 1

        geometry = feature["geometry"]

        try:
            for layer in layers:
                if not layer or not layer.get("kmiservice") or not layer["buffer"] or not layer["layerid"]:
                    continue

                if layer.get('check_bbox'):
                    #check whether feature is in layer's bbox
                    layer_bbox = layermetadata(layer).get("latlonBoundingBox_EPSG:4326") or layermetadata(layer).get("latlonBoundingBox")
                    if not layer_bbox:
                        get_feature_data["failed"] = "Can't find layer({})'s bounding box for epsg:4326".format(layer["layerid"])
                        break

                    if geometry.x < layer_bbox[1] or geometry.x > layer_bbox[3] or geometry.y < layer_bbox[0] or geometry.y > layer_bbox[2]:
                        #not in this layer's bounding box
                        continue

                if options["action"] == "getFeature":
                    get_feature_data["feature"] = None

                    if isinstance(geometry,Point):
                        if layerdefinition(layer)["geometry_type"] in ["point",'multipoint']:
                            get_feature_data["failed"] = "The {1} layer '{0}' doesn't support action '{2}'. ".format(layer["layerid"],layerdefinition(layer)["geometry_property"]["localType"],options["action"])
                            break
                        else:
                            #polygon or line
                            layer_features = retrieveFeatures(
                                "{}/wfs?service=wfs&version=2.0&request=GetFeature&typeNames={}&outputFormat=json&cql_filter=CONTAINS({},POINT({} {}))".format(layer["kmiservice"],layer["layerid"],layerdefinition(layer)["geometry_property"]["name"],geometry.x,geometry.y),
                                session_cookies
                            )["features"]

                    else:
                        get_feature_data["failed"] = "Action '{}' Only support Point geometry.".format(options["action"])
                        break
                elif options["action"] == "getIntersectedFeatures":
                    get_feature_data["features"] = None
                    if isinstance(geometry,Point):
                        if not layer.get("buff"):
                            get_feature_data["failed"] = "'buff' is missing in layer '{}'".format(layer["id"])
                            break
                        buff_polygon = Polygon(buffer(geometry.x,geometry.y,layer["buff"]))
                        layer_features = retrieveFeatures(
                            "{}/wfs?service=wfs&version=2.0&request=GetFeature&typeNames={}&outputFormat=json&cql_filter=INTERSECTS({},POLYGON(({})))".format(layer["kmiservice"],layer["layerid"],layerdefinition(layer)["geometry_property"]["name"],"%2C".join(["{} {}".format(coord[0],coord[1]) for coord in list(buff_polygon.exterior.coords)])),
                            session_cookies
                        )["features"]
                    elif isinstance(geometry,Polygon):
                        layer_features = retrieveFeatures(
                            "{}/wfs?service=wfs&version=2.0&request=GetFeature&typeNames={}&outputFormat=json&cql_filter=INTERSECTS({},POLYGON(({})))".format(layer["kmiservice"],layer["layerid"],layerdefinition(layer)["geometry_property"]["name"],"%2C".join(["{} {}".format(coord[0],coord[1]) for coord in list(geometry.exterior.coords)])),
                            session_cookies
                        )["features"]
                    else:
                        get_feature_data["failed"] = "Action '{}' Only support Point and Polygon geometry.".format(options["action"])
                        break

                elif options["action"] == "getClosestFeature":
                    get_feature_data["feature"] = None
                    layer_feature = None
                    if not isinstance(geometry,Point):
                        get_feature_data["failed"] = "Action '{}' Only support Point geometry.".format(options["action"])
                        break
                    #should get the grid data at the first try, if can't, set the grid data to null.
                    for buff in layer["buffer"] if isinstance(layer["buffer"],(list,tuple)) else [layer["buffer"]]:
                        buff_bbox = Polygon(buffer(geometry.x,geometry.y,buff)).bounds
                        layer_features = retrieveFeatures(
                            "{}/wfs?service=wfs&version=2.0&request=GetFeature&typeNames={}&outputFormat=json&bbox={},{},{},{},urn:ogc:def:crs:EPSG:4326".format(layer["kmiservice"],layer["layerid"],buff_bbox[1],buff_bbox[0],buff_bbox[3],buff_bbox[2]),
                            session_cookies
                        )["features"]

                        if len(layer_features) == 1:
                            layer_feature = layer_features[0]
                            break
                        elif len(layer_features) > 1:   
                            layer_feature = None
                            minDistance = None
                            for feat in layer_features:
                                if layer_feature is None:
                                    layer_feature = feat
                                    minDistance = getDistance(geometry,shape(feat["geometry"]),p2_proj=layermetadata(layer).get('srs') or "EPSG:4326")
                                else:
                                    distance = getDistance(geometry,shape(feat["geometry"]),p2_proj=layermetadata(layer).get('srs') or "EPSG:4326")
                                    if minDistance > distance:
                                        minDistance = distance
                                        layer_feature = feat
                            break
                    if layer_feature:
                        layer_features = [layer_feature]
                else:
                    get_feature_data["failed"] = "Action '{}' Not Support".format(options["action"])
                    break

                if layer_features:
                    if "feature" in get_feature_data and len(layer_features) > 1:
                        get_feature_data["failed"] = "Found {1} features in layer '{0}' ".format(layer["layerid"],len(layer_features))
                        break
                    if layer_features:    
                        get_feature_data["id"] = layer["id"]
                        get_feature_data["layer"] = layer["layerid"]
                        for layer_feature in layer_features:
                            feat = {}
                            if layer.get("properties"):
                                for name,column in layer["properties"].iteritems():
                                    feat[name] = layer_feature["properties"][column]
                            else:
                                for key,value in layer_feature["properties"].iteritems():
                                    feat[key] = value
                                    
                            if options.get("format") == "geojson":
                                #return geojson
                                layer_feature["properties"] = feat
                                feat = layer_feature
                            if "feature" in get_feature_data:
                                get_feature_data["feature"] = feat
                            elif "features" in get_feature_data:
                                if get_feature_data["features"]:
                                    get_feature_data["features"].append(feat)
                                else:
                                    get_feature_data["features"] = [feat]

                        break

        except:
            traceback.print_exc()
            get_feature_data["failed"] = "{} from layers ({}) failed.{}".format(options["action"],layers,traceback.format_exception_only(sys.exc_type,sys.exc_value))

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
    
        for key,val in options.iteritems():
            if "action" not in val:
                val["action"] = key
            if val["action"] == "getArea":
                calculateArea(cookies,results,key,features,val)
            else:
                getFeature(cookies,results,key,features,val)

        bottle.response.set_header("Content-Type", "application/json")
        return {"total_features":len(results),"features":results}
    except:
        if bottle.response.status < 400 :
            bottle.response.status = 400
        bottle.response.set_header("Content-Type","text/plain")
        traceback.print_exc()
        return traceback.format_exception_only(sys.exc_type,sys.exc_value)
    
