var env = {
    envType:"dev",
    appType: (window.location.protocol == "file:")?"cordova":"webapp",

    cswService:"https://oim.dpaw.wa.gov.au/catalogue/api/records/",
    catalogueAdminService:"https://oim.dpaw.wa.gov.au",
    ssoService:"https://oim.dpaw.wa.gov.au",

    wmtsService:"https://kmi.dpaw.wa.gov.au/geoserver/gwc/service/wmts",
    wmsService:"https://kmi.dpaw.wa.gov.au/geoserver/wms",
    wfsService:"https://kmi.dpaw.wa.gov.au/geoserver/wfs",
    legendSrc:"https://kmi.dpaw.wa.gov.au/geoserver/gwc/service/wms?REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&LAYER=",

    gokartService:"https://sss-dev.dpaw.wa.gov.au",
    resourceTrackingService:"https://resourcetracking-uat.dpaw.wa.gov.au",
    bfrsService:"https://bfrs-dev.dpaw.wa.gov.au",
    staticService:"https://static.dpaw.wa.gov.au",

    s3Service:"http://gokart.dpaw.io/",

    bfrsLayer:"dpaw:bushfire_dev",
    bfrsWMSLayer:"dpaw:bushfire_final_fireboundary_dev"

};

document.body.onload = function() {
    var setStyle = function (){
        var leftPanel = document.getElementById("offCanvasLeft");
        if (leftPanel) {
            leftPanel.style = "background-image:url('dist/static/images/dev.svg');background-size:cover;background-repeat:no-repeat;background-position:center center;"
        } else {
            setTimeout(setStyle,500)
        }
    }
    setTimeout(setStyle,500)
}
