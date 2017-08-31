<template>
  <div style="display:none">
  <div id="spotforecast" class="ol-selectable ol-control">
      <button type="button" title="Bom sport forecast" @click="toggleSpotForecast()" v-bind:class="{'selected':isSelected}"><img src="dist/static/images/spot-forecast.svg"></button>
  </div>
  </div>
  <form id="spotforecast" name="spotforecast" action="{{env.gokartService + '/spotforecast/html'}}" method="post" target="spotforecast">
      <input type="hidden" name="data" id="spotforecast_data">
  </form>
</template>

<style>
</style>

<script>
  import { ol,$,utils} from 'src/vendor.js'
  export default {
    data: function () {
      return {
        format:"html"
      }

    },
    // parts of the template to be computed live
    computed: {
      loading: function () { return this.$root.loading },
      map: function () { return this.$root.map },
      env: function () { return this.$root.env },
      active: function () { return this.$root.active },
      catalogue: function () { return this.$root.catalogue },
      annotations: function () { 
        return this.$root.$refs.app.$refs.annotations 
      },
      mapControl:function() {
        if (!this._controller) {
            this._controller = new ol.control.Control({
                element: $('#spotforecast').get(0),
        	target: $('#external-controls').get(0)
            })
        }
        return this._controller
      },
      isSelected:function() {
        return this.annotations.tool === this._spotforecastTool
      },
    },
    watch:{
      isSelected:function(newValue,oldValue) {
        if (newValue) {
            this._overlay.setMap(this.map.olmap)
        } else {
            this._overlay.setMap(null)
        }
      }
    },
    // methods callable from inside the template
    methods: {
      toggleSpotForecast: function () {
        if (!this._spotforecastTool || this.annotations.tool === this._spotforecastTool) {
            this.annotations.setTool('Pan')
        } else  {
            this.annotations.setTool(this._spotforecastTool)
        }
      },
      getSpotforecast:function(coordinate) {
        var vm = this
        var requestData = {
            point:coordinate,
            no_data:"-",
            datetime_pattern:"%d/%m/%Y %H:%M:%S",
            forecasts:[
                {
                    times:utils.getDatetimes(["00:00:00","06:00:00","12:00:00","18:00:00"],16,2).map(function(dt) {return dt.format("YYYY-MM-DD HH:mm:ss")}),
                    pattern:"%Y-%m-%d %H:%M:%S",
                    style:"text-align:center",
                    datasources:[
                        {
                            workspace:"bom",
                            id:"IDW71000_WA_T_SFC",
                            pattern:"{:-.2f}",
                            style:"text-align:right",
                        },
                        {
                            workspace:"bom",
                            id:"IDW71001_WA_Td_SFC",
                            pattern:"{:-.2f}",
                            style:"text-align:right",
                        },
                        {
                            group:"test",
                            datasources:[
                                {
                                    workspace:"bom",
                                    id:"IDW71002_WA_MaxT_SFC",
                                    pattern:"{:-.2f}",
                                    style:"text-align:right",
                                },
                                {
                                    workspace:"bom",
                                    id:"IDW71003_WA_MinT_SFC",
                                    pattern:"{:-.2f}",
                                    style:"text-align:right",
                                }
                            ]

                        }
                    ]
                }
            ]
        }
        if (this.format === "json") {
            $.ajax({
                url:vm.env.gokartService + "/spotforecast/json",
                dataType:"json",
                data:{
                    data:JSON.stringify(requestData),
                },
                method:"POST",
                success: function (response, stat, xhr) {
                    console.log(response)
                },
                error: function (xhr,status,message) {
                    alert(xhr.status + " : " + (xhr.responseText || message))
                },
                xhrFields: {
                    withCredentials: true
                }
            })
        } else {
            $("#spotforecast_data").val(JSON.stringify(requestData))
            utils.submitForm("spotforecast")
        }
        
      },
    },
    ready: function () {
      var vm = this
      var spotforecastStatus = vm.loading.register("spotforecast","BOM Spot Forecast Component")

      spotforecastStatus.phaseBegin("initialize",100,"Initialize")
      var map = this.$root.map

      this._features = new ol.Collection()
      this._features.on("add",function(event){
        vm.getSpotforecast(event.element.getGeometry().getCoordinates())
      })
      this._style =  new ol.style.Style({
          image: new ol.style.Icon({
            src: "dist/static/images/pin.svg",
            anchorOrigin:"bottom-left",
            anchorXUnits:"pixels",
            anchorYUnits:"pixels",
            anchor:[8,0]
          })
      })
      this._source = new ol.source.Vector({
          features:this._features
      })
      this._overlay = new ol.layer.Vector({
          source: this._source,
          style: this._style
      })

      //initialize the overlay and interactions
      var spotforecastInter = new ol.interaction.Draw({
          source: this._source,
          type: 'Point',
          style: this._style
      });

      spotforecastInter.on('drawend',function(){
        vm._features.clear()
      }, this)

      this._spotforecastTool = {
        name: 'SpotForecast',
        interactions:[
            spotforecastInter
        ]
      }

      this.annotations.tools.push(this._spotforecastTool)

      spotforecastStatus.phaseEnd("initialize")

    }
  }
</script>
