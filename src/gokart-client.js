var clientId = new Date().getTime().toString() + Math.random().toString().substring(1)
var debug = window.location.search?(window.location.search.toLowerCase().indexOf("debug=true") >= 0):false 
var requestId = 0
var pendingRequests = {}

function GokartClient(app,module,timeout) {
    var vm = this
    this.serverUrl = window.location.origin + "/" + app;
    this.app = app;
    this.defaultModule = module;
    this.channelName = "gokart(" + this.serverUrl + ")"
    this.timeoutTask = null
    this.gokartWindow = null

    window.addEventListener('storage',function(e){
        if (!e.key.startsWith(this.channelName)) {
            return
        }
        var response = JSON.parse(e.newValue)
        response["channel"] = "localStorage"
        if (!response["requestId"]) {
            return
        }
        vm._processResponse(response)
    })
}

GokartClient.prototype._processResponse = function (respose) {
    try { 
        this._clearTimeoutTask()
        if (response["clientId"] !== clientId) {
            return
        }

        if (debug) console.log(Date() + " : Receive response with requestId '" + response["requestId"] + "' through " + response["channel"]  + ". response = " + JSON.stringify(response.data))

        if (response.data["status"] !== "OK") {
            alert(response.data["status"] + " : " + response.data["message"])
        }
    } finally{
        delete pendingRequests[response["requestId"].toString()]
    }
}

GokartClient.prototype._clearTimeoutTask = function(){
    if (this.timeoutTask) {
        if (debug){
            console.log(Date() + " : Clear timeout task for app '" + this.app + "'")
        }
        clearTimeout(this.timeoutTask)
        this.timeoutTask = null
    }
}
GokartClient.prototype.populateRequest = function(method,data){
    pendingRequests[(++requestId).toString()] = this
    return {
        method:method,
        clientId:clientId,
        requestId:requestId,
        time:Date(),
        data:data
    }
}
GokartClient.prototype.open = function(options,module){
    module = module || this.defaultModule
    var vm = this

    var request = JSON.stringify(vm.populateRequest('open',{module:module,options:options}))
    var syncMessageFunc = null
    var postMessageFunc = function() {

        if (debug) console.log(Date() + " : " + vm.app + " is opened and send request to " + vm.app + " through postMessage. request = " + request)
        vm.gokartWindow.postMessage(request,window.location.origin);

        vm._clearTimeoutTask;
        if (debug) console.log(Date() + " : Create a timeout task to resend the request  if postMessage to " + vm.app + " is timeout. timeout = 10 seconds" )
        vm.timeoutTask = setTimeout(function(){
            vm.timeoutTask = null
            if (debug){
                console.log(Date() + " : post request to " + vm.app + " timeout")
            }
            if (this.gokartWindow && !this.gokartWindow.closed()) {
                this.gokartWindow.close()
            }
            vm.gokartWindow = null
            syncMessageFunc()
        },10000)
    }

    var syncMessageFunc = function() {
        if (debug) console.log(Date() + " : Sent request to " + vm.app + " through localStorage. request = " + request)
        localStorage.setItem(vm.channelName + ".open",request)
        vm._clearTimeoutTask()
        if (debug) console.log(Date() + " : Create a timeout task to send request to " + vm.app + " if " + vm.app + " is not opened before. timeout = 5 seconds" )
        vm.timeoutTask = setTimeout(function() {
            vm.timeoutTask = null
            if (debug) console.log(Date() + " : Send request to " + vm.app + " through localStorage timeout, try to open " + vm.app)
            vm.gokartWindow = window.open(vm.serverUrl)
            vm.gokartWindow.onload = function() {
                postMessageFunc()
            }
        },5000)
    }

    if (this.gokartWindow && !this.gokartWindow.closed()) {
        postMessageFunc()
    } else {
        syncMessageFunc()
    }

}

window.addEventListener("message",receiveMessage,false)
function receiveMessage(event) {
    if (event.origin != window.location.origin) {
        return
    }

    var response = JSON.parse(event.data)
    if (!response["requestId"]) {
        return
    }
    response["channel"] = "postMessage"
    if ( pendingRequests[response["requestId"].toString()] ) {
        pendingRequests[response["requestId"].toString()]._processResponse(processResponse)
    }
}

global.GokartClient = GokartClient
