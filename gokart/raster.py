import sys
import struct
from osgeo import ogr, osr, gdal
from affine import Affine

import json
import bottle

from .settings import *

def convertToPixel(data_source,point):
    """
    Convert the coordinate of the point to pixel in the raster data source
    data_source: the raster data source
    point: the coordinate of the point
    """
    point_sr = point.GetSpatialReference()
    raster_sr = osr.SpatialReference()
    raster_sr.ImportFromWkt(data_source.GetProjection())
    transform = osr.CoordinateTransformation(point_sr, raster_sr)
    point.Transform(transform)

    # Convert geographic co-ordinates to pixel co-ordinates
    x, y = point.GetX(), point.GetY()
    forward_transform = Affine.from_gdal(*data_source.GetGeoTransform())
    reverse_transform = ~forward_transform
    px, py = reverse_transform * (x, y)
    #choose the cloest pixel
    px, py = int(px + 0.5), int(py + 0.5)

    return (px,py)

def getRasterData(data_source,pixel, bands=[1]):
    """
    Return floating-point value  of given point and band list
    data_source: the raster data source
    pixel: the pixel of the point
    bands: the band list whose value will be returned
    """

    # Extract pixel value
    results = []
    for band_index in bands:
        band = data_source.GetRasterBand(band_index)
        structval = band.ReadRaster(pixel[0], pixel[1], 1, 1, buf_type=gdal.GDT_Float32)
        result = struct.unpack('f', structval)[0]
        if result == band.GetNoDataValue():
            result = float('nan')
        results.append(result)
    return results

raster_layers={
    "bom":{
    }
}

@bottle.route('/raster')
def raster():
    """
    Get data from raster layers
    Request datas
        coordinate: the coordinate of the point whose data will be retrieved from raster layers
        srs: the spatial reference system of the coordinate
        layers: a list of raster layers and related options
          [
            {
            workspace: the workspace of the layer; for example:bom
            layer: layer identity
            bands: a band identity or a array of band identities; its value dependents on workspace.
            }
          ]
    Response: json
        {
            workspace: 
            {
                layer:  
                {
                    bands: a band identity or a array of band identities; its value dependents on workspace.
                    datas: a array of data retrieved from band; null represent no value or invalid band. datas has the same length as bands
                }
            }

        }
    """
    pass

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print "Missing parameters: data_source (1(pixel) | 2(coordinate)) x y band band band"
    else:
        data_source = gdal.Open(sys.argv[1])
        srs4326 = osr.SpatialReference()
        srs4326.ImportFromEPSG(4326)
        isPixel = int(sys.argv[2]) == 1
        pixel = None
        if isPixel:
            pixel = (int(sys.argv[3]),int(sys.argv[4]))
            pixel = (
                0 if pixel[0] < 0 else (data_source.RasterXSize if pixel[0] > data_source.RasterXSize else pixel[0]),
                0 if pixel[1] < 0 else (data_source.RasterYSize if pixel[1] > data_source.RasterYSize else pixel[1])
            )
        else:
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint(float(sys.argv[3]),float(sys.argv[4]))
            point.Transform(osr.CoordinateTransformation(srs4326,srs4326))
            pixel = convertToPixel(data_source,point)
        bands = [1] if len(sys.argv) < 6 else [int(sys.argv[i]) for i in range(5,len(sys.argv)) if int(sys.argv[i]) < data_source.RasterCount and int(sys.argv[i]) > 0]
        value = getRasterData(data_source,pixel,bands)
        print value
