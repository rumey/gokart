import json
import os
import tempfile

from shapely.geometry import shape,MultiPoint,Point
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry import LinearRing,mapping
from shapely.geometry.collection import GeometryCollection

from gokart.spatial import calculateFeatureArea,calculateGeometryArea,extractPolygons

def getShapelyGeometry(feature):
    if feature["geometry"]["type"] == "GeometryCollection":
        return GeometryCollection([shape(g) for g in feature["geometry"]["geometries"]])
    else:
        return shape(feature["geometry"])

def exportGeojson(geom,fname):
    geojson = {
        "type":"FeatureCollection",
        "features":[
            {
                "type":"Feature",
                "geometry":mapping(geom),
                "properties":{
                    "toolName":"Fire Boundary",
                    "author":"rocky.chen@dbca.wa.gov.au",
                    "createTime":1558314708105
                }
            }
        ]
    }
    with open(fname,'w') as f:
        f.write(json.dumps(geojson,indent=True))

    return fname

#return polygon or multipolygons if have, otherwise return None
class PolygonUtil(object):
    def __init__(self,geom,parentPath=None):
        self.geom = geom
        self.parentPath = parentPath

    def _nextGeomPath(self):
        curPos = self.pos
        self.pos += 1
        if self.parentPath:
            return "{}.{}".format(self.parentPath,curPos)
        else:
            return str(curPos)

    @property
    def polygons(self):
        if not hasattr(self,"_polygons"):
            self.pos = 0
            if isinstance(self.geom,Polygon):
                self._polygons = [(self._nextGeomPath(),self.geom)]
            elif isinstance(self.geom,MultiPolygon):
                self._polygons = [(self._nextGeomPath(),geom1) for geom1 in self.geom.geoms]
            elif isinstance(self.geom,GeometryCollection):
                polygonList = None
                for g in self.geom:
                    sublist = PolygonUtil(g,parentPath=self._nextGeomPath()).polygons
                    if not p:
                        continue
                    elif not polygonList:
                        polygonList = sublist
                    else:
                        polygonList += sublist
                self._polygons = polygonList
            else:
                self._polygons = None

        return self._polygons

    def expandGeom(self,geom=None):
        geom = geom or self.geom
        if isinstance(geom,Polygon):
            return ['polygon',self.geom]
        elif isinstance(geom,MultiPolygon):
            return ["multipolygon",[['polygon',g] for g in geom.geoms]]
        elif isinstance(self.geom,GeometryCollection):
            return ['geometrycollection',[self.expandGeom(g) for g in geom]]
        else:
            return ['other',self.geom]

    def addOrphanRing(self,expandedGeom,orphanRings):
        """
        Try to add orphan interior ring into one of the poylgon,
        if this ring is contained by one polygon, then add it to the polygon as interior ring 
        if this ring is not contained by any polygon, then add it as indenpendent polygon
        """
        
        def _addAsInteriorRing(expandedGeom,orphanPoly):
            if expandedGeom[0] == 'polygon':
                if expandedGeom[1].contains(orphanPoly):
                    expandedGeom[1] = Polygon(expandedGeom[1].exterior,[r for r in expandedGeom[1].interiors] + [LinearRing([c for c in reversed(orphanPoly.exterior.coords)])])
                    return True
                else:
                    return False
            elif expandedGeom[0] == 'other':
                return False
            elif expandedGeom[0] == 'multipolygon':
                for g in expandedGeom[1]:
                    if _addAsInteriorRing(g,orphanPoly):
                        return True
                return False
            elif expandedGeom[0] == 'geometrycollection':
                for g in expandedGeom[1]:
                    if _addAsInteriorRing(g,orphanPoly):
                        return True
                return False
            else:
                return False
        index = len(orphanRings) - 1
        while index >= 0:
            orphanRing = LinearRing(orphanRings[index])
            if orphanRing.is_ccw:
                orphanPoly = Polygon(LinearRing(reversed(orphanRing.coords)))
            else:
                orphanPoly = Polygon(orphanRing)
            if _addAsInteriorRing(expandedGeom,orphanPoly):
                del orphanRings[index]
            index -= 1

        if orphanRings:
            print("Still have some orphan rings are not contained by polygon, added them as independent polygons")
            if expandedGeom[0] == 'polygon':
                expandedGeom = ["multipolygon",[expandedGeom]]
                for orphanRing in orphanRings:
                    orphanRing = LinearRing(orphanRing)
                    if orphanRing.is_ccw:
                        orphanPoly = Polygon(LinearRing(reversed(orphanRing.coords)))
                    else:
                        orphanPoly = Polygon(orphanRing)
                    expandedGeom[1].append(['polygon',orphanPoly])
            elif expandedGeom[0] in ("multipolygon","geometrycollection"):
                for orphanRing in orphanRings:
                    orphanRing = LinearRing(orphanRing)
                    if orphanRing.is_ccw:
                        orphanPoly = Polygon(LinearRing(reversed(orphanRing.coords)))
                    else:
                        orphanPoly = Polygon(orphanRing)
                    expandedGeom[1].append(['polygon',orphanPoly])
            else:
                raise Exception("Doesn't support expanded geometry type ({})".format("expandedGeom[0]"))

    def collapseGeom(self,expandedGeom):
        if expandedGeom[0] == 'polygon':
            return expandedGeom[1]
        elif expandedGeom[0] == 'other':
            return expandedGeom[1]
        elif expandedGeom[0] == 'multipolygon':
            return MultiPolygon([self.collapseGeom(g) for g in expandedGeom[1]]) 
        elif expandedGeom[0] == 'geometrycollection':
            return GeometryCollection([self.collapseGeom(g) for g in expandedGeom[1]]) 
        else:
            raise Exception("Unsupported geometry type {}".format(expandedGeom[0]))
            
    def first_selfintersect_point(self,ring_coords):
        """
        return the first selfintersect point
        """
        index = 0
        coord_map = {}
        for coord in ring_coords:
            if coord in coord_map:
                if index not in [0,len(ring_coords) - 1]:
                    return (coord,coord_map[coord],index)
            else:
                coord_map[coord] = index
            index += 1
    
        return None


    def selfintersect_points(self,ring):
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
        duplicate_coords.sort(key=lambda coord:coord_map[coord][0])
    
        for coord in duplicate_coords:
            if any([i for i in coord_map[coord] if i != 0 and  i != len(ring.coords) - 1]):
                result.append((coord,coord_map[coord]))
    
        return result

    def check_selfintersect(self):
        polygonList = self.polygons
    
        if not polygonList:
            return None

        selfintersect_polygons = []
        for path,poly in polygonList:
            selfintersect_rings = []
            index = 0
            for ring in [poly.exterior] + list(poly.interiors):
                selfintersects = self.selfintersect_points(ring)
                if selfintersects:
                    selfintersect_rings.append((index,selfintersects))
                index += 1
                    
            if selfintersect_rings:
                selfintersect_polygons.append((path,selfintersect_rings))

        return selfintersect_polygons

    def fix_selfintersect(self):
        polygonList = self.polygons

        expandedGeom = self.expandGeom()

        fixed_geom = False
        fixed_polygons = []
        orphan_rings = []
        for path,polygon in reversed(polygonList):
            fixed_polygons = []

            #feat polygon is self-intersected
            exterior_rings = []
            interior_rings = []
            #import ipdb;ipdb.set_trace()
            all_rings = []
            fixed = False
            if polygon.exterior.is_ccw:
                all_rings.append([(exterior_rings,0,LinearRing(reversed(polygon.exterior.coords)))])
                fixed = True
            else:
                all_rings.append((exterior_rings,0,polygon.exterior))

            i = 1
            exterior_polygon = Polygon(all_rings[0][2])
            for r in polygon.interiors:
                polygon_r = Polygon(r)
                if exterior_polygon.contains(polygon_r):
                    if r.is_ccw:
                        all_rings.append((interior_rings,i,r))
                    else:
                        all_rings.append((interior_rings,i,LinearRing(reversed(r.coords))))
                        fixed = True
                elif extractPolygons(exterior_polygon).intersection(polygon_r):
                    raise Exception("The exterior ring of the polygon({}) is intersected with interior ring".format(path))
                else:
                    fixed = True
                    print("==============================")
                    print(mapping(r))
                    print("==============================")
                    if r.is_ccw:
                        all_rings.append((orphan_rings,i,r))
                    else:
                        all_rings.append((orphan_rings,i,LinearRing(reversed(r.coords))))

                i += 1

            polygon = Polygon(LinearRing(all_rings[0][2]),[LinearRing(r[2]) for r in all_rings[1:]])

            while all_rings:
                rings,ring_index,ring = all_rings[0]
                del all_rings[0]


                check_rings = [ring.coords]

                #if path == '150' and ring_index < 10:
                #    import ipdb;ipdb.set_trace()


                while check_rings:
                    check_ring = check_rings[0]
                    del check_rings[0]

                    first_selfintersect_point = self.first_selfintersect_point(check_ring)
                    if not first_selfintersect_point:
                        rings.append(check_ring)
                        continue
                    fixed = True

                    coord,start_pos,end_pos  = first_selfintersect_point

                    """
                    if ring_index == 0:
                        print("Split the exterior ring of the polygon({}) as {} :coord = {}, start_pos = {}, end_pos = {}".format(path,"exterior ring" if exterior else "interior ring",coord,start_pos,end_pos))
                    else:
                        print("Split the interior({}) ring of the polygon({}) as {} :coord = {}, start_pos = {}, end_pos = {}".format(ring_index - 1,path,"exterior ring" if exterior else "interior ring",coord,start_pos,end_pos))
                    """
                    if start_pos == 0:
                        #fist point is self intersected, split into two polygons
                        ring1 = check_ring[:end_pos + 1 ]
                        ring2 = check_ring[end_pos:]
                    else:
                        #middle point is self intersected, split into two polygons
                        ring1 = check_ring[0:start_pos] + check_ring[end_pos:]
                        ring2 = check_ring[start_pos:end_pos + 1 ]

                    for r in (ring1,ring2):
                        if len(r) < 4:
                            if ring_index == 0:
                                raise Exception("Fix the exterior ring of the polygon({}) failed, the splitted ring only has {} pints ".format(path, len(r)))
                            else:
                                raise Exception("Fix the interior ring ({}) of the polygon({}) failed, the splitted ring only has {} pints ".format(ring_index - 1,path, len(r)))

                        if r[0] != r[-1]:
                            if ring_index == 0:
                                raise Exception("Fix the exterior ring of the polygon({}) failed, the fist point of the splitted ring is not the same point as the last point.({} <> {}) ".format(path, r[0], r[-1] ))
                            else:
                                raise Exception("Fix the interior ring ({}) of the polygon({}) failed, the fist point of the splitted ring is not the same point as the last point.({} <> {}) ".format(ring_index - 1,path, r[0],r[-1] ))

                    if Polygon(ring1).contains(Polygon(ring2)):
                        #ring2 inside ring1,treat  ring2 as a hole
                        check_rings.insert(0,ring1)
                        if rings == exterior_rings:
                            all_rings.insert(0,(interior_rings,ring_index,LinearRing(ring2)))
                        elif rings == interior_rings:
                            #this is a island, generate replace the same point with two adjecent points.
                            all_rings.insert(0,(exterior_rings,ring_index,LinearRing(ring2)))
                        else:
                            raise Exception("Doesn't support orphan ring island")

                        continue
                    elif Polygon(ring2).contains(Polygon(ring1)):
                        #ring1 inside ring2,treat  ring1 as a hole
                        check_rings.insert(0,ring2)
                        if ring_index == 0:
                            all_rings.insert(0,LinearRing(ring1))
                        else:
                            #this is a island, generate replace the same point with two adjecent points.
                            all_rings.insert(0,(not exterior,ring_index,LinearRing(ring1)))
                        continue
                    else:
                        check_rings.insert(0,ring1)
                        check_rings.insert(1,ring2)
                        #import ipdb;ipdb.set_trace()
                        for i in (0,1):
                            container_index = 1 if i == 0 else 0
                            container_polygon = Polygon(LinearRing(check_rings[container_index]))
                            for ring_coord in check_rings[i]:
                                if coord == ring_coord:
                                    continue
                                if container_polygon.contains(Point(ring_coord)):
                                    if ring_index == 0:
                                        raise Exception("Fix the exterior ring of the polygon({}) failed, the point({}) of splitted ring is inside the other splitted ring ".format(path, ring_coord ))
                                    else:
                                        raise Exception("Fix the interior ring({}) of the polygon({}) failed, the point({}) of splitted ring is inside the other splitted ring ".format(ring_index - 1,path, ring_coord ))

            if not fixed :
                exportGeojson(polygon,"/tmp/bf_2017_ekm_024_{}.geojson".format(path))
                continue
            #import ipdb;ipdb.set_trace()
            fixed_geom = True
            if interior_rings:
                for exterior_ring_coords in exterior_rings:
                    exterior_ring = Polygon(LinearRing(exterior_ring_coords))
                    interior_index = len(interior_rings) - 1
                    interior_rings_coords = []
                    while interior_index >= 0:
                        interior_ring = Polygon(LinearRing(interior_rings[interior_index]))
                        if exterior_ring.contains(interior_ring):
                            interior_rings_coords.append(interior_rings[interior_index])
                            del interior_rings[interior_index]
                        interior_index -= 1

                    if interior_rings_coords:
                        fixed_polygons.append(Polygon(exterior_ring_coords,interior_rings_coords))
                    else:
                        fixed_polygons.append(Polygon(exterior_ring_coords))

                if interior_rings:
                    import ipdb;ipdb.set_trace()
                    raise Exception("Some interior rings are not in polygon.")
            else:
                for exterior_ring_coords in exterior_rings:
                    fixed_polygons.append(Polygon(exterior_ring_coords))

            #import ipdb;ipdb.set_trace()
            polygon_area = calculateGeometryArea(polygon)
            fixed_polygon_area = calculateGeometryArea(MultiPolygon(fixed_polygons))
            print("Original polygon area = {}, fixed polygon area = {}".format(polygon_area,fixed_polygon_area))
            #replace the selfintersected polygon in the expanded geom
            exportGeojson(MultiPolygon(fixed_polygons),"/tmp/bf_2017_ekm_024_{}.geojson".format(path))
            paths = [int(i) for i in path.split(".")]
            parentGeom = expandedGeom
            for p in paths[0:-1]:
                if parentGeom[0] not in ('multipolygon','geometrycollection'):
                    raise Exception("container geometry is not multipolygon and geometrycollection")
                parentGeom = parentGeom[1][p]

            if paths[-1] == 0:
                if parentGeom[0] == 'polygon':
                    parentGeom[0] = 'multipolygon'
                    parentGeom[1] = [["polygon",p] for p  in fixed_polygons]
                elif parentGeom[0] == 'other':
                    raise Exception("Replaced geometry type is 'other', can't be replaced by a polygon")
                else:
                    del parentGeom[1][paths[-1]]
                    for poly in reversed(fixed_polygons):
                        parentGeom[1].insert(paths[-1],['polygon',poly])
            else:
                del parentGeom[1][paths[-1]]
                for poly in reversed(fixed_polygons):
                    parentGeom[1].insert(paths[-1],['polygon',poly])


        if fixed_geom:
            #import ipdb;ipdb.set_trace()
            if orphan_rings:
                self.addOrphanRing(expandedGeom,orphan_rings)

                
            fixed_geom = self.collapseGeom(expandedGeom)
            return fixed_geom
        else:
            return None


