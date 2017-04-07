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
    
}

GokartListener.prototype._processRequest = function(request,sentResponse) {
    if (this.debug) console.log(Date() + " : Receive a request through localStorage. request = " + JSON.stringify(request))
    sentResponse(JSON.stringify(this.populateResponse(request,"RECEIVED")))
    if (!gokart || !gokart["loading"]) {
        if (this.debug) console.log("gokart is loading")
        setTimeout(func,1000)
    } else if (gokart['loading'].completedPercentage < 100) {
        if (this.debug) console.log("gokart is initializing")
        setTimeout(func,1000)
    } else if (gokart['loading'].completedPercentage === -1) {
        sentResponse(JSON.stringify(this.populateResponse(request,"GOKART_FAILED",gokart['loading'].message)))
    } else if (request["method"] === "open") {
        if (!gokart[request["data"]['module']]) {
            sentResponse(JSON.stringify(this.populateResponse(request,"MODULE_NOT_FOUND")))
        } else if (!gokart[request["data"]["module"]]["open"]) {
            sentResponse(JSON.stringify(this.populateResponse(request,'METHOD_NOT_SUPPORT')))
        } else {
            try {
                gokart[data["module"]].open(data['options'])
                window.focus();
                sentResponse(JSON.stringify(this.populateResponse(request,'OK')))
            } catch(ex) {
                sentResponse(JSON.stringify(this.populateResponse(request,'METHOD_FAILED',ex)))
            }
        }
    } else {
        sentResponse(JSON.stringify(this.populateResponse(request,'UNKNOWN_METHOD')))
    }
}
GokartListener.prototype.populateResponse = function(request,status,failedReason) {
    var response = {
        clientId:request["clientId"],
        requestId:request["requestId"],
        time:Date(),
        data:{
            status:status,
            message:""
        }
    }
    var data = response["data"]
    if (status === "RECEIVED") {
        data["message"] = "Request is received from " + request["channel"] + ". data = " + JSON.stringify(request["data"])
    } else if (status === "GOKART_FAILED") {
        data["message"] = failedReason
    } else if (status === "MODULE_NOT_FOUND") {
        data["message"] = "Module(" + gokart[request["data"]['module']] + ") is not found."
    } else if (status === "METHOD_NOT_SUPPORT") {
        data["message"] = "Module(" + gokart[request["data"]['module']] + ") does not support method " + request["method"] +"."
    } else if (status === "OK") {
        data["message"] = "Succeed to execute method '" + request["method"] + "', data = " + JSON.stringify(request["data"])
    } else if (status === "UNKNOWN_METHOD") {
        data["message"] = "Rquest method '" + request["method"] + "' is unknown, data = " + JSON.stringify(request["data"])
    } else if (status === "METHOD_FAILED") {
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
    request["channel"] = "localStorage"
    gokartListener._processRequest(request,function(response){
        event.source.postMessage(response,window.location.origin)
    })
}

export default gokartListener
