import { $,moment } from 'src/vendor.js'


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
FeatureTask.FAIL_CONFIRMED = -2
FeatureTask.WAITING = 1
FeatureTask.RUNNING = 2
FeatureTask.SUCCEED = 3
FeatureTask.WARNING = 4
FeatureTask.IGNORED =  5
FeatureTask.MERGED =  6

FeatureTask.prototype._getIcon = function() {
    if (this.status === FeatureTask.FAILED || this.status === FeatureTask.FAIL_CONFIRMED) {
        return "fa-close"
    } else if (this.status === FeatureTask.WAITING) {
        return "fa-pause"
    } else if (this.status === FeatureTask.RUNNING) {
        return "fa-spinner"
    } else if (this.status === FeatureTask.SUCCEED) {
        return "fa-check"
    } else if (this.status === FeatureTask.WARNING) {
        return "fa-warning"
    } else if (this.status === FeatureTask.IGNORED) {
        return "fa-minus"
    } else if (this.status === FeatureTask.MERGED) {
        return "fa-link"
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
    } else if (this.status === FeatureTask.WARNING) {
        return "Warning"
    } else if (this.status === FeatureTask.IGNORED) {
        return "Ignored"
    } else if (this.status === FeatureTask.MERGED) {
        return "Merged"
    } else if (this.status === FeatureTask.FAIL_CONFIRMED) {
        return "Failed"
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
    //call when feature's tasks changed.
    this.changeCallback = changeCallback
}

//return true if init succeed;otherwise return false
FeatureTaskManager.prototype.initTasks = function(feat) {
    if (this.changeCallback) this.changeCallback()
    if (feat.tasks && feat.tasks.length > 0) {
        if (feat.tasks.find(function(t){return t.status === FeatureTask.WAITING || t.status === FeatureTask.RUNNING})) {
            alert("Feature still has running jobs.")
            return false
        }
    }
    feat.tasks = []
    return true
}
FeatureTaskManager.prototype.clearTasks = function(feat) {
    var vm = this
    var tasks = feat.tasks
    if (!tasks || tasks.length === 0) {
        return
    }
    var delay = 1000
    if (this.allTasksSucceed(feat)) {
        delay = 1000
    } else if(this.allTasksNotFailed(feat)) {
        delay = 10000
    } else {
        delay = 60000
    }
    setTimeout(function(){
        if (vm.changeCallback) vm.changeCallback()
        if (tasks) {
            tasks.length = 0
        }
    },delay)
}
FeatureTaskManager.prototype.getTasks = function(feat) {
    return feat.tasks || []
}
FeatureTaskManager.prototype.getTask = function(feat,scope,taskId) {
    return feat.tasks?(feat.tasks.find(function(t) {return t.id === taskId && t.scope === scope})):null
}
//status should be "waiting","running","succeed","failed"
FeatureTaskManager.prototype.addTask = function(feat,scope,taskId,description,status) {
    if (this.changeCallback) this.changeCallback()
    var task = new FeatureTask(this,scope,taskId,description,status)
        
    feat.tasks.push(task)
    return task
}

FeatureTaskManager.prototype.allTasksSucceed = function(feat,scope) {
    return feat.tasks.find(function(t) {return (!scope || t.scope === scope) && [FeatureTask.SUCCEED,FeatureTask.IGNORED,FeatureTask.MERGED].indexOf(t.status) === -1 })?false:true;
}

FeatureTaskManager.prototype.allTasksNotFailed = function(feat,scope) {
    return feat.tasks.find(function(t) {return (!scope || t.scope === scope) && [FeatureTask.SUCCEED,FeatureTask.IGNORED,FeatureTask.MERGED,FeatureTask.WARNING].indexOf(t.status) === -1 })?false:true;
}

FeatureTaskManager.prototype.allTasksFinished = function(feat,scope) {
    return feat.tasks.find(function(t) {return (!scope || t.scope === scope) && [FeatureTask.RUNNING,FeatureTask.WAITING].indexOf(t.status) >= 0 })?false:true;
}

FeatureTaskManager.prototype.errorMessages = function(feat,scope) {
    return feat.tasks.filter(function(t) {return (!scope || t.scope === scope) && [FeatureTask.FAILED,FeatureTask.WARNING].indexOf(t.status) >= 0 && t.message }).map(function(t){return t.message;})
}

let Utils = function() {
}

Utils.prototype.importSpatialFileTypes = "";//".json,.geojson,.gpx,.gpkg"
Utils.prototype.importSpatialFileTypeDesc = "Support GeoJSON(.geojson .json), GPS data(.gpx), GeoPackage(.gpkg), 7zip(.7z), TarFile(.tar.gz,tar.bz,tar.xz),ZipFile(.zip)"

Utils.prototype.SUCCEED = FeatureTask.SUCCEED
Utils.prototype.FAILED = FeatureTask.FAILED
Utils.prototype.WAITING = FeatureTask.WAITING
Utils.prototype.RUNNING = FeatureTask.RUNNING
Utils.prototype.WARNING = FeatureTask.WARNING
Utils.prototype.IGNORED = FeatureTask.IGNORED
Utils.prototype.MERGED = FeatureTask.MERGED
Utils.prototype.FAIL_CONFIRMED = FeatureTask.FAIL_CONFIRMED

Utils.prototype.getFeatureTaskManager = function(changeCallback) {
    return new FeatureTaskManager(changeCallback)
}

Utils.prototype.checkPermission = function(url,method,callback) {
    method = method || "GET"
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
    if (arguments.length > 3) {
        parameters = []
        for(var index = 3;index < arguments.length;index++) {
            parameters.push(arguments[index])
        }
    }
    var ajaxSetting = {
        xhrFields:{
            withCredentials: true
        },
        method:method,
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
        
    }
    if (["POST","PATCH","PUT"].indexOf(method) >= 0) {
        ajaxSetting["contentType"] = "application/json"
        ajaxSetting["data"] = JSON.stringify({})
    }
    $.ajax(url ,ajaxSetting)
}

Utils.prototype.editResource = function(event,options,url,target) {
    if (!url) {
        var targetElement = (event.target.nodeName == "A")?event.target:event.target.parentNode;
        url = targetElement.href
        target = targetElement.target
    }
    if (!target) {
        target = "_blank"
    }
    if (env.appType == "cordova") {
        window.open(url,"_system");
    } else {
        options = options || "scrollbars=yes,locationbar=no,menubar=no,statusbar=yes,toolbar=no,personalbar=no,centerscreen=yes,width=" + Math.floor(window.innerWidth * 0.95) + ",height=" + Math.floor(window.innerHeight * 0.95)
        var  win = window.open(url,target,options);
        setTimeout(function(){win.focus()},500)
    }
}

Utils.prototype.submitForm = function(formid,options) {
    var form = $("#" + formid)

    if (env.appType == "cordova") {
        form.submit()
    } else {
        var target = form.attr("target") || "_blank"
        options = options || "scrollbars=yes,locationbar=no,menubar=no,statusbar=yes,toolbar=no,personalbar=no,centerscreen=yes,width=" + Math.floor(window.innerWidth * 0.95) + ",height=" + Math.floor(window.innerHeight * 0.95)
        var win = null;
        if (target !== "_blank" ) {
            win = window.open("",target,options);
        }
        form.submit()
        if (win) {
            setTimeout(function(){win.focus()},500)
        }
    }
}

Utils.prototype.getWindowTarget = function(target){
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
            alert(xhr.status + " : " + message)
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
                eval("ProxyClass.prototype[\"" + key + "\"] = function() { \
                    return this._objectPrototype[\"" + key + "\"].apply(this._object,arguments); \
                }")
            }
        }

        for(var i = 0;i < methods.length;i++) {
            key = methods[i]
            eval("ProxyClass.prototype[\"" + key + "\"] = function() { \
                return this._object[\"" + key + "\"]?this._object[\"" + key + "\"].apply(this._object,arguments) : undefined; \
            }")
        }

        for (var key in attrs) {
            eval("ProxyClass.prototype[\"" + key + "\"] = function() { \
                return attrs[\"" + key + "\"].apply(this._object,arguments); \
            }")
        }

        ProxyClass.prototype.constructor = ProxyClass
        proxyCache[classname] = ProxyClass
    }
    return new proxyCache[classname](object)

}
//verify the user input date string.
//event, the dom event trigger this verification
//inputPattern: the array of input patterns 
//pattern: the pattern to normialize the user input 
//if correct, format the date with pattern
//if failed, set focus to the date element
//return true if correct;otherwise return false
Utils.prototype.verifyDate = function(event,inputPattern,pattern) {
    var element = event.target;
    element.value = element.value.trim()
    if (element.value.length > 0) {
        var m = moment(element.value,inputPattern,true)
        if (!m.isValid()) {
            setTimeout(function() {
                element.focus()
            },10);
            return false
        } else {
            element.value = m.format(pattern)
            $(element).trigger('change')
            return true
        }
    } else {
        return true
    }
}