def check_selfintersect(geojsonfile,properties=None):
    with open(geojsonfile) as f:
        geojson = json.loads(f.read())

    return _check_selfintersect(geojson)

def _check_selfintersect(geojsonFeatures,properties=None):
    features = geojsonFeatures["features"]

    selfintersect_features = []
    for feat in features:
        selfintersect_polygons = PolygonUtil(getShapelyGeometry(feat)).check_selfintersect()

        if selfintersect_polygons:
            selfintersect_features.append((feat,selfintersect_polygons))


    return selfintersect_features

def print_selfintersect_features(selfintersect_features,properties=None):
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
            for path,selfintersect_rings in selfintersect_polygons:
                print("The {} polygon is self-intersected".format(path))
                for index,selfintersects in selfintersect_rings:
                    if index == 0:
                        print("  The exterior ring is self-intersected")
                    else:
                        print("  The interior ring({}) is self-intersected".format(index - 1))
                    for coord,indexes in selfintersects:
                        print("    Coordinate({}) is self-intersected at position({})".format(coord,indexes))


def replace_geojson_geometry(feat_geom,geom):
    feat_geom.update(mapping(geom))


def fix_selfintersect(geojson):
    """
    if geojson can be a geojson file or geojson string
    if some the polygon fetures in this geosjon string or geojson file are selfintersected, a new file or geojson string  will be created to contain the fixed features and the other features and return the caller; 

    otherwise , return the same geojson file or geojson string.
    """
    isfile = None
    originFile = None
    openNewFile = None

    if geojson[-8:].lower() == ".geojson":
        openNewFile = lambda originFile:tempfile.NamedTemporaryFile(prefix="{}_fixed_".format(os.path.split(originFile)[1][:-8]),suffix=".geojson")

        with open(geojson) as f:
            geojsonFeatures = json.loads(f.read())
        isFile = True
    else:
        geojsonFeatures = json.loads(geojson)
        isFile = False

    features = geojsonFeatures["features"]
    index = 0
    selfintersect_index = 0
    changed = False
    #import ipdb;ipdb.set_trace()
    while index < len(features):
        feat = features[index]
        index += 1

        featureArea = calculateFeatureArea(feat)

        geom = getShapelyGeometry(feat)
        fixed_geom = PolygonUtil(geom).fix_selfintersect()
        if not fixed_geom:
            continue

        changed = True
        replace_geojson_geometry(feat["geometry"],fixed_geom)
        fixedFeatureArea = calculateFeatureArea(feat)
        print("feature area = {},fixed feature area = {}".format(featureArea,fixedFeatureArea))

    if not changed:
        return geojson

    if isFile:
        with tempfile.NamedTemporaryFile(prefix="{}_fixed_".format(os.path.split(geojson)[1][:-8]),suffix=".geojson",delete=False) as fixedFile:
            fixedFile.write(json.dumps(geojsonFeatures,indent=True))
            return fixedFile.name
    else:
        return features



            


selfintersected_features = check_selfintersect("/home/rockyc/work/gokart/tmp/bf_2017_ekm_024.geojson")
print_selfintersect_features(selfintersected_features)

fixed_file = fix_selfintersect("/home/rockyc/work/gokart/tmp/bf_2017_ekm_024.geojson")
print(fixed_file)

selfintersected_features = check_selfintersect(fixed_file)
print_selfintersect_features(selfintersected_features)

#selfintersected_features = check_selfintersect("/home/rockyc/work/gokart/tmp/BF_2017_EKM_024.geojson")
#print_selfintersect_features(selfintersected_features)

#selfintersected_features = check_selfintersect("/home/rockyc/work/gokart/tmp/BF_2017_EKM_024_EPSG_4326.geojson")
#print_selfintersect_features(selfintersected_features)
