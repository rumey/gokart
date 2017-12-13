<template>
    <div style="display:none">
    <div id="featuredetail_control" class="ol-selectable ol-control" v-bind:style="topPositionStyle">
        <button type="button" title="{{layer.title}}" v-bind:style="controlButtonStyle" @click="toggleFeaturedetail()" v-bind:class="{'selected':isControlSelected,'warning':warning}">
            <img v-bind:src="layer.icon" width=36 height=36>
        </button>
        <button v-if="layers.length > 1" type="button" style="height:16px;border-top-left-radius:0px;border-top-right-radius:0px"  @click="showLayers=!showLayers" >
            <i class="fa fa-angle-double-down" aria-hidden="true"></i>
        </button>
        <div v-show="showLayers" style="position:absolute;width:300px;right:0px">
            <button type="button" v-for="l in layers" title="{{l.title}}"  style="margin:1px;float:right" track-by="$index" @click.stop.prevent="selectLayer(l)">
                <img v-bind:src="l.icon" width="36" height="36">
            </button>
        </div>
    </div>
    </div>
  </div>
</template>

<style>
#featuredetail_control .selected{
    background-color: #2199E8;
}
#featuredetail_control .warning{
    background-color: rgba(125, 47, 34, 0.7);
}
#featuredetail_control {
    position: absolute;
    left: auto;
    right: 16px;
    bottom: auto;
    width:48px;
    height:48px;
    padding: 0;
}

</style>

