var env = {
    envType: "prod",
    envVersion:"2007-09-08 14:46",
    appType: (window.location.protocol == "file:")?"cordova":"webapp",

    cswService:"https://oim.dpaw.wa.gov.au/catalogue/api/records/",
    catalogueAdminService:"https://oim.dpaw.wa.gov.au",

    wmtsService:"https://kmi.dpaw.wa.gov.au/geoserver/gwc/service/wmts",
    wmsService:"https://kmi.dpaw.wa.gov.au/geoserver/wms",
    wfsService:"https://kmi.dpaw.wa.gov.au/geoserver/wfs",
    legendSrc:"https://kmi.dpaw.wa.gov.au/geoserver/gwc/service/wms?REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&legend_options=fontName:Times%20New%20Roman;fontAntiAliasing:true;fontSize:14;bgColor:0xFFFFEE;dpi:120;labelMargin:10&LAYER=",

    gokartService:"https://sss.dpaw.wa.gov.au",
    resourceTrackingService:"https://resourcetracking.dpaw.wa.gov.au",
    bfrsService:"https://bfrs.dpaw.wa.gov.au",
    staticService:"https://static.dpaw.wa.gov.au",

    s3Service:"http://gokart.dpaw.io/",

    bushfireListLayer:"dpaw:bushfirelist_latest",

    bushfireLayer:"dpaw:bushfire_latest",
    finalFireboundaryLayer:"dpaw:bushfire_final_fireboundary_latest",
    fireboundaryLayer:"dpaw:bushfire_fireboundary_latest",

    allBushfireLayer:"dpaw:bushfire",
    allFireboundaryLayer:"dpaw:bushfire_fireboundary"
};
