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
from .jinja2settings import settings as jinja2settings

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

def getEpochTime(name,f=None,defaultBand=None):
    """
    Get the meta data whose type is epoch time
    if f is not None, then return formated string; otherwise return date time
    """
    def _func(ds,band=None):
        """
        Get the data from datasource's metadata if both band and defaultBand are None; otherwise get the data from datasource's band
        """
        try:
            if band is not None:
                dt = convertEpochTimeToDatetime(ds.GetRasterBand(band).GetMetadata().get(name))
            elif defaultBand is not None:
                dt = convertEpochTimeToDatetime(ds.GetRasterBand(defaultBand).GetMetadata().get(name))
            else:
                dt = convertEpochTimeToDatetime(ds.GetMetadata().get(name))

            if f is None:
                return dt
            else:
                return dt.strftime(f)
        except:
            return None
    return _func

def getEpsgSrs(srsid):
    srs = srsid.split(":")
    if len(srs) != 2 or srs[0] != "EPSG":
        raise Exception("Srs '{}' is not a invalid epsg srs".format(srsid))
    result = osr.SpatialReference()
    result.ImportFromEPSG(int(srs[1]))
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
            del datasource["bands"][:]
        else:
            datasource["bands"] = []
        index = 1
        while index <= ds.RasterCount:
            bandid= datasource["bandid_f"](ds,index)
            datasource["bands"].append((index,bandid))
            #print "Band {} = {}".format(index,bandid)
            index+=1
        datasource["refresh_time"] = datasource["refresh_time_f"](ds)
        datasource["status"] = "loaded"
        #print "End to load raster datasource: ".format(datasource["datasource"])
    except:
        datasource["status"] = "loadfailed"
        datasource["refresh_time"] = None
        del datasource["bands"][:]
        datasource["message"] = traceback.format_exception_only(sys.exc_type,sys.exc_value)
        traceback.print_exc()
    finally:
        ds = None

def loadAllDatasources():
    for workspace in raster_datasources:
        for datasourceId in raster_datasources[workspace]:
            loadDatasource(raster_datasources[workspace][datasourceId])
        
"""
match_strategy: the way to match a user specified value to a band
    equal: The band is matched if bandid is equal with the value
    floor: The band is matched if bandid is equal with the value; if no bandid is equal with the value, then find a band whose bandid is cloest and less than specified value 
    ceiling: The band is matched if bandid is equal with the value; if no bandid is equal with the value, then find a band whose bandid is cloest and large than specified value 
"""
raster_datasources={
    "bom":{
        "IDW71000_WA_T_SFC":{
            "datasource":os.path.join(Setting.getString("BOM_HOME","/var/www/bom_data"),"adfd","IDW71000_WA_T_SFC.grb"),
            "bandid_f":getEpochTime("GRIB_VALID_TIME"),
            "match_strategy":"floor",
            'refresh_time_f':getEpochTime("GRIB_VALID_TIME",None,1)
        },
        "IDW71001_WA_Td_SFC":{
            "datasource":os.path.join(Setting.getString("BOM_HOME","/var/www/bom_data"),"adfd","IDW71001_WA_Td_SFC.grb"),
            "bandid_f":getEpochTime("GRIB_VALID_TIME"),
            "match_strategy":"floor",
            'refresh_time_f':getEpochTime("GRIB_VALID_TIME",None,1)
        },
        "IDW71002_WA_MaxT_SFC":{
            "datasource":os.path.join(Setting.getString("BOM_HOME","/var/www/bom_data"),"adfd","IDW71002_WA_MaxT_SFC.grb"),
            "bandid_f":getEpochTime("GRIB_VALID_TIME"),
            "match_strategy":"floor",
            'refresh_time_f':getEpochTime("GRIB_VALID_TIME",None,1)
        },
        "IDW71003_WA_MinT_SFC":{
            "datasource":os.path.join(Setting.getString("BOM_HOME","/var/www/bom_data"),"adfd","IDW71003_WA_MinT_SFC.grb"),
            "bandid_f":getEpochTime("GRIB_VALID_TIME"),
            "match_strategy":"equal",
            'refresh_time_f':getEpochTime("GRIB_VALID_TIME",None,1)
        }

    }
}

