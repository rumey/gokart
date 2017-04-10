<template>
    <div id="loading-status-overlay" v-if="show">
    <div id="loading-status" v-if="show">
      <div class="row" >
        <div class="small-11">
            <h4>Status</h4>
        </div>
        <div class="small-1">
            <a @click="close" class="close" v-show="closable"><i class="fa fa-close" aria-hidden="true"></i></a>
        </div>
      </div>
      <div class="row application" >
          <div class="small-7">
              <a class="name">{{application}} </a>
          </div>
          <div class="small-5">
              <div v-for="(index,phase) in phaseStatus(appStatus.phases)"  tracking-by="$index">
                  <br v-if="index > 0">
                  <a v-if="!phaseStatus(phase).async" class="float-right"><i class="fa fa-spinner" aria-hidden="true"></i></a>
                  <a v-if="phaseStatus(phase).async" class="float-right"><i class="fa fa-pause" aria-hidden="true"></i></a>
                  <a class="action">{{phaseStatus(phase).description}}</a>
                  <a class="error" v-if="phase.failed">({{phaseStatus(phase).reason}})</a>
              </div>
              <a v-if="phaseStatus(appStatus).isSucceed()" class="float-right">OK</a>
          </div>
      </div>
      <div v-for="status in components" class="row component" track-by="id">
        <div class="small-7">
            <a class="name">{{status.name}} </a>
        </div>
        <div class="small-5">
          <div v-for="(index,phase) in phaseStatus(status.phases)" tracking-by="$index">
            <a v-if="!phaseStatus(phase).async" class="float-right"><i class="fa fa-spinner" aria-hidden="true"></i></a>
            <a v-if="phaseStatus(phase).async" class="float-right"><i class="fa fa-pause" aria-hidden="true"></i></a>
            <a class="action">{{phaseStatus(phase).description}}</a>
            <a class="error" v-if="phaseStatus(phase).failed">({{phaseStatus(phase).reason}})</a>
          </div>
          <a v-if="phaseStatus(status).isSucceed()" class="float-right">OK</a>
        </div>
      </div>
      <div v-if="hasError">
          <hr class="row" style="border-width:4px;">
          <div v-for="error in errors" class="row"  track_by="id">
            <div class="small-12">
                <a class="error">{{error.id}} : {{error.message}} </a>
            </div>
          </div>
      </div>
    </div>
    </div>
</template>

<style>
#loading-status-overlay {
    position: absolute;
    top: 0%;
    left: 0%;
    width: 100%;
    height: 100%;
    background-color: rgba(0,0,0,0);
    opacity: 1;
    z-index:2147483647;
}
#loading-status {
    position: absolute;
    top: 50%;
    left:50%;
    width:600px;
    border-style:solid;
    padding:10px 10px 10px 10px;
    transform: translate(-50%,-50%);
    background-color: rgba(0,0,0,0.3);
    opacity: 1;
}
#loading-status .application{
    font-size: 1.1em
}
#loading-status .component{
    font-size: 1em;
    font-style: italic;
}
#loading-status .component .name{
    padding-left:20px
}
#loading-status .error {
    color: #ec5840;
    font-weight: bold;
}
#loading-status .close {
    color: black;
}
</style>

