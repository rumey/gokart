import { $ } from 'src/vendor.js'


let Utils = function() {
}

Utils.prototype.checkPermission = function(url,callback) {
    var pos = url.indexOf('?')
    if  (pos >= 0) {
        if (pos === url.length - 1) {
            url = url + "checkpermission=true"
        } else {
            url = url + "&checkpermission=true"
        }
    } else {
        url = url + "?checkpermission=true"
    }
    $.ajax(url ,{
        xhrFields:{
            withCredentials: true
        },
        success:function(data,status,jqXHR) {
            callback(true)
        },
        error:function(jqXHR) {
            if (jqXHR.status === 401) {
                callback(false)
            } else if(jqXHR.status >= 500) {
                callback(false)
            } else {
                callback(true)
            }
        }
        
    })
}

Utils.prototype.editResource = function(event) {
    var target = (event.target.nodeName == "A")?event.target:event.target.parentNode;
    if (env.appType == "cordova") {
        window.open(target.href,"_system");
    } else {
        window.open(target.href,target.target);
    }
}

Utils.prototype.getAddressTarget = function(target){
    return (env.appType === "cordova")?"_system":target
}

var utils = new Utils()

export default utils