//Return a list of moment object whose time is specified in timesInDay array
//timesInDay: specify the time part in format "HH:mm:ss" ,required
//size: the number of the datetimes , required
//stragegy: the way to get the first datetime, default is 2
//  1: The first datetime is consisted with current date and first time in timesInDay
//  2: The first datetime is consisted with current date and the nearest time before current time in timesInDay 
//  3: The first datetime is consisted with current date and the nearest time after current time in timesInDay 
//startDate: the start datetime of the forecast,if missing, current datetime will be used
Utils.prototype.getDatetimes = function(timesInDay,size,strategy,startDate) {
    startDate = startDate || moment().tz("Australia/Perth");
    var currentDate = startDate.format("YYYY-MM-DD");
    strategy = strategy || 2;

    var result = [];
    var timeIndex = -1;
    if (strategy === 2 || strategy === 3) {
        $.each(timesInDay,function(index,time){
            if (strategy === 2 && startDate < moment.tz(currentDate + " " + time,"Australia/Perth") ) {
                if (index === 0) {
                    timeIndex = timesInDay.length - 1;
                    startDate.date(startDate.date() - 1);
                } else {
                    timeIndex = index - 1;
                }
                return false;
            } else if (strategy === 3 && startDate < moment.tz(currentDate + " " + time,"Australia/Perth") ) {
                furstIndex = index;
                return false;
            }
        })
        if (strategy === 3 && timeIndex === -1) {
            timeIndex = 0;
            startDate.date(startDate.date() + 1);
        }
    } else {
        timeIndex = 0;
    }
    var result = [];
    while (result.length < size) {
        result.push( moment.tz(startDate.format("YYYY-MM-DD") + " " + timesInDay[timeIndex],"Australia/Perth") );
        timeIndex += 1;
        if (timeIndex >= timesInDay.length) {
            timeIndex = 0;
            startDate.date(startDate.date() + 1);
        }
    }
    return result
}

var utils = new Utils()

export default utils
