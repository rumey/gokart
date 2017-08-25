import sys
import struct
import time
import traceback
from datetime import datetime
from osgeo import ogr, osr, gdal
from affine import Affine

import json
import bottle

from .settings import *

def getBandMetadata(band,name):
    return band.GetMetadata().get(name)

def convertEpochTimeToDatetime(t):
    """
    Convert the epoch time to the datetime with perth timezone
    """
    if t:
        datetimes = t.split()
        if (len(datetimes) == 3 and datetimes[1].lower() == "sec" and datetimes[2].upper() == 'UTC'):
            return datetime.fromtimestamp(long(datetimes[0]),PERTH_TIMEZONE)
        else:
            raise "Invalid epoch time '{}'".format(t)

def getEpochTimeId(band,name):
    return convertEpochTimeToDatetime(getBandMetadata(band,name)).strftime("%Y/%m/%d %H:%M:%S")

def getEpsgSrs(srsid):
    srs = srsid.split(":")
    if len(srs) != 2 or srs[0] != "EPSG":
        raise Exception("Srs '{}' is not a invalid epsg srs".format(srsid))
    result = osr.SpatialReference()
    result.ImportFromEPSG(srs[1])
    return result

def loadDatasource(datasource):
    """
    load the data source
    """
    datasource["status"] = "loading"
    ds = None
    try:
        #print "Begin to load raster datasource: ".format(datasource["datasource"])
        ds = gdal.Open(datasource["datasource"])

        datasource["srs"] = osr.SpatialReference()
        datasource["srs"].ImportFromWkt(ds.GetProjection())

        if datasource.get("bands") is not None:
            datasource["bands"].clear()
        else:
            datasource["bands"] = {}
        index = 1
        while index <= ds.RasterCount:
            band = ds.GetRasterBand(index)
            bandid= datasource["bandid_f"](band,datasource["bandid"])
            datasource["bands"][bandid] = index
            #print "Band {} = {}".format(index,bandid)
            index+=1
        datasource["status"] = "loaded"
        #print "End to load raster datasource: ".format(datasource["datasource"])
    except:
        datasource["status"] = "loadfailed"
        datasource["bands"].clear()
        datasource["message"] = traceback.format_exception_only(sys.exc_type,sys.exc_value)
        traceback.print_exc()
        #print "Failed to load raster datasource: ".format(datasource["datasource"])
        return traceback.format_exception_only(sys.exc_type,sys.exc_value)
    finally:
        ds = None

def loadAllDatasources():
    for workspace in raster_datasources:
        for datasourceId in raster_datasources[workspace]:
            bands = loadDatasource(raster_datasources[workspace][datasourceId])
        

raster_datasources={
    "bom":{
        "IDW71000_WA_T_SFC":{
            "datasource":os.path.join(Setting.getString("bom_home","/var/www/bom_data/adfd"),"IDW71000_WA_T_SFC.grb"),
            "bandid":"GRIB_VALID_TIME",
            "bandid_f":getEpochTimeId
        },
        "IDW71001_WA_Td_SFC":{
            "datasource":os.path.join(Setting.getString("bom_home","/var/www/bom_data/adfd"),"IDW71001_WA_Td_SFC.grb"),
            "bandid":"GRIB_VALID_TIME",
            "bandid_f":getEpochTimeId
        }
    }
}

