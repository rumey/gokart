var env = {
    envType: "prod",
    appType: (window.location.protocol == "file:")?"cordova":"webapp",

    cswService:"https://oim.dpaw.wa.gov.au/catalogue/api/records/",
    catalogueAdminService:"https://oim.dpaw.wa.gov.au",
    ssoService:"https://oim.dpaw.wa.gov.au",

    wmtsService:"https://kmi.dpaw.wa.gov.au/geoserver/gwc/service/wmts",
    wfsService:"https://kmi.dpaw.wa.gov.au/geoserver/wfs",
    legendSrc:"https://kmi.dpaw.wa.gov.au/geoserver/gwc/service/wms?REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&LAYER=",

    gokartService:"https://sss.dpaw.wa.gov.au",
    resourceTrackingService:"https://resourcetracking.dpaw.wa.gov.au",
    bfrsService:"https://bfrs.dpaw.wa.gov.au",
    staticService:"https://static.dpaw.wa.gov.au",

    s3Service:"http://gokart.dpaw.io/",

    bfrsLayer:"dpaw:bushfire"
};
