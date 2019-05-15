import json
from shapely.geometry import shape,MultiPoint,Point
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon

def getShapelyGeometry(feature):
    if feature["geometry"]["type"] == "GeometryCollection":
        return GeometryCollection([shape(g) for g in feature["geometry"]["geometries"]])
    else:
        return shape(feature["geometry"])

#return polygon or multipolygons if have, otherwise return None
def extractPolygons(geom,to_multiple=False):
    if isinstance(geom,Polygon):
        if to_multiple:
            return MultiPolygon([result])
        else:
            return geom
    elif isinstance(geom,MultiPolygon):
        return geom
    elif isinstance(geom,GeometryCollection):
        result = None
        for g in geom:
            p = extractPolygons(g,to_multiple)
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

def selfintersect_points(ring):
    index = 0
    coord_map = {}
    duplicate_coords = []
    for coord in ring.coords:
        if coord in coord_map:
            coord_map[coord].append(index)
            if coord not in duplicate_coords:
                duplicate_coords.append(coord)
        else:
            coord_map[coord] = [index]
        index += 1

    result = []
    for coord in duplicate_coords:
        if any([i for i in coord_map[coord] if i != 0 and  i != len(ring.coords) - 1]):
            result.append((coord,coord_map[coord]))

    return result

def check_selfintersect(geojsonfile,properties=None):
    with open(geojsonfile) as f:
        features = json.loads(f.read())

    features = features["features"]

    selfintersect_features = []
    for feat in features:
        mpoly = extractPolygons(getShapelyGeometry(feat),True)

        if mpoly:
            selfintersect_polygons = []
            pindex = 0
            for poly in mpoly.geoms:
                selfintersect_rings = []
                index = 0
                for ring in [poly.exterior] + list(poly.interiors):
                    selfintersects = selfintersect_points(ring)
                    if selfintersects:
                        selfintersect_rings.append((index,selfintersects))
                    index += 1
                    
                if selfintersect_rings:
                    selfintersect_polygons.append((pindex,selfintersect_rings))
                pindex += 1

            if selfintersect_polygons:
                selfintersect_features.append((feat,selfintersect_polygons))


    if selfintersect_features:
        for feat,selfintersect_polygons in selfintersect_features:
            print("======================The following feature is self-intersected==============================")
            if properties:
                feat_properties = feat.get("properties") or {}
                for key in properties:
                    print("{}={}".format(key,feat_properties.get(key) ))
            else:
                for key,value in (feat.get("properties") or {}).items():
                    print("{}={}".format(key,value))
            print("")
            for pindex,selfintersect_rings in selfintersect_polygons:
                print("The {} polygon is self-intersected".format(pindex))
                for index,selfintersects in selfintersect_rings:
                    if index == 0:
                        print("  The exterior ring is self-intersected")
                    else:
                        print("  The interior ring({}) is self-intersected".format(index - 1))
                    for coord,indexes in selfintersects:
                        print("    Coordinate({}) is self-intersected at position({})".format(coord,indexes))


    return selfintersect_features