def getRasterData(options):
    """
    options: a dictionary
        workspace: the workspace
        datasource: the raster datasource
        point: the point whose data will retrieved from datasource bands, optional
        srs: point srs  optional
        pixel: the pxiel whose data will be retireved from datasource bands, optional
        band_indexes: the list of band index,optional
        bandids: the list of band id,optional

    Return dictionary
        status: true if succeed;otherwise false
        message: error message if failed
        datas: data of bands, if succeed
    """

    ds = None
    try:
        if not options.get("workspace"):
            raise Exception("Workspace is missing in the options")
        elif not raster_datasources.get(options["workspace"]):
            raise Exception("Workspace '{}' is not found".format(options["workspace"]))

        if not options.get("datasource"):
            raise Exception("Datasource is missing in the options")
        elif not raster_datasources[options["workspace"]].get(options["datasource"]):
            raise Exception("Datasource '{}:{}' is not found".format(options["workspace"],options["datasource"]))

        if not options.get("bands"):
            raise Exception("Bands is missing in the options")

        if not options.get("pixel") and not options.get("point"):
            raise Exception("Either pixel or point must be present in the options")

        if not options.get("band_indexes") and not options.get("bandids"):
            raise Exception("Either band_indexes or bandids must be present in the options")

        datasource = raster_datasources[options["workspace"]][options["datasource"]]

        runtimes = 1

        while True:
            ds = gdal.Open(datasource["datasource"])
            if datasource.get('status') == 'loaded':
                if ds.RasterCount > 0 and datasource["bands"][1] != datasource["bandid_f"](ds.GetRasterBand(1),datasource["bandid"]):
                    datasource["status"]="outdated"

            #try to reload datasource if required
            while (datasource.get('status') or "loadfailed") != "loaded":
                if (datasource.get('status') or 'loadfailed') in ("loadfailed","outdated"):
                    loadDatasource(datasource)
                    if (datasource.get('status') or 'loadfailed') == "loadfailed":
                        raise Exception(datasource.get("message") or "unknown error.")
                else:
                    #loading by other threads, wait
                    time.sleep(0.1)

            if not options.get("band_indexes"):
                options["band_indexes"] = []
                for bandid in bandids:
                    options["band_indexes"].append(datasource["bands"].get(bandid,-1))

            try:
                if not options.get("pixel"):
                    if options.get("point"):
                        point = ogr.Geometry(ogr.wkbPoint)
                        point.AddPoint(options["point"][0],options["point"][1])
                        point.Transform(osr.CoordinateTransformation(getEpsgSrs(options["srs"]),datasource["srs"]))
                        # Convert geographic co-ordinates to pixel co-ordinates
                        forward_transform = Affine.from_gdal(*ds.GetGeoTransform())
                        reverse_transform = ~forward_transform
                        px, py = reverse_transform * (point.GetX(),point.GetY())
                        #choose the cloest pixel
                        px, py = int(px + 0.5), int(py + 0.5)
                        if px < 0 or px > ds.RasterXSize or py < 0 or py > ds.RasterYSize:
                            options["pixel"] = None
                        else:
                            options["pixel"] = (px,py)

                # Extract pixel value
                datas = []
                for index in options["bands"]:
                    if index < 1 or index > ds.RasterCount:
                        data = None
                    elif not options["pixel"]:
                        data = None
                    else:
                        band = ds.GetRasterBand(index)
                        structval = band.ReadRaster(options["pixel"][0], options["pixel"][1], 1, 1, buf_type=gdal.GDT_Float32)
                        data = struct.unpack('f', structval)[0]
                        if data == band.GetNoDataValue():
                            data = None
                    datas.append(data)
                return {
                    "status":True,
                    "datas":datas
                }
            except:
                #retrieve data failed, maybe be caused by ftp sync process; retrieved it again
                if runTimes == 1:
                    ds = None
                    ds = gdal.Open(datasource["datasource"])
                else:
                    raise
    except:
        traceback.print_exc()
        return {
            "status":False,
            "message":traceback.format_exception_only(sys.exc_type,sys.exc_value)
        }
    finally:
        ds = None

@bottle.route('/raster')
def raster():
    """
    Get data from raster datasources
    Request datas
        point: the coordinate of the point whose data will be retrieved from raster datasources
        srs: the spatial reference system of the coordinate, if missing, epsg:4326 will be used
        datasources:  raster datasources and related options
          {
            workspace: the workspace of the datasource; for example:bom
            {
                datasource : bands(a band identity or a array of band identities; its value dependents on workspace).
            }
          {
    Response: json
        {
            workspace: 
            {
                datasource:  
                {
                    status:true/false
                    message: error message if failed
                    data: a array of data retrieved from band; null represent no value or invalid band. datas has the same length as bands
                }
            }

        }
    """
    try:
        point = bottle.request.forms.get("coordinate")
        point_srs = (bottle.request.forms.get("srs") or "EPSG:4326").strip().upper()
        datasources = bottle.request.forms.get("datasources")
        if point:
            point = json.loads(point)
        else:
            raise Exception("Point, whose corresponding data will be retrieved from raster datasource, is missing.")
    
        if datasources:
            datasources = json.loads(datasources)
            #change the bands to a list if it is not a list(shoule be a string)
            for workspace in datasources:
                for datasource in datasources[workspace]:
                    if datasources[workspace][datasource] and not isinstance(datasources[workspace][datasource],list):
                        datasources[workspace][datasource] = [datasources[workspace][datasource]]
        else:
            raise Exception("Raster datasources is missing.")
        result = {}
        for workspace in datasources:
            result[workspace] = result[workspace] or {}
            for datasource in datasources[workspace]:
                result[workspace][datasource] = getRasterData({
                    "workspace":workspace,
                    "datasource":datasource,
                    "point":point,
                    "srs":point_srs,
                    "bands":datasources[workspace][datasource]
    
                })
    
    
        bottle.response.set_header("Content-Type", "application/json")
        return result
    except:
        bottle.response.status = 400
        bottle.response.set_header("Content-Type","text/plain")
        traceback.print_exc()
        return traceback.format_exception_only(sys.exc_type,sys.exc_value)
        

    
#load all raster datasource first
loadAllDatasources()
