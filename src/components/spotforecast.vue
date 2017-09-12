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
        format:"html",
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
            options: {
                title:"Spot Fire Weather 4 Day Outlook for (" + Math.round(coordinate[0] * 10000) / 10000 + "," + Math.round(coordinate[1] * 10000) / 10000 + ")",
            },
            forecasts:[
                {
                    times:utils.getDatetimes(["09:00:00","12:00:00","15:00:00","18:00:00","21:00:00"],20,1).map(function(dt) {return dt.format("YYYY-MM-DD HH:mm:ss")}),
                    options:{
                    },
                    datasources:[
                        {
                            workspace:"bom",
                            id:"IDW71000_WA_T_SFC",
                            options:{
                                title:"Temp<br>(C)<br>({refresh_time})",
                            }
                        },
                        {
                            workspace:"bom",
                            id:"IDW71001_WA_Td_SFC",
                            options:{
                                title:"Dewpt<br>(C)<br>({refresh_time})",
                            }
                        },
                        {
                            workspace:"bom",
                            id:"IDW71018_WA_RH_SFC",
                            options:{
                                title:"RH<br>(%)<br>({refresh_time})",
                            }
                        },
                        {
                            group:"10m Wind (km/h)",
                            datasources:[
                                {
                                    workspace:"bom",
                                    id:"IDW71089_WA_Wind_Dir_SFC",
                                    options:{
                                        title:"Dir<br>({refresh_time})",
                                    }
                                },
                                {
                                    workspace:"bom",
                                    id:"IDW71071_WA_WindMagKmh_SFC",
                                    options:{
                                        title:"Speed<br>({refresh_time})",
                                    }
                                },
                                {
                                    workspace:"bom",
                                    id:"IDW71072_WA_WindGustKmh_SFC",
                                    options:{
                                        title:"Gust<br>({refresh_time})",
                                    }
                                }
                            ]

                        },
                        {
                            workspace:"bom",
                            id:"IDW71127_WA_DF_SFC",
                            options:{
                                title:"DF<br>({refresh_time})",
                            }
                        },
                        {
                            workspace:"bom",
                            id:"IDW71139_WA_Curing_SFC",
                            options:{
                                title:"Curing<br>({refresh_time})",
                            }
                        },
                        {
                            workspace:"bom",
                            id:"IDW71117_WA_FFDI_SFC",
                            options:{
                                title:"FFDI<br>({refresh_time})",
                            }
                        },
                        {
                            workspace:"bom",
                            id:"IDW71122_WA_GFDI_SFC",
                            options:{
                                title:"GFDI<br>({refresh_time})",
                            }
                        },
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
            utils.submitForm("spotforecast",{width: (screen.width > 1890)?1890:screen.width, height:(screen.height > 1060)?1060:screen.height})
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