<script>
  import { ol,$,utils} from 'src/vendor.js'
  export default {
    store: {
    },
    data: function () {
      return {
        layer:{},
        layers:[],
        showLayers:false,
        warning:false
      }

    },
    // parts of the template to be computed live
    computed: {
      loading: function () { return this.$root.loading },
      annotations: function () { return this.$root.annotations },
      catalogue:function() { return this.$root.catalogue},
      spotforecast:function() { return this.$root.spotforecast},
      active:function() { return this.$root.active},
      dialog: function () { return this.$root.dialog },
      map: function () { return this.$root.map },
      env: function () { return this.$root.env },
      enabled:function() {
        return this.layers.length > 0
      },
      controlButtonStyle:function() {
        return this.layers.length > 1 ? "height:36px;border-bottom-left-radius:0px;border-bottom-right-radius:0px":""
      },
      height:function() {
        if (this.layers.length === 0) {
            return 0
        } else if (this.layers.length === 1) {
            return 48
        } else if (!this.showLayers) {
            return 52
        } else {
            return 52 + Math.ceil(this.layers.length / 6) * 50
        }
      },
      topPosition:function() {
        return 180 + this.spotforecast.height + 9;
      },
      topPositionStyle:function() {
        return "top:" + this.topPosition + "px";
      },
      mapControl:function() {
        if (!this._controller) {
            this._controller = new ol.control.Control({
                element: $('#featuredetail_control').get(0),
        	target: $('#external-controls').get(0)
            })
        }
        return this._controller
      },
      isControlSelected:function() {
        if (this.annotations) {
            return !this.warning && this.annotations.tool === this._featuredetailTool
        } else {
            return false
        }
      },
    },
    watch:{
    },
    // methods callable from inside the template
    methods: {
      toggleFeaturedetail: function () {
        if (!this._featuredetailTool || this.annotations.tool === this._featuredetailTool) {
            this.annotations.setTool('Pan')
        } else  {
            this.annotations.setTool(this._featuredetailTool)
            // enable resource bfrs layer, if disabled
            var mapLayer = this.map.getMapLayer(this.layer)
            if (!mapLayer) {
              this.catalogue.onLayerChange(this.layer, true)
            } else if (this.active.isHidden(mapLayer)) {
                this.active.toggleHidden(mapLayer)
            }
        }
        this.warning = false
      },
      selectLayer:function(l) {
        this.showLayers = false
        if (this.layer === l) {
            return
        }
        /*
        if (this.layer) {
            //remove the preivouse selected layer from map
            var mapLayer = this.map.getMapLayer(this.layer)
            if (mapLayer) {
              this.catalogue.onLayerChange(this.layer, false)
            }
        }
        */
        this.layer = l
        this.warning = false
        if (this.isControlSelected) {
            // enable resource bfrs layer, if disabled
            var mapLayer = this.map.getMapLayer(this.layer)
            if (!mapLayer) {
              this.catalogue.onLayerChange(this.layer, true)
            } else if (this.active.isHidden(mapLayer)) {
                this.active.toggleHidden(mapLayer)
            }

        }
      }
    },
    ready: function () {
      var vm = this
      this._featuredetailStatus = vm.loading.register("featuredetail","Feature Detail Component")

      this._featuredetailStatus.phaseBegin("gk-init",80,"Listen 'gk-init' event",true,true)
      this.$on('gk-init', function() {
        vm._featuredetailStatus.phaseEnd("gk-init")

        vm._featuredetailStatus.phaseBegin("initialize",20,"Initialize",true,false)

        vm.catalogue.catalogue.forEach(function(layer){
            if (layer.tags && layer.tags.some(function(o) {return o.name === "detail_link" || o.name === "detail_dialog"} )) {
                layer.icon = "/dist/static/images/" + layer.id.replace(":","-").toLowerCase() + ".png"
                vm.layers.splice(0,0,layer)
            }
        })
        if (vm.layers.length) {
            vm.layer = vm.layers[0]

            vm.map.mapControls["featuredetail"] = {
                enabled:false,
                autoenable:false,
                controls:vm.mapControl
            }
    
            var featuredetailInter = new ol.interaction.Interaction({
                handleEvent:function(browserEvent) {
                    if (!ol.events.condition.click(browserEvent)) {
                        return true
                    }
                    var topLeft = vm.map.olmap.getCoordinateFromPixel(browserEvent.pixel.map(function(d){return d - 10}))
                    var bottomRight = vm.map.olmap.getCoordinateFromPixel(browserEvent.pixel.map(function(d){return d + 10}))

                    var bbox = "&bbox=" + bottomRight[1] + "," + topLeft[0] + "," + topLeft[1] + "," + bottomRight[0]
                    $.ajax({
                        url:vm.env.wfsService + "/wfs?service=wfs&version=2.0&request=GetFeature&count=1&outputFormat=application%2Fjson&typeNames=" + getDetailLayerId(vm.layer.id) + bbox,
                        dataType:"json",
                        success: function (response, stat, xhr) {
                            if (response.totalFeatures < 1) {
                                vm.warning = true
                                return
                            }

                            if (vm.layer.tags && vm.layer.tags.some(function(o) {return o.name === "detail_link"} )) {
                                if (response.features[0].properties["url"]) {
                                    utils.editResource(browserEvent,null,response.features[0].properties["url"],vm.layer.id,true)
                                    vm.warning = false
                                }
                            } else if (vm.layer.tags && vm.layer.tags.some(function(o) {return o.name === "detail_dialog"} )) {
                               var messages = []
                                $.each(response.features[0].properties,function(key,value) {
                                    if (['ogc_fid','md5_rowhash'].indexOf(key) >= 0){
                                        return
                                    }
                                    if (vm.dialog.isLink(value)) {
                                        messages.push([[key,3,"detail_name"],[value,9,"detail_value",vm.layer.id + "." + key]])
                                    } else {
                                        messages.push([[key,3,"detail_name"],[value,9,"detail_value"]])
                                    }
                                })
                                vm.dialog.show({
                                    messages:messages,
                                    buttons:[]
                                })
                            } else {
                                vm.warning = true
                            }
                        },
                        error: function (xhr,status,message) {
                            vm.warning = true
                            alert(xhr.status + " : " + (xhr.responseText || message))
                        },
                        xhrFields: {
                            withCredentials: true
                        }
                    })
                    
                    return false
                }
            });

            vm._featuredetailTool = {
              name: 'FeatureDetail',
              interactions:[
                  featuredetailInter
              ]
            }

            vm.annotations.tools.push(vm._featuredetailTool)
        }

        vm._featuredetailStatus.phaseEnd("initialize")
      })
        
    }
  }
</script>
