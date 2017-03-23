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

var proxyCache = {}
Utils.prototype.proxy = function(classname,object,attrs){
    if (!object) {return null;}
    if (!(classname in proxyCache)) {
        var properties = []
        var methods = []
        var ProxyClass = null
        for (var key in object) {
            if (key[0] === "_") {
                continue
            } else if (typeof object[key] !== 'function') {
                properties.push(key)
            } else if (object.hasOwnProperty(key)){
                methods.push(key)
            }
        }
        var key = null
        if (properties.length > 0 || methods.length > 0) {
            ProxyClass = function(object) {
                this._object = object
                this._objectPrototype = Object.getPrototypeOf(this._object)
                for(var i = 0;i < properties.length;i++) {
                    key = properties[i]
                    console.log("create property " + key)
                    eval("Object.defineProperty(this,\"" + key + "\",{ \
                        get:function(){return this._object[\"" + key + "\"]}, \
                        set:function(value){this._object[\"" + key + "\"] = value}, \
                    })")
                }
            }
        } else {
            ProxyClass  = function(object) {
            }
        }
        //proxy all the method
        ProxyClass.prototype = Object.create(Object.getPrototypeOf(object))
        ProxyClass.prototype.constructor = ProxyClass
        ProxyClass.prototype.getWrappedObject = function() {
            return this._object
        }
        for (var key in Object.getPrototypeOf(object)) {
            if (["constructor"].indexOf(key) < 0 && (!attrs || !(key in attrs))) {
                console.log("Create prototype method " + key)
                eval("ProxyClass.prototype[\"" + key + "\"] = function() { \
                    console.log(\"Invoke prototype method " + key + "\"); \
                    return this._objectPrototype[\"" + key + "\"].apply(this._object,arguments); \
                }")
            }
        }

        for(var i = 0;i < methods.length;i++) {
            key = methods[i]
            console.log("create function " + key)
            eval("ProxyClass.prototype[\"" + key + "\"] = function() { \
                console.log(\"Invoke instance method " + key + "\"); \
                return this._object[\"" + key + "\"]?this._object[\"" + key + "\"].apply(this._object,arguments) : undefined; \
            }")
        }

        for (var key in attrs) {
            eval("ProxyClass.prototype[\"" + key + "\"] = function() { \
                console.log(\"Invoke override method " + key + "\"); \
                return attrs[\"" + key + "\"].apply(this._object,arguments); \
            }")
        }

        ProxyClass.prototype.constructor = ProxyClass
        proxyCache[classname] = ProxyClass
    }
    return new proxyCache[classname](object)

}

var utils = new Utils()

export default utils
