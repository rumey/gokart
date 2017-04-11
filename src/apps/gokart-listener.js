let GokartListener = function() {
    var vm = this
    this.debug = window.location.search?(window.location.search.toLowerCase().indexOf("debug=true") >= 0):false 
    this.channelName = "gokart(" + window.location.origin + window.location.pathname + ")"

    window.addEventListener('storage',function(e){
        if (e.key === vm.channelName + ".open") {
            var request = JSON.parse(e.newValue)
            if (!request["clientId"] || !request["data"]) {
                if (this.debug) console.log(Date() + " : Request without clientId or request data is received from channel " + vm.channelName + ".open. request = " + e.newValue)
                return 
            }
            if (request["method"] !== "open") {
                if (this.debug) console.log(Date() + " : Request with invalid method is received from channel " + vm.channelName + ".open. request = " + e.newValue)
                return
            }

            request["channel"] = "localStorage"
            vm._processRequest(request,function(response){
                localStorage.setItem(vm.channelName + ".openstatus",response)
            })
        }
    })
    
    if (this.debug) console.log(Date() + " : Gokart listener is initialized." )
}

GokartListener.prototype._processRequest = function(request,sentResponse) {
    var vm = this
    var func = function() {
        if (vm.debug) console.log(Date() + " : Receive a request through " + request["channel"] + ". request = " + JSON.stringify(request))
        sentResponse(JSON.stringify(vm.populateResponse(request,"RECEIVED")))
        if (!window.gokart || !window.gokart["loading"].appStatus.isFinished()) {
            if (vm.debug) console.log("gokart is loading")
            setTimeout(func,1000)
        } else if (!(window.gokart['loading'].appStatus.isSucceed())) {
            sentResponse(JSON.stringify(vm.populateResponse(request,"GOKART_FAILED",window.gokart['loading'].appStatus.failedMessages())))
        } else if (request["method"] === "open") {
            if (!window.gokart[request["data"]['module']]) {
                sentResponse(JSON.stringify(vm.populateResponse(request,"MODULE_NOT_FOUND")))
            } else if (!window.gokart[request["data"]["module"]]["open"]) {
                sentResponse(JSON.stringify(vm.populateResponse(request,'METHOD_NOT_SUPPORT')))
            } else {
                var moduleStatus = window.gokart['loading'].getStatus(request["data"]["module"])
                if (!moduleStatus.isFinished()) {
                    if (vm.debug) console.log(request["data"]["module"] + " is initializing")
                    setTimeout(func,1000)
                    return
                } else if (!moduleStatus.isSucceed()) {
                    sentResponse(JSON.stringify(vm.populateResponse(request,"GOKART_FAILED",moduleStatus.failedMessages())))
                    return
                }

                try {
                    window.gokart[request["data"]["module"]].open(request["data"]['options'])
                    window.focus();
                    sentResponse(JSON.stringify(vm.populateResponse(request,'OK')))
                } catch(ex) {
                    sentResponse(JSON.stringify(vm.populateResponse(request,'METHOD_FAILED',ex)))
                    throw ex
                }
            }
        } else {
            sentResponse(JSON.stringify(vm.populateResponse(request,'UNKNOWN_METHOD')))
        }
    }
    func()
}
GokartListener.prototype.populateResponse = function(request,code,failedReason) {
    var response = {
        clientId:request["clientId"],
        requestId:request["requestId"],
        time:Date(),
        data:{
            status:"failed",
            code:code,
            message:"",
        }
    }
    var data = response["data"]
    if (code === "RECEIVED") {
        data["message"] = "Request is received from " + request["channel"] + ". data = " + JSON.stringify(request["data"])
        data["status"] = "processing"
    } else if (code === "GOKART_FAILED") {
        data["message"] = failedReason
    } else if (code === "MODULE_NOT_FOUND") {
        data["message"] = "Module(" + window.gokart[request["data"]['module']] + ") is not found."
    } else if (code === "METHOD_NOT_SUPPORT") {
        data["message"] = "Module(" + window.gokart[request["data"]['module']] + ") does not support method " + request["method"] +"."
    } else if (code === "OK") {
        data["message"] = "Succeed to execute method '" + request["method"] + "', data = " + JSON.stringify(request["data"])
        data["status"] = "succeed"
    } else if (code === "UNKNOWN_METHOD") {
        data["message"] = "Rquest method '" + request["method"] + "' is unknown, data = " + JSON.stringify(request["data"])
    } else if (code === "METHOD_FAILED") {
        data["message"] = "Failed to execute method '" + request["method"] + "', data = " + JSON.stringify(request["data"]) + ". Reason = " + failedReason
    }

    if (this.debug) console.log(Date() + " : Send response to client '" + request['clientId'] + "' through " + request["channel"] + " . response = " + JSON.stringify(response))

    return response
}

var gokartListener = new GokartListener()
    
window.addEventListener("message",receiveMessage,false)
function receiveMessage(event) {
    if (event.origin != window.location.origin) {
        return
    }
    var request = JSON.parse(event.data)
    request["channel"] = "postMessage"
    gokartListener._processRequest(request,function(response){
        event.source.postMessage(response,window.location.origin)
    })
}

export default gokartListener
