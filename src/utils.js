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

Utils.prototype.checkVersion = function(profile,check) {
    $.ajax({
        url: "/profile/sss/" + profile.distributionType,
        contentType:"application/json",
        success: function (response, stat, xhr) {
            if (profile.build.datetime !== response.build.datetime || 
                profile.build.host !== response.build.host || 
                profile.build.platform !== response.build.platform
            ) {
                alert("New version is available, please press <F5> to reload the system; if can't fix, please clean browser's cache.")
            } else if (profile.build.vendorMD5 !== response.build.vendorMD5) {
                alert("Application was not built on the latest vendor library, please rebuild the application again.")
            } else if (check){
                alert("You have the latest version.")
            }
        },
        error: function (xhr,status,message) {
            alert(status + " : " + message)
        },
        xhrFields: {
            withCredentials: true
        }
    })
}

var utils = new Utils()

export default utils
