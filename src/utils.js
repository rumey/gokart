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
FeatureTask.WAITING = 1
FeatureTask.RUNNING = 2
FeatureTask.SUCCEED = 3
FeatureTask.WARNING = 4
FeatureTask.IGNORED =  5
FeatureTask.MERGED =  6

FeatureTask.prototype._getIcon = function() {
    if (this.status === FeatureTask.FAILED) {
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
    var tasks = feat.tasks
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
    return feat.tasks.find(function(t) {return (!scope || t.scope === scope) && [FeatureTask.SUCCEED,FeatureTask.IGNORED,FeatureTask.MERGED].indexOf(t.status) === -1 })?false:true;
}

FeatureTaskManager.prototype.allTasksNotFailed = function(feat,scope) {
    return feat.tasks.find(function(t) {return (!scope || t.scope === scope) && [FeatureTask.SUCCEED,FeatureTask.IGNORED,FeatureTask.MERGED,FeatureTask.WARNING].indexOf(t.status) === -1 })?false:true;
}

FeatureTaskManager.prototype.allTasksFinished = function(feat,scope) {
    return feat.tasks.find(function(t) {return (!scope || t.scope === scope) && [FeatureTask.RUNNING,FeatureTask.WAITING].indexOf(t.status) >= 0 })?false:true;
}

let Utils = function() {
}

Utils.prototype.SUCCEED = FeatureTask.SUCCEED
Utils.prototype.FAILED = FeatureTask.FAILED
Utils.prototype.WAITING = FeatureTask.WAITING
Utils.prototype.RUNNING = FeatureTask.RUNNING
Utils.prototype.WARNING = FeatureTask.WARNING
Utils.prototype.IGNORED = FeatureTask.IGNORED
Utils.prototype.MERGED = FeatureTask.MERGED

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

Utils.prototype.isMobile= function() {
    var check = false;
    (function(a){if(/(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino|android|ipad|playbook|silk/i.test(a)||/1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(a.substr(0,4))) check = true;})(navigator.userAgent||navigator.vendor||window.opera);
    if (!check) {
        if(window.innerWidth <= 800 && window.innerHeight <= 600) {
            check = true;
        }
    }

    return check;
}();

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
        var win = null;
        if (this.isMobile) {
            win = window.open(url,target);
        } else {
            options = options || "locationbar=yes,menubar=yes,statusbar=yes,toolbar=yes,personalbar=yes,centerscreen=true,width=" + Math.floor(window.innerWidth * 0.95) + ",height=" + Math.floor(window.innerHeight * 0.95)
            win = window.open(url,target,options);
        }
        setTimeout(function(){win.focus()},500)
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

var utils = new Utils()

export default utils