<script>
  import { $,Vue } from 'src/vendor.js'
  export default {
    data: function () {
      return {
        app:null,
        components:[],
        revision:1,
        errors:[],
      }
    },
    computed: {
      hasError:function() {
        return this.errors.length > 0
      },
      show: function() {
        return true//this.revision && true && ( !this.app || !this.app.isReady() || this.errors.length > 0) || this.components.find(function(component){return !component.isReady()})
      },
      closable: function() {
        return this.revision && this.app && ( this.app.isFinished() )
      },
      appStatus:function() {
        return  this.revision && (this.app || {})
      },
    },
    props:["application"],
    methods: {
      close:function() {
          $("#loading-status-overlay").remove()
          $("#loading-status").remove()
      },
      phaseStatus:function(status) {
        return this.revision && status
      },
      getStatus:function(componentId) {
        return this.components.find(function(o){
            return o.id === componentId
        })
      },
      register: function(componentId,componentName) {
        componentName = componentName || componentId
        var vm = this
        if (!vm.Status) {
            vm.Status = function(componentId,componentName) {
                if (componentId === "app") {
                    vm.app = this
                    vm.revision += 1
                } else {
                    var index = -1
                    for(var i = 0; i < vm.components.length;i++) {
                        if (componentId === vm.components[i].id) {
                            index = i
                            break
                        }
                    }
                    if (index > 0) {
                        //already registered, replace
                        vm.componets[index] = this
                    } else {
                        //not registered, add it
                        vm.components.push(this)
                    }
                    vm.revision += 1
                    
                }
                this.id = componentId
                this.name = componentName
                this.completed = 0
                this.processed = 0
                this.phases = []
                return this
            }
            vm.Status.prototype._change = function() {
                if (vm.app === this) {
                    //app status
                    vm.revision += 1
                } else {
                    //component status
                    vm.revision += 1
                    for(var i = 0; i < vm.components.length;i++) {
                        if (this.id === vm.components[i].id) {
                            Vue.set(vm.components,i,vm.components[i])
                            break
                        }
                    }
                }
            }
            vm.Status.prototype.phaseBegin = function(name,weight,description,critical,async) {
                this.phases.push({name:name,weight:weight,description:description,critical:critical || true,async:async || false})
                this._change()
            }
            vm.Status.prototype.phaseEnd = function(name) {
                if (this.completed >= 100) return
                var index = this.phases.findIndex(function(o) {return o.name === name})
                if (index < 0) return
                this.completed += this.phases[index].weight
                this.processed += this.phases[index].weight
                this.phases.splice(index,1)
                this._change()
            }
            vm.Status.prototype.phaseFailed = function(name,reason) {
                if (this.completed >= 100) return
                var phase = this.phases.find(function(o) {return o.name === name})
                if (!phase) return
                this.processed += phase.weight
                phase["reason"] = reason
                phase["failed"] = true
                this._change()
            }
            vm.Status.prototype.failedPhases = function() {
                return this.phases.filter(function(o) {return o.failed})
            }
            vm.Status.prototype.isSucceed = function() {
                return this.completed >= 100
            }
            vm.Status.prototype.isFinished = function() {
                return this.processed >= 100
            }
            vm.Status.prototype.isReady = function(reason) {
                return !this.phases.find(function(o) {return o.failed && o.critical})
            }
        }
        return new vm.Status(componentId,componentName)
      }
    },
    ready: function () {
        var vm = this
        vm.register("app",this.application)
        var loadingStatus = vm.register("LoadingStatus","Loading Status Component")
        loadingStatus.phaseBegin("initialize",100,"Override console")
        //override console.error
        var getArguments = function(args,startIndex) {
            var result = []
            startIndex = (startIndex === null||startIndex === undefined)?0:startIndex
            for(var i = startIndex; i < args.length ; i++) {
                result.push(args[i])
            }
            return result
        }
        console.error = (function(){
            var originFunc = console.error
            return function(args) {
                var message = null
                if (arguments.length == 1) {
                    if (typeof arguments[0] === "string") {
                        message = arguments[0]
                    } else {
                        message = JSON.stringify(arguments[0])
                    }
                } else {
                    message = JSON.stringify(getArguments(arguments))
                }
                if (vm.errors.findIndex(function(e){return e.message === message}) >= 0) {
                    //already exist, return to prevent dead loop
                    return
                }
                vm.errors.push({"id": vm.errors.length + 1 ,"message":message})
                originFunc.apply(this,arguments)
            }
        })()
        //override console.error
        console.assert = (function(){
            var originFunc = console.assert
            return function(args) {
                if (!arguments[0]) {
                    if (arguments.length == 2) {
                        if (typeof arguments[1] === "string") {
                            vm.errors.push(arguments[1])
                        } else {
                            vm.errors.push(JSON.stringify(arguments[1]))
                        }
                    } else {
                        vm.errors.push(JSON.stringify(getArguments(arguments,1)))
                    }
                }
                originFunc.apply(this,arguments)
            }
        })()
        //customize vue error handler
        Vue.config.errorHandler = (function(){
            var originFunc = Vue.config.errorHandler
            return function(err,vm) {
                vm.errors.push(err)
                return originFunc(err,vm)
            }
        })()
        loadingStatus.phaseEnd("initialize")
    }
  }
</script>