def getRasterData(options):
    """
    options: a dictionary
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
        if not options.get("datasource"):
            raise Exception("Datasource is missing in the options")

        if not raster_datasources.get(options["datasource"]["workspace"]):
            raise Exception("Workspace '{}' is not found".format(options["datasource"]["workspace"]))

        if not raster_datasources[options["datasource"]["workspace"]].get(options["datasource"]["id"]):
            raise Exception("Datasource '{}:{}' is not found".format(options["datasource"]["workspace"],options["datasource"]["id"]))

        if not options.get("pixel") and not options.get("point"):
            raise Exception("Either pixel or point must be present in the options")

        if not options.get("band_indexes") and not options.get("bandids"):
            raise Exception("Either band_indexes or bandids must be present in the options")

        datasource = raster_datasources[options["datasource"]["workspace"]][options["datasource"]["id"]]

        options["datasource"]["refresh_time"] = None
        runtimes = 0
        #import ipdb;ipdb.set_trace()
        while True:
            runtimes += 1
            ds = gdal.Open(datasource["datasource"])
            if datasource.get('status') == 'loaded':
                if ds.RasterCount > 0 and datasource["bandid_f"](ds,1)  != datasource["bands"][1][1]:
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
                for inputBandid in options["bandids"]:
                    matchedBand = -1
                    for band in datasource["bands"]:
                        if band[1] == inputBandid:
                            matchedBand = band[0]
                            break
                        elif inputBandid < band[1] and datasource["match_strategy"] != "equal":
                            if datasource["match_strategy"] == "floor":
                                if band[0] >= 2:
                                    matchedBand = band[0] - 1
                                else:
                                    matchedBand = -1
                            elif datasource["match_strategy"] == "ceiling":
                                matchedBand = band[0]
                            else:
                                matchedBand = -1
                            break
                    options["band_indexes"].append(matchedBand)


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
                for index in options["band_indexes"]:
                    if index < 1 or index > ds.RasterCount:
                        data = None
                    elif not options["pixel"]:
                        data = None
                    else:
                        band = ds.GetRasterBand(index)
                        structval = band.ReadRaster(options["pixel"][0], options["pixel"][1], 1, 1, buf_type=gdal.GDT_Float32)
                        if structval:
                            data = struct.unpack('f', structval)[0]
                            if data == band.GetNoDataValue():
                                data = None
                        else:
                            data = None
                    datas.append(data)
                #import ipdb;ipdb.set_trace()
                options["datasource"]["status"] = True
                options["datasource"]["refresh_time"] = datasource["refresh_time"]
                options["datasource"]["data"] = datas
                return options["datasource"]
            except:
                #retrieve data failed, maybe be caused by ftp sync process; retrieved it again
                if runtimes == 1:
                    ds = None
                    ds = gdal.Open(datasource["datasource"])
                else:
                    raise
    except:
        traceback.print_exc()
        options["datasource"]["status"] = False
        options["datasource"]["message"] = traceback.format_exception_only(sys.exc_type,sys.exc_value)
        return options["datasource"]
    finally:
        ds = None

@bottle.route('/spotforecast/<fmt>',method="POST")
def spotforecast(fmt):
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
    Response: json or html
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
    fmt = (fmt or "json").lower()
    try:
        requestData = bottle.request.forms.get("data")
        if requestData:
            requestData = json.loads(requestData)
        else:
            requestData = {}

        requestData["srs"] = (requestData.get("srs") or "EPSG:4326").strip().upper()

        if not requestData.get("forecasts"):
            raise Exception("Parameter 'forecasts' is missing")

        if not requestData.get("point"):
            raise Exception("Parameter 'point' is missing.")

        for forecast in requestData["forecasts"]:
            if not forecast.get("times"):
                raise Exception("Property 'times' within forecast is missing.")
            elif not isinstance(forecast["times"],list):
                forecast["times"] = [forecast["times"]]
            forecast["times"] = [datetime.strptime(dt,"%Y-%m-%d %H:%M:%S").replace(tzinfo=PERTH_TIMEZONE)  for dt in forecast["times"]]

            if forecast.get("datasources"):
                #change the bands to a list if it is not a list(shoule be a string)
                for datasource in forecast["datasources"]:
                    if datasource.get("group"):
                        if not datasource.get("datasources"):
                            raise Exception("Property 'datasources' within datasource group is missing.")
                        for ds in datasource["datasources"]:
                            if not ds.get("workspace"):
                                raise Exception("Property 'workspace' within datasource is missing.")
                            if not ds.get("id"):
                                raise Exception("Property 'id' within datasource is missing.")
                    else:
                        if not datasource.get("workspace"):
                            raise Exception("Property 'workspace' within datasource is missing.")
                        if not datasource.get("id"):
                            raise Exception("Property 'id' within datasource is missing.")
            else:
                raise Exception("Property 'datasources' within forecast is missing.")


        for forecast in requestData["forecasts"]:
            for datasource in forecast["datasources"]:
                if datasource.get("group"):
                    for ds in datasource["datasources"]:
                        ds.update(getRasterData({
                            "datasource":ds,
                            "point":requestData["point"],
                            "srs":requestData["srs"],
                            "bandids":forecast["times"]
                        }))
                else:
                    datasource.update(getRasterData({
                        "datasource":datasource,
                        "point":requestData["point"],
                        "srs":requestData["srs"],
                        "bandids":forecast["times"]
                    }))
    
        result = requestData

        if fmt == "json":
            bottle.response.set_header("Content-Type", "application/json")
            return result
        else:
            #html
            for forecast in result["forecasts"]:
                forecast["has_group"] = False
                forecast["columns"] = 0
                for datasource in forecast["datasources"]:
                    if datasource.get("group"):
                        forecast["has_group"] = True
                        datasource["columns"] = 0
                        for ds in datasource["datasources"]:
                            forecast["columns"] += 1
                            datasource["columns"] += 1
			    ds["title"] = ds.get("title") or ds["id"]
                    else:
                        forecast["columns"] += 1
			datasource["title"] = datasource.get("title") or datasource["id"]
            bottle.response.set_header("Content-Type", "text/html")
            return bottle.template('spotforecast.html',template_adapter=bottle.Jinja2Template,template_settings=jinja2settings, staticService=STATIC_SERVICE,data=result)

    except:
        bottle.response.status = 400
        bottle.response.set_header("Content-Type","text/plain")
        traceback.print_exc()
        return traceback.format_exception_only(sys.exc_type,sys.exc_value)
        

    
#load all raster datasource first
loadAllDatasources()
