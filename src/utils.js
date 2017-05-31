import { $ } from 'src/vendor.js'


let FeatureTask = function(manager,scope,taskId,description,status,message) {
    this.manager = manager
    this.scope = scope
    this.taskId = taskId
    this.description = description
    this.icon = ""
    this.statusText = ""
    this.message = ""
    this.setStatus(status,message)
}

FeatureTask.FAILED = -1
FeatureTask.WAITING = 1
FeatureTask.RUNNING = 2
FeatureTask.SUCCEED = 3

FeatureTask.prototype._getIcon = function() {
    if (this.status === FeatureTask.FAILED) {
        return "fa-close"
    } else if (this.status === FeatureTask.WAITING) {
        return "fa-pause"
    } else if (this.status === FeatureTask.RUNNING) {
        return "fa-spinner"
    } else if (this.status === FeatureTask.SUCCEED) {
        return "fa-check"
    }  else {
        return "fa-spinner"
    }
}

FeatureTask.prototype._getStatusText = function() {
    if (this.status === FeatureTask.FAILED) {
        return "Failed"
    } else if (this.status === FeatureTask.WAITING) {
        return "Waiting"
    } else if (this.status === FeatureTask.RUNNING) {
        return "Running"
    } else if (this.status === FeatureTask.SUCCEED) {
        return "OK"
    }  else {
        return "Running"
    }
}

FeatureTask.prototype.setStatus = function(status,message) {
    this.status = status
    this.message = message || ""
    this.statusText = this._getStatusText()
    this.icon = this._getIcon()
    if (this.manager && this.manager.changeCallback) this.manager.changeCallback()
}

let FeatureTaskManager = function(changeCallback) {
    this.changeCallback = changeCallback
}

//return true if init succeed;otherwise return false
FeatureTaskManager.prototype.initTasks = function(feat) {
    if (this.changeCallback) this.changeCallback()
    feat.tasks = feat.tasks || []
    if (feat.tasks.length > 0) {
        if (feat.tasks.find(function(t){return t.status === FeatureTask.WAITING || t.status === FeatureTask.RUNNING})) {
            alert("Feature still has running jobs.")
            return false
        }
        feat.tasks.length = 0
    } 
    return true
}
FeatureTaskManager.prototype.clearTasks = function(feat) {
    var vm = this
    setTimeout(function(){
        if (vm.changeCallback) vm.changeCallback()
        if (feat.tasks) {
            feat.tasks.length = 0
        }
    },1000)
}
FeatureTaskManager.prototype.getTasks = function(feat) {
    return feat.tasks
}
FeatureTaskManager.prototype.getTask = function(feat,scope,taskId) {
    return feat.tasks.find(function(t) {return t.id === taskId && t.scope === scope})
}
//status should be "waiting","running","succeed","failed"
FeatureTaskManager.prototype.addTask = function(feat,scope,taskId,description,status) {
    if (this.changeCallback) this.changeCallback()
    var task = new FeatureTask(this,scope,taskId,description,status)
        
    feat.tasks.push(task)
    return task
}

FeatureTaskManager.prototype.allTasksSucceed = function(feat,scope) {
    return !((feat.tasks.find(function(t) {return t.scope === scope && t.status !== FeatureTask.SUCCEED}) && true)||false)
}

FeatureTaskManager.prototype.allTasksFinished = function(feat,scope) {
    return !((feat.tasks.find(function(t) {return t.scope === scope && t.status !== FeatureTask.SUCCEED && t.status !== FeatureTask.FAILED}) && true)||false)
}

let Utils = function() {
}

Utils.prototype.SUCCEED = FeatureTask.SUCCEED
Utils.prototype.FAILED = FeatureTask.FAILED
Utils.prototype.WAITING = FeatureTask.WAITING
Utils.prototype.RUNNING = FeatureTask.RUNNING

Utils.prototype.getFeatureTaskManager = function(changeCallback) {
    return new FeatureTaskManager(changeCallback)
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
    var parameters = null
    if (arguments.length > 2) {
        parameters = []
        for(var index = 2;index < arguments.length;index++) {
            parameters.push(arguments[index])
        }
    }
    $.ajax(url ,{
        xhrFields:{
            withCredentials: true
        },
        success:function(data,status,jqXHR) {
            if (parameters) {
                parameters.splice(0,0,true)
                callback.apply(null,parameters)
            } else {
                callback(true)
            }
        },
        error:function(jqXHR) {
            if (parameters) {
                if (jqXHR.status === 401) {
                    parameters.splice(0,0,false)
                } else if(jqXHR.status >= 500) {
                    parameters.splice(0,0,false)
                } else {
                    parameters.splice(0,0,true)
                }
                callback.apply(null,parameters)
            } else {
                if (jqXHR.status === 401) {
                    callback(false)
                } else if(jqXHR.status >= 500) {
                    callback(false)
                } else {
                    callback(true)
                }
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
