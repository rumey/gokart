var env = {
    envType:"uat",
    appType: (window.location.protocol == "file:")?"cordova":"webapp",
    cswService:"https://oim.dpaw.wa.gov.au/catalogue/api/records/",
    wmtsService:"https://kmi.dpaw.wa.gov.au/geoserver/gwc/service/wmts",
    wfsService:"https://kmi.dpaw.wa.gov.au/geoserver/wfs",
    legendSrc:"https://kmi.dpaw.wa.gov.au/geoserver/gwc/service/wms?REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&LAYER=",
    gokartService:"https://sss-uat.dpaw.wa.gov.au",
    oimService:"https://oim.dpaw.wa.gov.au",
    sssService:"https://resourcetracking.dpaw.wa.gov.au",
    bfrsService:"https://bfrs.dpaw.wa.gov.au",
    staticService:"https://static.dpaw.wa.gov.au",
    s3Service:"http://gokart.dpaw.io/"
};
