var env = {
    envType: "prod",
    appType: (window.location.protocol == "file:")?"cordova":"webapp",

    cswService:"https://oim.dpaw.wa.gov.au/catalogue/api/records/",
    catalogueAdminService:"https://oim.dpaw.wa.gov.au",

    wmtsService:"https://kmi.dpaw.wa.gov.au/geoserver/gwc/service/wmts",
    wfsService:"https://kmi.dpaw.wa.gov.au/geoserver/wfs",
    legendSrc:"https://kmi.dpaw.wa.gov.au/geoserver/gwc/service/wms?REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&LAYER=",

    gokartService:"https://sss.dpaw.wa.gov.au",
    resourceTrackingService:"https://resourcetracking.dpaw.wa.gov.au",
    bfrsService:"https://bfrs.dpaw.wa.gov.au",
    staticService:"https://static.dpaw.wa.gov.au",

    s3Service:"http://gokart.dpaw.io/",

    bushfireLayer:"dpaw:bushfire_latest",
    finalFireboundaryLayer:"dpaw:bushfire_final_fireboundary_latest",
    fireboundaryLayer:"dpaw:bushfire_fireboundary_latest",

    allBushfireLayer:"dpaw:bushfire",
    allFireboundaryLayer:"dpaw:bushfire_fireboundary"
};
