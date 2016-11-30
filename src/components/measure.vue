<template>
  <div id="map-measure" class="ol-selectable ol-control">
      <button type="button" title="Measure length" @click="toggleMeasure('MeasureLength')" v-bind:class="{'selected':isMeasureLength}"><img src="dist/static/images/measure-length.svg"></button>
      <button type="button" title="Measure area" @click="toggleMeasure('MeasureArea')" v-bind:class="{'selected':isMeasureArea}"><img src="dist/static/images/measure-area.svg"></button>
      <button type="button" title="Clear measurements" v-show="showClear" @click="clearMeasure()"><i class="fa fa-trash"></i></button>
  </div>
  <div id="map-measure-tooltips"></div>
</template>

<style>
  .feature-icon {
    width: 24px;
    height: 24px;
  }
</style>

<script>
  import { ol,$ } from 'src/vendor.js'
  export default {
    store: ['settings'],
    data: function () {
      return {
      }
    },
    // parts of the template to be computed live
    computed: {
      loading: function () { return this.$root.loading },
      map: function () { return this.$root.map },
      active: function () { return this.$root.active },
      annotations: function () { 
        return this.$root.$refs.app.$refs.annotations 
      },
      measureType: function() {
        if (["MeasureLength","MeasureArea"].indexOf(this.annotations.tool.name) >= 0) {
            return this.annotations.tool.name
        } else {
            return ""
        }
      },
      showClear: function () {
        return this.measureType != "" && this.features.getLength()
      },
      isMeasureLength: function () {
        return this.measureType == "MeasureLength"
      },
      isMeasureArea:function() {
        return this.measureType == "MeasureArea"
      },
      mapControl:function() {
        if (!this._controller) {
            this._controller = new ol.control.Control({
              element: $('#map-measure').get(0),
        	  target: $('#external-controls').get(0)
            })
        }
        return this._controller
      },
      lengthUnit: function() {
        return this.settings.lengthUnit
      },
      areaUnit: function() {
        return this.settings.areaUnit
      },
      measureAnnotation:function() {
        return this.settings.measureAnnotation
      }
    },
    watch:{
        lengthUnit:function(newValue,oldValue) {
            var vm = this
            var geom = null
            this.features.forEach(function(feature) {
                var tooltipElement = feature['tooltipElement']
                if (!tooltipElement) return
                var element = $(tooltipElement).find(".length")
                if (element.length > 0) {
                    element.html(vm.formatLength(feature))
                }
            })

            this.annotations.features.forEach(function(feature){
                var tooltipElement = feature['tooltipElement']
                if (!tooltipElement) return
                var element = $(tooltipElement).find(".length")
                if (element.length > 0) {
                    element.html(vm.formatLength(feature))
                }
            })
        },
        areaUnit:function(newValue,oldValue) {
            var vm = this
            this.features.forEach(function(feature) {
                var tooltipElement = feature['tooltipElement']
                if (!tooltipElement) return
                var element = $(tooltipElement).find(".area")
                if (element.length > 0) {
                    element.html(vm.formatArea(feature))
                }
            })

            this.annotations.features.forEach(function(feature){
                var tooltipElement = feature['tooltipElement']
                if (!tooltipElement) return
                var element = $(tooltipElement).find(".area")
                if (element.length > 0) {
                    element.html(vm.formatArea(feature))
                }
            })
        },
        measureAnnotation:function(newValue,oldValue) {
            if (this.map.getMapLayer("annotations") && !this.active.isHidden(this.map.getMapLayer("annotations"))) {
                this.enableAnnotationMeasurement(newValue)
            }
        },
        measureType:function(newVal,oldVal){
            if (newVal == "") {
                //switchoff
                if (this.overlay) {
                    this.overlay.setMap(null)
                }
                if (this.drawingFeature) {
                    this.removeTooltip(this.drawingFeature)
                    this.drawingFeature = null
                }
                //hidden measuretips
                this.showTooltip(this.features,false)
            } else if (oldVal == ""){
                //switchon
                this.overlay.setMap(this.$root.map.olmap)
                this.showTooltip(this.features,true)
            } else {
                //switch measure type
                if (this.drawingFeature) {
                    this.removeTooltip(this.drawingFeature)
                    this.drawingFeature = null
                }
            }
        },
    },
    // methods callable from inside the template
    methods: {
      enableAnnotationMeasurement:function(enable) {
        var vm = this
        if(enable) {
            //enable
            $.each(this.annotations.features.getArray(),function(index,feature){
                var tool = vm.annotations.getTool(feature.get('toolName'))
                if (!tool) {return}
                if (!tool.measureLength && !tool.measureArea) {return}
                if (feature.tooltip) {
                    if (feature.tooltip.getMap()) {
                        //already enabled, return
                        return false
                    } else {
                        vm.$root.map.olmap.addOverlay(feature.tooltip)
                        feature.tooltip.setOffset([0, -7])
                    }
                } else {
                    vm.createTooltip(feature,tool.measureLength,tool.measureArea)
                    vm.measuring(feature,tool.measureLength,tool.measureArea)
                    vm.endMeasure(feature)
                }
            })
        } else {
            //disable
            this.showTooltip(this.annotations.features,false)
        }
      },
      toggleMeasure: function (type) {
        if (this.measureType == type) {
            this.annotations.setTool('Pan')
        } else  {
            this.annotations.setTool(type)
        }
      },
      clearMeasure:function() {
        var vm = this
        if (this.features) {
            this.features.clear()
        }
        if (this.drawingFeature) {
            this.removeTooltip(this.drawingFeature)
            this.drawingFeature = null
        }
        if (this.measureType) {
            //readd the interact to remove the drawing features.
            $.each(this.annotations.tool.interactions,function(index,interact){
                vm.map.olmap.removeInteraction(interact)       
            })
            $.each(this.annotations.tool.interactions,function(index,interact){
                vm.map.olmap.addInteraction(interact)       
            })
        }
      },
      startMeasureFunc:function(measureLength,measureArea){
        var vm = this
        return function(evt) {
            //console.log("Start measure")
            // set feature
            vm.drawingFeature = evt.feature

            vm.createTooltip(vm.drawingFeature,measureLength,measureArea)

            vm.geometryChangeHandler = vm.drawingFeature.getGeometry().on('change', function(feature,measureLength,measureArea){
                return function(evg) {
                    vm.measuring(feature,measureLength,measureArea,true)
                }
            }(vm.drawingFeature,measureLength,measureArea))
        }
      },
      measuring: function(feature,measureLength,measureArea,drawing) {
        var geom = feature.getGeometry()
        var tooltipCoord = null
        if (geom instanceof ol.geom.Polygon) {
            tooltipCoord = geom.getInteriorPoint().getCoordinates()
        } else if (geom instanceof ol.geom.LineString) {
            tooltipCoord = geom.getLastCoordinate()
        }
        if (tooltipCoord) {
            if (measureLength) {
                $(feature.tooltipElement).find(".length").html(this.formatLength(feature,drawing))
            }
            if (measureArea) {
                $(feature.tooltipElement).find(".area").html(this.formatArea(feature,drawing))
            }
            feature.tooltip.setPosition(tooltipCoord)
        }
      },
      endMeasure: function(feature) {
        //console.log("End measure")
        feature.tooltipElement.className = 'tooltip-measure tooltip-measured'
        feature.tooltip.setOffset([0, -7])
      },
      showTooltip:function(features,show) {
        var vm = this
        if (features) {
            $.each(features.getArray(),function(index,f){
                if (f['tooltip']) {
                    if (show) {
                        if (f['tooltip'].getMap()) {
                            //already show,return
                            return false
                        } else {
                            vm.$root.map.olmap.addOverlay(f['tooltip'])
                        }
                    } else {
                        if (f['tooltip'].getMap()) {
                            vm.$root.map.olmap.removeOverlay(f['tooltip'])
                        } else {
                            //already removed, return
                            return false
                        }
                    }
                }
            })
        }
      },
      createTooltip: function (feature,measureLength,measureArea) {
        if (!feature.tooltipElement) {
            //console.log("Create measure tooltip element")
            var measureTooltipElement = $("<div></div>")
            if (measureLength) {
                measureTooltipElement.append("<div class='length'></div>")
            }
            if (measureArea) {
                measureTooltipElement.append("<div class='area'></div>")
            }
            measureTooltipElement.addClass('tooltip-measure tooltip-measuring')

            $("#map-measure-tooltips").append(measureTooltipElement)
            feature['tooltipElement'] = measureTooltipElement.get(0)
        }
        if (!feature.tooltip) {
            //console.log("Create measure tooltip overlay")
            var measureTooltip = new ol.Overlay({
              element: feature.tooltipElement,
              offset: [0, -15],
              stopEvent:false,
              positioning: 'bottom-center'
            })
            this.$root.map.olmap.addOverlay(measureTooltip)
            feature['tooltip'] = measureTooltip
        }
      },
      removeTooltip: function (feature,removeTooltipElement) {
        removeTooltipElement = removeTooltipElement === undefined?true:removeTooltipElement
        if (feature.tooltip) {
            if (feature.tooltip.getMap()) {
                this.$root.map.olmap.removeOverlay(feature.tooltip)
            }
            delete feature.tooltip
        }
        if (removeTooltipElement && feature.tooltipElement) {
            feature.tooltipElement.parentNode.removeChild(feature.tooltipElement)
            delete feature.tooltipElement
        }
      },
      getLength: function(coordinates) {
        var length = 0
        var sourceProj = this.$root.map.olmap.getView().getProjection()
        for (var i = 0, ii = coordinates.length - 1; i < ii; ++i) {
          var c1 = ol.proj.transform(coordinates[i], sourceProj, 'EPSG:4326')
          var c2 = ol.proj.transform(coordinates[i + 1], sourceProj, 'EPSG:4326')
          length += this.wgs84Sphere.haversineDistance(c1, c2)
        }
        return length
      },
      formatLength : function(feature,drawing) {
        var length = drawing?undefined:feature.get('length')
        if (length === undefined) {
            var geom = feature.getGeometry()
            if (geom instanceof ol.geom.LineString) {
                length = this.getLength(geom.getCoordinates())
            } else if(geom instanceof ol.geom.Polygon) {
                length = this.getLength(geom.getLinearRing(0).getCoordinates())
            }
            if (length) {
                feature.set('length',length,true)
            }
        }
        var output = null
        if (this.lengthUnit === "nm") {
              output = (Math.round( (length * 250) / (10 * 463) ) / 100) +
                  ' ' + 'nm'
        } else if (this.lengthUnit === "mile") {
              output = (Math.round( (length * 15625) / (10 * 25146) ) / 100) +
                  ' ' + 'mile'
        } else {
            if (length > 100) {
              output = (Math.round(length / 10) / 100) +
                  ' ' + 'km'
            } else {
              output = (Math.round(length * 100) / 100) +
                  ' ' + 'm'
            }
        }
        return output
      },
      formatArea : function(feature,drawing) {
        var vm = this
        var area = drawing?undefined:feature.get('area')
        if (area === undefined) {
            var geom = feature.getGeometry()
            /*
            var sourceProj = this.$root.map.olmap.getView().getProjection()
            var geom = (polygon.clone().transform(
                sourceProj, 'EPSG:4326'))
            */
            $.each(geom.getLinearRings(),function(index,linearRing){
                if (index === 0) {
                    area = Math.abs(vm.wgs84Sphere.geodesicArea(linearRing.getCoordinates()))
                } else {
                    area -= Math.abs(vm.wgs84Sphere.geodesicArea(linearRing.getCoordinates()))
                }
            })
            feature.set('area',area,true)
        }
        var output = null
        if (this.areaUnit === "ha") {
            if (area > 10000) {
              // large than 1 hectare
              output = Math.round(area / 10000) + 
                  ' ' + 'ha'
            } else {
              //less than 1 hectare
              output = (Math.round(area / 10000 * 100) / 100) +
                  ' ' + 'ha'
            }
        } else {
            if (area > 10000) {
              output = (Math.round(area / 1000000 * 100) / 100) +
                  ' ' + 'km<sup>2</sup>'
            } else {
              output = (Math.round(area * 100) / 100) +
                  ' ' + 'm<sup>2</sup>'
            }
        }
        return output
      },
    },
    ready: function () {
      var vm = this
      var measureStatus = vm.loading.register("measure","Measurement Component","Initialize")
      var map = this.$root.map
      //initialize the overlay and interactions
      this.features = new ol.Collection()
      this.features.on("remove",function(event){
          if (event.element['tooltipElement']) {
              //console.log("Remove measured tooltip")
              vm.removeTooltip(event.element)
          }
      })
      this.style =  new ol.style.Style({
          fill: new ol.style.Fill({
            color: 'rgba(0,0,0, 0.25)'
          }),
          stroke: new ol.style.Stroke({
            color: 'rgba(0, 0, 0, 0.5)',
            lineDash: [10, 10],
            width: 2
          }),
          image: new ol.style.Circle({
            radius: 5,
            fill: new ol.style.Fill({
              color: 'rgb(0, 153, 255)'
            })
          })
      })
      this.source = new ol.source.Vector({
          features:this.features
      })
      this.overlay = new ol.layer.Vector({
          source: this.source,
          style: this.style
      })

      var measureLengthInter = new ol.interaction.Draw({
              source: this.source,
              type: 'LineString',
              style: this.style
            });

      var drawendHandler = function(ev) {
        vm.endMeasure(ev.feature)
        vm.drawingFeature = null
      }
      measureLengthInter.on('drawstart',this.startMeasureFunc(true,false),this)
      measureLengthInter.on('drawend',drawendHandler, this)

      var measureLength = {
        name: 'MeasureLength',
        interactions:[
            //map.dragPanInter,
            //map.doubleClickZoomInter,
            //map.keyboardPanInter,
            //map.keyboardZoomInter,
            measureLengthInter,
        ]
      }
      this.annotations.tools.push(measureLength)

      var measureAreaInter = new ol.interaction.Draw({
              source: this.source,
              type: 'Polygon',
              style: this.style
            });
      measureAreaInter.on('drawstart',this.startMeasureFunc(true,true),this)
      measureAreaInter.on('drawend',drawendHandler, this)

      var measureArea = {
        name: 'MeasureArea',
        interactions:[
            //map.dragPanInter,
            //map.doubleClickZoomInter,
            //map.keyboardPanInter,
            //map.keyboardZoomInter,
            measureAreaInter
        ]
      }

      this.annotations.features.on("remove",function(ev){
        var feature = ev.element
        if (feature.tooltip) {
            vm.removeTooltip(feature)
        }
      })

      this.annotations.features.on("add",function(ev){
        if (vm.map.getMapLayer("annotations")) {
            var feature = ev.element
            var tool = vm.annotations.getTool(feature.get('toolName'))
            if (!tool) {return}
            if (tool.measureLength || tool.measureArea) {
                if (vm.measureAnnotation) {
                    vm.createTooltip(feature,tool.measureLength,tool.measureArea)
                    vm.measuring(feature,tool.measureLength,tool.measureArea)
                    vm.endMeasure(feature)
                }
            }
        }

      })
      var featuresChanged = function(ev){
        ev.features.forEach(function(feature) {
            var tool = vm.annotations.getTool(feature.get('toolName'))
            if (!tool) {return}
            if (tool.measureLength) {
                feature.unset('length',true)
            }
            if (tool.measureArea) {
                feature.unset('area',true)
            }
            if (feature.tooltip) {
                if (vm.measureAnnotation) {
                    vm.measuring(feature,tool.measureLength,tool.measureArea)
                    vm.endMeasure(feature)
                    //console.log("Recalculated")
                } else {
                    vm.removeTooltip(feature,false)
                    //console.log("Remove tooltip because feature is changed")
                }
            }
        })
      }

      this.annotations.ui.modifyInter.on("featuresmodified",featuresChanged)
      this.annotations.ui.translateInter.on("translateend",featuresChanged)
      this.annotations.tools.push(measureArea)

      this.wgs84Sphere = new ol.Sphere(6378137);

      measureStatus.wait(30,"Listen 'gk-init' event")
      this.$on("gk-init",function() {
          measureStatus.progress(80,"Process 'gk-init' event")
        
          //add measure tooltips when adding annotation layer and measureAnnotation is true
          var changeOpacityHandler = function(ev) {
            if (!vm.measureAnnotation) { return }
            if (ev.target.get(ev.key) === 0) {
                vm.enableAnnotationMeasurement(false)
            } else if(ev.oldValue === 0) {
                vm.enableAnnotationMeasurement(true)
            }
          }

          if (vm.map.getMapLayer("annotations")) {
            vm.map.getMapLayer("annotations").on("change:opacity",changeOpacityHandler)
          }
          vm.map.olmap.getLayers().on("add",function(ev){
              if (ev.element.get('id') === "annotations") {
                  if (vm.measureAnnotation) {
                      vm.enableAnnotationMeasurement(true)
                  }
                  ev.element.on("change:opacity",changeOpacityHandler)
              }
          })

          //remove measure tooltips when removing annotation layer
          vm.map.olmap.getLayers().on("remove",function(ev){
              if (ev.element.get('id') === "annotations") {
                  if (vm.measureAnnotation) {
                      vm.enableAnnotationMeasurement(false)
                  }
              }
          })
          measureStatus.end()
      })
    }
  }
</script>
