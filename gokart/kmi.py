import settings
import bottle
import traceback
import requests
import sys
import json
try:
    import uwsgi
except:
    # ignore uwsgi when profiling
    pass

import xml.etree.ElementTree as ET


def get_child_value(node,child_name):
    try:
        return node.find(child_name).text
    except:
        return None

def layermetadatakey(layerid):
    return "layermetadata_{}".format(layerid)

def get_layermetadata(layerids,kmiserver="https://kmi.dbca.wa.gov.au"):
    #initialize kmiserver
    kmiserver = kmiserver or "https://kmi.dbca.wa.gov.au"
    if  kmiserver.endswith("/"):
        kmiserver = kmiserver[:-1]

    multiple_layers = True
    if isinstance(layerids,basestring):
        layerids = [layerids]
        multiple_layers = False
    results = {}
    #group layers against layer workspace
    layers = {}
    for layerid in layerids:
        layerid = layerid.strip()
        #check whether it is cached or not
        key = layermetadatakey(layerid)
        if uwsgi.cache_exists(key):
            try:
                metadata = uwsgi.cache_get(key)
                if metadata:
                    results[layerid] = json.loads(metadata)
                    print("Retrieve the metadata from cache for layer ({})".format(layerid))
                    continue
            except:
                pass

        layer = layerid.split(":")

        if len(layer) == 1:
            #no workspace
            layer_ws = ""
            layer = layer[0]
        else:
            layer_ws = layer[0]
            layer = layer[1]

        if layer_ws not in layers:
            layers[layer_ws] = [layer]
        else:
            layers[layer_ws].append(layer)


    session_cookie = settings.get_session_cookie()

    #find the layer's metadata 
    url = None
    for layer_ws,layers in layers.iteritems():
        if layer_ws:
            url = "{}/{}/wms?service=wms&version=1.1.1&request=GetCapabilities".format(kmiserver,layer_ws)
        else:
            url = "{}/wms?service=wms&version=1.1.1&request=GetCapabilities".format(kmiserver)

        tree = ET.fromstring(requests.get(
            url,
            verify=False,
            cookies={settings.sso_cookie_name:session_cookie}
        ).content)

        capability = tree.find('Capability')
        if not len(capability):
            raise Exception("getCapability failed")
        kmi_layers = capability.findall("Layer")
        while kmi_layers:
            kmi_layer = kmi_layers.pop()
            name = get_child_value(kmi_layer,"Name")
            
            if name:
                try:
                    index = layers.index(name)
                except:
                    index = -1
                if index >= 0:
                    #this layer's metadata is requsted by the user
                    if layer_ws:
                        result = {"id":"{}:{}".format(layer_ws,name)}
                    else:
                        result = {"id":name}
                    results[result["id"]] = result
                    del layers[index]

                    result["title"] = get_child_value(kmi_layer,"Title")
                    result["abstract"] = get_child_value(kmi_layer,"Abstract")
                    result["srs"] = get_child_value(kmi_layer,"SRS")
                    bbox = kmi_layer.find("LatLonBoundingBox")
                    if bbox is  not None:
                        result["latlonBoundingBox"] = [float(bbox.attrib["miny"]),float(bbox.attrib["minx"]),float(bbox.attrib["maxy"]),float(bbox.attrib["maxx"])]
                    else:
                        result["latlonBoundingBox"] = None
                    for bbox in kmi_layer.findall("BoundingBox"):
                        result["latlonBoundingBox_{}".format(bbox.attrib["SRS"].upper())] = [float(bbox.attrib["miny"]),float(bbox.attrib["minx"]),float(bbox.attrib["maxy"]),float(bbox.attrib["maxx"])]

                    #cache it for 1 hour
                    key = layermetadatakey(result["id"])
                    try:
                        if uwsgi.cache_exists(key):
                            uwsgi.cache_update(key, json.dumps(result),3600)
                        else:
                            uwsgi.cache_set(key, json.dumps(result),3600)
                    except:
                        pass
                        
                    print("Retrieve the metadata from kmi for layer ({})".format(result["id"]))

                    if len(layers):
                        continue
                    else:
                        #already find metadata for all required layers
                        break
            sub_layers = kmi_layer.findall("Layer")
            if sub_layers:
                kmi_layers += sub_layers
        
        if len(layers) == 1:
            if layer_ws:
                raise Exception("The layer({}:{}) Not Found".format(layer_ws,layers[0]))
            else:
                raise Exception("The layer({}) Not Found".format(layers[0]))
        elif len(layers) > 1:
            if layer_ws:
                raise Exception("The layers({}) Not Found".format(",".join(["{}:{}".format(layer_ws,l) for l in layers])))
            else:
                raise Exception("The layers({}) Not Found".format(",".join(layers)))

    if multiple_layers:
        return results
    else:
        return results[layerids[0]]

def layermetadata():
    try:
        kmiserver = bottle.request.query.get("server") or "https://kmi.dbca.wa.gov.au/"
        if not kmiserver.endswith("/"):
            kmiserver = "{}/".format(kmiserver)

        layer = bottle.request.query.get("layer")
        if not layer:
            raise Exception("Missing parameter 'layer'")
        else:
            layers = [l.strip() for l in layer.split(",") if l.strip()]

        bottle.response.set_header("Content-Type", "application/json")
        return get_layermetadata(layers,kmiserver)
    except:
        if bottle.response.status < 400 :
            bottle.response.status = 400
        bottle.response.set_header("Content-Type","text/plain")
        traceback.print_exc()
        return traceback.format_exception_only(sys.exc_type,sys.exc_value)
    
