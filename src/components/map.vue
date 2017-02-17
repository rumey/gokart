<template>
  <div class="map" id="map" tabindex="0">
    <gk-info v-ref:info></gk-info>
  </div>
  <gk-scales v-ref:scales></gk-scales>
  <gk-search v-ref:search></gk-search>
  <gk-measure v-ref:measure></gk-measure>
</template>
<style>
    .ol-custom-overviewmap,
    .ol-custom-overviewmap.ol-uncollapsible {
        bottom: 0;
        left: auto;
        right: 0;
        top: auto;
    }

    .ol-custom-overviewmap:not(.ol-collapsed)  {
       border: 1px solid black;
    }

    .ol-custom-overviewmap .ol-overviewmap-map {
        border: none;
        width: 300px;
        height:150px;
    }

    .ol-custom-overviewmap .ol-overviewmap-box {
        border: 2px solid red;
    }

    .ol-custom-overviewmap:not(.ol-collapsed) button{
        bottom: auto;
        left: auto;
        right: 1px;
        top: 1px;
    }

</style>

<script>
  import { $, ol, proj4, moment,interact } from 'src/vendor.js'
  import gkInfo from './info.vue'
  import gkScales from './scales.vue'
  import gkSearch from './search.vue'
  import gkMeasure from './measure.vue'
  export default {
    store: {
        defaultWMTSSrc:'defaultWMTSSrc', 
        defaultWFSSrc:'defaultWFSSrc', 
        gokartService:'gokartService', 
        fixedScales:'fixedScales', 
        resolutions:'resolutions', 
        matrixSets:'matrixSets', 
        dpmm:'dpmm', 
        view:'view',
        displayGraticule:'settings.graticule',
        displayResolution:'displayResolution'
    },
    components: { gkInfo, gkScales, gkSearch, gkMeasure },
    data: function () {
      return {
        scale: 0,
        mapControls:{},
        graticule: new ol.LabelGraticule(),
        dragPanInter: new ol.interaction.DragPan({
          condition: function (mapBrowserEvent) {
            if (mapBrowserEvent.pointerEvent && (mapBrowserEvent.pointerEvent.button === 1)) {
              return false
            }
            return ol.events.condition.noModifierKeys(mapBrowserEvent)
          }
        }),
        doubleClickZoomInter: new ol.interaction.DoubleClickZoom(),
        keyboardPanInter: new ol.interaction.KeyboardPan(),
        keyboardZoomInter: new ol.interaction.KeyboardZoom(),
        middleDragPanInter: new ol.interaction.DragPan({
          condition: function (mapBrowserEvent) {
            if (mapBrowserEvent.pointerEvent && (mapBrowserEvent.pointerEvent.button === 1)) {
              mapBrowserEvent.preventDefault()
              return true
            }
            return false
          }
        })
      }
    },
    // parts of the template to be computed live
    computed: {
      loading: function () { return this.$root.loading },
      annotations: function () { return this.$root.annotations    },
      active: function () { return this.$root.active    },
      measure: function () { return this.$root.measure    },
      // because the viewport size changes when the tab pane opens, don't cache the map width and height
      width: {
        cache: false,
        get: function get () {
          return $("#map").width()
        }
      },
      height: {
        cache: false,
        get: function get () {
          return $("#map").height()
        }
      },
      extent: function() {
        return this.olmap.getView().calculateExtent(this.olmap.getSize())
      },
      resolution:function() {
        return this.olmap.getView().getResolution()
      }
    },
    watch: {
      displayGraticule:function(newValue,oldValue) {
        this.showGraticule(newValue)
      }
    },
    // methods callable from inside the template
    methods: {
      clearFeatureProperties:function(feature){
          $.each(feature.getKeys(),function(index,key){
              if (key !== feature.getGeometryName()) {
                  feature.unset(key)
              }
          })
      },
      isGeometryEqual:function(geom1,geom2){
        if ( !geom1 && !geom2 ) {
            return true
        } else if ( (geom1 && 1 || 0) + (geom2 && 1 || 0) === 1) {
            return false
        } else if (geom1 instanceof ol.geom.Point && geom2 instanceof ol.geom.Point) {
            return geom1.getCoordinates()[0] === geom2.getCoordinates()[0] && geom1.getCoordinates()[1] === geom2.getCoordinates()[1]
        } else if (geom1 instanceof ol.geom.LineString && geom2 instanceof ol.geom.LineString) {
            var coords1 = geom1.getCoordinates()
            var coords2 = geom2.getCoordinates()
            if (coords1.length !== coords2.length) return false
            var i2 = coords2.findIndex(function(c) { return c[0] === coords1[0][0] && c[1] === coords1[0][1]})
            if (i2 < 0) {return false}
            for( i1 = 1,i2 = i2 + 1;i1 < coords1.length;i1++,i2 = (i2 + 1) % coords2.length) {
                if (coords1[i1][0] !== coords2[i2][0] || coords1[i1][1] !== coords2[i2][1]) {return false}
            }
            return true
        } else if (geom1 instanceof ol.geom.LinearRing && geom2 instanceof ol.geom.LinearRing) {
            var coords1 = geom1.getCoordinates()
            var coords2 = geom2.getCoordinates()
            if (coords1.length !== coords2.length) return false
            var i2 = coords2.findIndex(function(c) { return c[0] === coords1[0][0] && c[1] === coords1[0][1]})
            if (i2 < 0) {return false}
            for( i1 = 1,i2 = i2 + 1;i1 < coords1.length - 1;i1++,i2 = (i2 + 1) % (coords2.length - 1)) {
                if (coords1[i1][0] !== coords2[i2][0] || coords1[i1][1] !== coords2[i2][1]) {return false}
            }
            return true
        } else if(geom1 instanceof ol.geom.Polygon && geom2 instanceof ol.geom.Polygon) {
            var vm = this
            var rings1 = geom1.getLinearRings()
            var rings2 = geom2.getLinearRings()
            if (rings1.length != rings2.length) {return false}
            var foundIndexes = []
            for(i = 0;i < rings1.length;i++) {
                if (!rings2.find(function(r2,index) {
                    if (foundIndexes.indexOf(index) >= 0) {
                        return false
                    } else if(vm.isGeometryEqual(r2,rings1[i])) {
                        foundIndexes.push(index)
                        return true
                    } else {
                        return false
                    }
                })) {
                    return false
                }
            }
            return true
        } else if(geom1 instanceof ol.geom.MultiLineString && geom2 instanceof ol.geom.MultiLineString) {
            var vm = this
            var lines1 = geom1.getLineStrings()
            var lines2 = geom2.getLineStrings()
            if (lines1.length != lines2.length) {return false}
            var foundIndexes = []
            for(i = 0;i < lines1.length;i++) {
                if (!lines2.find(function(l2,index) {
                    if (foundIndexes.indexOf(index) >= 0) {
                        return false
                    } else if(vm.isGeometryEqual(l2,lines1[i])) {
                        foundIndexes.push(index)
                        return true
                    } else {
                        return false
                    }
                })) {
                    return false
                }
            }
            return true
        } else if(geom1 instanceof ol.geom.MultiPolygon && geom2 instanceof ol.geom.MultiPolygon) {
            var vm = this
            var polygons1 = geom1.getPolygons()
            var polygons2 = geom2.getPolygons()
            if (polygons1.length != polygons2.length) {return false}
            var foundIndexes = []
            for(i = 0;i < polygons1.length;i++) {
                if (!polygons2.find(function(p2,index) {
                    if (foundIndexes.indexOf(index) >= 0) {
                        return false
                    } else if(vm.isGeometryEqual(p2,polygons1[i])) {
                        foundIndexes.push(index)
                        return true
                    } else {
                        return false
                    }
                })) {
                    return false
                }
            }
            return true
        } else if(geom1 instanceof ol.geom.GeometryCollection && geom2 instanceof ol.geom.GeometryCollection) {
            var vm = this
            var geometries1 = geom1.getGeometriesArray()
            var geometries2 = geom2.getGeometriesArray()
            if (geometries1.length != geometries2.length) {return false}
            var foundIndexes = []
            for(i = 0;i < geometries1.length;i++) {
                if (!geometries2.find(function(p2,index) {
                    if (foundIndexes.indexOf(index) >= 0) {
                        return false
                    } else if(vm.isGeometryEqual(p2,geometries1[i])) {
                        foundIndexes.push(index)
                        return true
                    } else {
                        return false
                    }
                })) {
                    return false
                }
            }
            return true
        }
        return false
      },
      showGraticule: function (show) {
        this.graticule.setMap(show?this.olmap:null)
      },
      //enable or disable a control
      getControl:function(controlName) {
        var control = this.mapControls[controlName]
        return control?control.controls:undefined
      },
      isControlEnabled:function(controlName) {
        var control = this.mapControls[controlName]
        return control?control.enabled:undefined
      },
      enableControl:function(controlName,enable) {
        var vm = this
        var control = this.mapControls[controlName]
        if (!control || control.enabled === enable) {
            //already enabled or disabled
            return
        }
        if (control.controls) {
            if (control.preenable) {
                control.preenable.call(control,enable)
            }
            if (Array.isArray(control.controls)) {
                $.each(control.controls,function(index,c){
                    if (enable) {
                        vm.olmap.addControl(c)
                    } else {
                        vm.olmap.removeControl(c)
                    }
                })
            } else {
                if (enable) {
                    vm.olmap.addControl(control.controls)
                } else {
                    vm.olmap.removeControl(control.controls)
                }
            }
            if (control.postenable) {
                control.postenable.call(control,enable)
            }
        }
        control.enabled = enable
      },
      editResource: function(event) {
        var target = (event.target.nodeName == "A")?event.target:event.target.parentNode;
        if (env.appType == "cordova") {
            window.open(target.href,"_system");
        } else {
            window.open(target.href,target.target);
        }
      },
      tintSVG: function(svgstring, tints) {
        tints.forEach(function(colour) {
          svgstring = svgstring.split(colour[0]).join(colour[1])
        })
        return svgstring
      },
      //keys:[url,tint?,dims?]
      getBlob: function(feature, keys,tintSettings,callback) {
        // method to precache SVGs as raster (PNGs)
        // workaround for Firefox missing the SurfaceCache when blitting to canvas
        // returns a url or undefined if svg isn't baked yet
        var vm = this
        var tool = feature.get('toolName')?vm.annotations.getTool(feature.get('toolName')):{}
        var key = keys.map(function(k) {
          return vm.annotations.getStyleProperty(feature,k,'default',tool)
        }).join(";")
        if (this.svgBlobs[key]) {
          return this.svgBlobs[key]
        } else if (this.jobs[key]) {
          vm.jobs[key].then(function(){
                feature.changed()
                if (callback) {callback()}
          })
        } else {
          var dimsKey = (keys.length >= 3)?keys[2]:'dims'
          var tintKey = (keys.length >= 2)?keys[1]:'tint'

          var dims = tool[dimsKey] || [48, 48]
          var tint = vm.annotations.getStyleProperty(feature,tintKey,'default',tool)
          if (!Array.isArray(tint)) {
              //tint is a named tint,get the tint setting from tints object
              tint = (tintSettings && tintSettings[tint])?tintSettings[tint]:[]
          }
          var url = vm.annotations.getStyleProperty(feature,keys[0],null,tool)
          if (typeof tint === "string") {
            //tint is not just a color replacement, is a totally different icon
            url = tint
            tint = []
          }
          vm.jobs[key] = new Promise(function(resolve, reject) {
            vm.addSVG(key, url, tint, dims, resolve)
          }).then(function() {
            feature.changed()
            delete vm.jobs[key]
            if (callback) {callback()}
          })
        }


      },
      addSVG: function(key, url, tint, dims, pResolve) {
        var vm = this
        tint = tint || []
        var draw = function() {
          if (typeof vm.svgBlobs[key] !== 'undefined') { pResolve() }
          // RACE CONDITION: MS edge inlines promises and callbacks!
          // we can't set vm.svgBlobs[key] to be the Promise, as
          // it's entirely possible for the whole thing to have been 
          // completed in the constructor before the svgBlobs array is even set
          //vm.svgBlobs[key] = ''
          var drawJob = new Promise(function(resolve, reject) {
            vm.drawSVG(key, vm.svgTemplates[url], tint, dims, resolve, reject)
          }).then(function() {
            pResolve()
          })
        }
        if (vm.svgTemplates[url]) {
          // render from loaded svg or queue render post load promise
          draw()
        } else if (vm.jobs[url]) {
            vm.jobs[url].then(function(){
                draw()
            })
        } else {
          vm.jobs[url] = new Promise(function (resolve, reject) { 
            // load svg
            //console.log('addSVG: Cache miss for '+key)
            var req = new window.XMLHttpRequest()
            req.withCredentials = true
            req.onload = function () {
              if (!this.responseText) {
                return
              }
              //console.log('addSVG: XHR returned for '+key)
              vm.svgTemplates[url] = this.responseText
              resolve()
            }
            req.onerror = function() {
              reject()
            }
            req.open('GET', url)
            req.send()
          }).then(function(){
            draw()
            delete vm.jobs[url]
          })
        }
      },
      drawSVG: function(key, svgstring, tints, dims, resolve, reject) {
        var vm = this
        //console.log('drawSVG: Cache miss for '+key)
        var canvas = $('<canvas>')
        canvas.attr({width: dims[0], height: dims[1]})
        canvas.drawImage({
          source: 'data:image/svg+xml;utf8,' + encodeURIComponent(vm.tintSVG(svgstring, tints)),
          fromCenter: false, x: 0, y: 0, width: dims[0], height: dims[1],
          load: function () {
            //console.log('drawSVG: Canvas drawn for '+key)
            canvas.get(0).toBlob(function (blob) {
              vm.svgBlobs[key] = window.URL.createObjectURL(blob)
              //console.log("drawSVG:" + key + "\t url = " + vm.svgBlobs[key])
              resolve()
            }, 'image/png')
          }
        })
      },
      //always using style array to simplify the logic
      cacheStyle: function(styleFunc, feature, keys,sufix) {
        var vm = this
        if (feature) {
            var key = keys.map(function(k) {
              return vm.annotations.getStyleProperty(feature,k,'default')
            }).join(";")
            key = sufix?(key + ";" + sufix):key
            var style = this.cachedStyles[key]
            if (style) { 
                return style 
            }
            style = styleFunc(feature)
            if (style) {
              style = (Array.isArray(style))?style:[style]
              this.cachedStyles[key] = style
              return style
            }
        }
        return new ol.layer.Vector().getStyleFunction()()
      },
      animate: function (args) {
        // pan from the current center
        this.olmap.getView().animate.apply(this.olmap.getView(),arguments)
      },
      // force OL to approximate a fixed scale (1:1K increments)
      setScale: function (scale) {
        while (Math.abs(this.getScale() - scale) > 0.001) {
          this.olmap.getView().setResolution(this.olmap.getView().getResolution() * scale / this.getScale())
        }
        this.scale = scale
      },
      // return the scale (1:1K increments)
      getScale: function () {
        var size = this.olmap.getSize()
        var center = this.getCenter()
        var extent = this.olmap.getView().calculateExtent(size)
        var distance = this.$root.wgs84Sphere.haversineDistance([extent[0], center[1]], center) * 2
        return distance * this.dpmm / size[0]
      },
      // get the fixed scale (1:1K increments) closest to specified or the current scale
      getFixedScale: function (scale) {
        scale = scale || this.getScale()
        var closest = null
        $.each(this.fixedScales, function () {
          if (closest === null || Math.abs(this - scale) < Math.abs(closest - scale)) {
            closest = this
          }
        })
        return closest
      },
      // generate a human-readable scale string
      getScaleString: function (scale) {
        if (Math.round(scale * 100) / 100 < 10.0) {
          return '1:' + (Math.round(scale * 1000)).toLocaleString()
        } else if (Math.round(scale * 100) / 100 >= 1000.0) {
          return '1:' + (Math.round(scale / 1000)).toLocaleString() + ' M'
        }
        return '1:' + (Math.round(scale)).toLocaleString() + ' K'
      },
      // get the decimal degrees representation of some EPSG:4326 coordinates
      getDeg: function(coords) {
        return coords[0].toFixed(5)+', '+coords[1].toFixed(5)
      },
      // get the DMS representation of some EPSG:4326 coordinates
      getDMS: function(coords) {
        return ol.coordinate.degreesToStringHDMS_(coords[0], 'EW', 1) + ', ' +
               ol.coordinate.degreesToStringHDMS_(coords[1], 'NS', 1)
      },
      // get the MGA representation of some EPSG:4326 coordinates
      getMGA: function(coords) {
        var mga = this.getMGARaw(coords)
        if (mga) {
            return 'MGA '+mga.mgaZone+' '+Math.round(mga.mgaEast)+'E '+Math.round(mga.mgaNorth)+'N'
        }
        return ''
      },
      getMGARaw: function(coords) {
        var results = {}
        if ((coords[0] >= 108) && (coords[0] < 114)) {
          results.mgaZone = 49
        } else if ((coords[0] >= 114) && (coords[0] < 120)) {
          results.mgaZone = 50
        } else if ((coords[0] >= 120) && (coords[0] < 126)) {
          results.mgaZone = 51
        } else if ((coords[0] >= 126) && (coords[0] < 132)) {
          results.mgaZone = 52
        } else if ((coords[0] >= 132) && (coords[0] < 138)) {
          results.mgaZone = 53
        } else if ((coords[0] >= 138) && (coords[0] < 144)) {
          results.mgaZone = 54
        } else if ((coords[0] >= 144) && (coords[0] < 150)) {
          results.mgaZone = 55
        } else if ((coords[0] >= 150) && (coords[0] < 156)) {
          results.mgaZone = 56
        } else {
          // fail if not in the bounding box for MGA
          return null
        }
        var newCoords = proj4('EPSG:4326', 'EPSG:283'+results.mgaZone).forward(coords)
        results.mgaEast = newCoords[0]
        results.mgaNorth = newCoords[1]
        return results
      },
      // parse a string containing coordinates in decimal or DMS format
      parseDMSString: function(dmsStr) {
        // https://regex101.com/r/kS2zR1/22
        var dmsRegex = /^\s*(-)?(\d+(?:\.\d+)?)[°º:d\s]?\s*(?:(\d+(?:\.\d+)?)['’‘′:m]\s*(?:(\d{1,2}(?:\.\d+)?)(?:"|″|’’|''|s)?)?)?\s*([NSEW])?[,:\s]+(-)?(\d+(?:\.\d+)?)[°º:d\s]?\s?(?:(\d+(?:\.\d+)?)['’‘′:m]\s*(?:(\d{1,2}(?:\.\d+)?)(?:"|″|’’|''|s)?)?)?\s*([NSEW])?$/gmi
        
        var groups = dmsRegex.exec(dmsStr)

        if (!groups) {
          return null
        }

        var dmsToDecimal = function(sign, deg, min, sec, dir) {
          var sg = sign ? -1 : 1
          sg = sg * (('wWsS'.indexOf(dir) >= 0) ? -1 : 1)
          var d = Number(deg)
          var m = min ? Number(min) : 0
          var s = sec ? Number(sec) : 0
          if (!(d >= 0 && d <= 180)) return null
          if (!(m >= 0 && m <= 60)) return null
          if (!(s >= 0 && s <= 60)) return null
          return sg*(d+(m/60)+(s/3600))
        }

        var coords = [
          dmsToDecimal(groups[1], groups[2], groups[3], groups[4], groups[5]),
          dmsToDecimal(groups[6], groups[7], groups[8], groups[9], groups[10])
        ]

        if ((!coords[0]) || (!coords[1])) {
          // one coordinate fails the sniff test
          return null
        }

        // order most people use is northing, easting (opposite of EPSG:4326)
        if (!groups[5] && !groups[10]) {
            coords = coords.reverse()
        // if only one is explicitly defined, swap if required
        } else if (!groups[5] || !groups[10]) {
          if (groups[5] && ('nNsS'.indexOf(groups[5]) >=0)) {
            coords = coords.reverse()
          } else if (groups[10] && ('wWeE'.indexOf(groups[10]) >=0)) {
            coords = coords.reverse()
          }
        // both are explicitly defined
        } else {
          // bomb out if someone describes two of the same
          if (('nNsS'.indexOf(groups[5]) >=0) && ('nNsS'.indexOf(groups[10]) >=0)) {
            return null
          } else if (('wWeE'.indexOf(groups[5]) >=0) && ('wWeE'.indexOf(groups[10]) >=0)) {
            return null
          }
          // swap if defined around the other way
          if (('nNsS'.indexOf(groups[5]) >=0) && ('wWeE'.indexOf(groups[10]) >=0)) {
            coords = coords.reverse()
          }
        }
        return coords 
      },
      // parse a string containing coordinates in MGA grid reference format
      // e.g. MGA 51 340000 6340000, MGA 51 340000mE 6340000mN, MGA 51 3406340
      parseMGAString: function(mgaStr) {
        // https://regex101.com/r/zY8dW4/2
        var mgaRegex = /(?:MGA|mga)\s*(49|50|51|52|53|54|55|56)\s*(\d{3,7})\s*[mM]{0,1}\s*([nNeE]{0,1})\s*,*\s*(\d{4,7})\s*[mM]{0,1}\s*([nNeE]{0,1})/gi
        var groups = mgaRegex.exec(mgaStr)
        
        if (!groups) {
          return null
        }

        var results = {
          mgaZone: parseInt(groups[1]),
          mgaEast: groups[2],
          mgaNorth: groups[4],
        }
        if ((groups[5] === "E") && (groups[3] === "N")) {
          results.mgaEast = groups[4]
          results.mgaNorth = groups[2]
        }
        if ((results.mgaEast.length === 3) && (results.mgaNorth.length === 4)) {
          results.mgaEast = results.mgaEast + '000'
          results.mgaNorth = results.mgaNorth + '000'
        } else if ((results.mgaEast.length === 6) && (results.mgaNorth.length === 7)) {
          // full length MGA coords
        } else {
          return null  // invalid MGA length
        }
        results.mgaEast = parseInt(results.mgaEast)
        results.mgaNorth = parseInt(results.mgaNorth)

        var coords = proj4('EPSG:283'+groups[1], 'EPSG:4326').forward([results.mgaEast, results.mgaNorth])
        results.coords = coords
        
        return results
      },
      // parse a string containing a FD Grid reference
      parseGridString: function(fdStr) {
        var fdRegex = /(FD|fd|PIL|pil)\s*([a-zA-Z]{1,2})\s*([0-9]{1,5})/gi
        var groups = fdRegex.exec(fdStr)
        if (!groups) {
          return null
        }
        var results = {
          gridType: groups[1].toUpperCase(),
          gridNorth: groups[2].toUpperCase(),
          gridEast: groups[3]
        }
        return results
      },

      getCenter: function() {
        return this.olmap.getView().getCenter();
      },

      // reusable tile loader hook to update a loading indicator
      tileLoaderHook: function (tileSource, tileLayer) {
        // number of tiles currently in flight
        var numLoadingTiles = 0
        // number of misses for the current set
        var badTiles = 0
        var tileLoader = tileSource.getTileLoadFunction()
        return function (tile, src) {
          if (numLoadingTiles === 0) {
            tileLayer.progress = 'loading'
            badTiles = 0
          }
          numLoadingTiles++
          var image = tile.getImage()
          // to hell with you, cross origin policy!
          image.crossOrigin = 'use-credentials'
          image.onload = function () {
            numLoadingTiles--
            if (numLoadingTiles === 0) {
              if (badTiles > 0) {
                tileLayer.progress = 'error'
              } else {
                tileLayer.progress = 'idle'
              }
            }
          }
          image.onerror = function () {
            badTiles++
            image.onload()
          }
          tileLoader(tile, src)
        }
      },
      setUrlTimestamp:function(tileSource,time) {
        if (!tileSource.setUrlTimestamp) {
          tileSource.setUrlTimestamp = function() {
              var originFunc = tileSource.getTileUrlFunction()
              return function(time) {
                  tileSource.setTileUrlFunction(function(tileCoord,pixelRatio,projection){
                      return originFunc(tileCoord,pixelRatio,projection) + "&time=" + time
                  },tileSource.getUrls()[0] + "?time=" + time)
              }
          }()
        }
        tileSource.setUrlTimestamp(time)
      },
      refreshLayerTile : function (tileLayer) {
        var vm = this
        //for timeline layer, layer's source will be changed when change timeline index
        if (!tileLayer.getSource().load) {
          tileLayer.getSource().load = function() {
            //console.log(((tileLayer.getSource().getLayer)?tileLayer.getSource().getLayer():tileLayer.getSource().getUrls()[0]) + " : Start refresh tiles")
            tileLayer.set('updated', moment().toLocaleString())
            // changing a URL forces a fetch + redraw
            vm.setUrlTimestamp(tileLayer.getSource(),moment.utc().unix())
            // empty the tile cache so other zoom levels are also reloaded
            tileLayer.getSource().tileCache.clear()
            vm.$root.active.refreshRevision += 1
          }
        }
        tileLayer.getSource().load()
      },
      // loader for layers with a "time" axis, e.g. live satellite imagery
      createTimelineLayer: function (options) {
        var vm = this
        options.params = $.extend({
          FORMAT: 'image/jpeg',
          SRS: 'EPSG:4326'
        }, options.params || {})

        // technically, we can specify a WMS source and a layer without
        // either the source URL or the layerID. which is good, because
        // we need to do that later on in a callback.
        var tileSource = new ol.source.TileWMS({
          params: options.params,
          tileGrid: new ol.tilegrid.TileGrid({
            extent: [-180, -90, 180, 90],
            resolutions: this.resolutions,
            tileSize: [1024, 1024]
          })
        })

        var tileLayer = new ol.layer.Tile({
          opacity: options.opacity || 1,
          source: tileSource
        })

        // hook the tile loading function to update progress indicator
        tileLayer.progress = ''
        tileSource.setTileLoadFunction(this.tileLoaderHook(tileSource, tileLayer))

        // hook to swap the tile layer when timeIndex changes
        tileLayer.on('propertychange', function (event) {
          if (event.key === 'timeIndex') {
            tileSource.updateParams({
              'layers': options.timeline[event.target.get(event.key)][1]
            })
          }
        })

        // helper function to update the time index
        options.updateTimeline = options.updateTimeline || function (layer,tileLayer) {
          // fetch the latest timestamp-to-layerID map from the source URL
          $.getJSON(layer.source, function (data) {
            tileLayer.set('updated', moment().toLocaleString())
            tileLayer.getSource().setUrls(data.servers)
            layer.timeline = data.layers.reverse()
            tileLayer.set('timeIndex', layer.timeIndex || layer.timeline.length - 1)
            vm.$root.active.update()
          })
        }

        options.updateTimeline(options,tileLayer)
        // if the "refresh" option is set, set a timer
        // to update the source
        if (options.refresh) {
          tileLayer.refresh = setInterval(function () {
            options.updateTimeline(options,tileLayer)
          }, options.refresh * 1000)
        }

        // set properties for use in layer selector
        tileLayer.set('name', options.name)
        tileLayer.set('id', options.id)
        return tileLayer
      },
      // loader for vector layers with hover querying
      createWFSLayer: function (options) {
        var vm = this
        var url = this.defaultWFSSrc  

        // default overridable params sent to the WFS source
        options.params = $.extend({
          version: '1.1.0',
          service: 'WFS',
          request: 'GetFeature',
          outputFormat: 'application/json',
          srsname: 'EPSG:4326',
          typename: options.id
        }, options.params || {})


        var vectorSource = new ol.source.Vector()
        var vector = new ol.layer.Vector({
          opacity: options.opacity || 1,
          source: vectorSource,
          style: options.style
        })
        vector.progress = ''

        vectorSource.retrieveFeatures = function (filter,onSuccess,onError) {
          var params = $.extend({},options.params)
          
          if (filter) {
            params.cql_filter = filter
          } else if (params.cql_filter) {
            delete params.cql_filter
          }
          $.ajax({
            url: url + '?' + $.param(params),
            success: function (response, stat, xhr) {
              var features = vm.$root.geojson.readFeatures(response)
              onSuccess(features)
            },
            error: function () {
                if (onError) {
                    onError(status,message)
                }
            },
            dataType: 'json',
            xhrFields: {
              withCredentials: true
            }
          })
        }

        vectorSource.loadSource = function (loadType,onSuccess) {
          if (options.cql_filter) {
            options.params.cql_filter = options.cql_filter
          } else if (options.params.cql_filter) {
            delete options.params.cql_filter
          }
          vm.$root.active.refreshRevision += 1
          vector.progress = 'loading'
          $.ajax({
            url: url + '?' + $.param(options.params),
            success: function (response, stat, xhr) {
              var features = vm.$root.geojson.readFeatures(response)
              var defaultOnload = function(loadType,source,features) {
                  source.clear(true)
                  source.addFeatures(features)
              }
              if (options.onload) {
                options.onload(loadType,vectorSource,features,defaultOnload)
              } else {
                defaultOnload(loadType,vectorSource,features)
              }
              vm.$root.active.refreshRevision += 1
              vector.progress = 'idle'
              vector.set('updated', moment().toLocaleString())
              vectorSource.dispatchEvent('loadsource')
              if (onSuccess) {
                onSuccess()
              }
            },
            error: function () {
              vm.$root.active.refreshRevision += 1
              vector.progress = 'error'
            },
            dataType: 'json',
            xhrFields: {
              withCredentials: true
            }
          })
        }

        if (options.onadd) {
          vectorSource.on('addfeature', function (event) {
            options.onadd(event.feature)
          })
        }
        
        vector.postRemove = function () {
          // disable autoupdates
          if (this.autoRefresh) {
            clearInterval(this.autoRefresh)
            delete this.autoRefresh
          }
        }

        // if the "refresh" option is set, set a timer
        // to update the source
        if (options.refresh && !vector.autoRefresh) {
          vector.autoRefresh = setInterval(function () {
            vectorSource.loadSource("auto")
          }, options.refresh * 1000)
        }
        // populate the source with data
        vectorSource.loadSource("initial")

        vector.set('name', options.name)
        vector.set('id', options.id)

        vector.stopAutoRefresh = function() {
            if (this.autoRefresh) {
                clearInterval(this.autoRefresh)
                //console.log("Stop auto refresh for layer (" + options.id + ")")
                delete this.autoRefresh
            }
        }

        vector.startAutoRefresh = function() {
            if (!options.refresh) {
                //not refreshable
                return
            } 
            if(this.autoRefresh) {
                //already started
                return
            }
            this.autoRefresh = setInterval(function () {
                vectorSource.loadSource("auto")
            }, options.refresh * 1000)
            //console.log("Start auto refresh for layer (" + options.id + ") with interval " + options.refresh)
        }

        return vector
      },
      createAnnotations: function (layer) {
        return this.annotations.featureOverlay
      },
      // loader to create a WMTS layer from a kmi datasource
      createTileLayer: function (options) {
        var vm = this
        if (options.base) {
          options.format = 'image/jpeg'
        }
        var layer = $.extend({
          opacity: 1,
          name: 'Mapbox Outdoors',
          id: 'dpaw:mapbox_outdoors',
          format: 'image/png',
          tileSize: 1024,
          style: '',
          projection: 'EPSG:4326',
          wmts_url: this.defaultWMTSSrc
        }, options)

        // create a tile grid using the stock KMI resolutions
        var matrixSet = this.matrixSets[layer.projection][layer.tileSize]
        var tileGrid = new ol.tilegrid.WMTS({
          origin: ol.extent.getTopLeft([-180, -90, 180, 90]),
          resolutions: this.resolutions,
          matrixIds: matrixSet.matrixIds,
          tileSize: layer.tileSize
        })

        // override getZForResolution on tile grid object;
        // for weird zoom levels, the default is to round up or down to the
        // nearest integer to determine which tiles to use.
        // because we want the printing rasters to contain as much detail as
        // possible, we rig it here to always round up.
        tileGrid.origGetZForResolution = tileGrid.getZForResolution
        tileGrid.getZForResolution = function (resolution, optDirection) {
          return tileGrid.origGetZForResolution(resolution*1.4, -1)
        }

        // create a tile source
        var tileSource = new ol.source.WMTS({
          url: layer.wmts_url,
          layer: layer.id,
          matrixSet: matrixSet.name,
          format: layer.format,
          style: layer.style,
          projection: layer.projection,
          wrapX: true,
          tileGrid: tileGrid
        })

        var tileLayer = new ol.layer.Tile({
          opacity: layer.opacity || 1,
          source: tileSource
        })

        // hook the tile loading function to update progress indicator
        tileLayer.progress = ''

        tileLayer.postRemove = function () {
          if (this.autoRefresh) {
            clearInterval(this.autoRefresh)
            delete this.autoRefresh
          }
          if (this.autoTimelineRefresh) {
            clearTimeout(this.autoTimelineRefresh)
            //console.log(moment().toLocaleString() + " : " + this.autoTimelineRefresh + " - Clear auto timeline refresh task for " + options.name )
            this.autoTimelineRefresh = null
          }
          
        }   

        // set properties for use in layer selector
        tileLayer.set('name', layer.name,false)
        tileLayer.set('id', layer.id,false)

        if (options.lastUpdatetime) {
            tileLayer.set('updated',layer.lastUpdatetime)
        }

        tileLayer.stopAutoRefresh = function() {
            if (this.autoRefresh) {
                clearInterval(this.autoRefresh)
                //console.log(tileLayer.getSource().getLayer() + " : Stop auto refresh for layer (" + layer.id + ")")
                delete this.autoRefresh
            }
        }

        tileLayer.startAutoRefresh = function() {
            if (!options.refresh) {
                //not refreshable
                return
            } 
            if(this.autoRefresh) {
                //already started
                return
            }
            this.autoRefresh = setInterval(function () {
                vm.refreshLayerTile(tileLayer)
            }, options.refresh * 1000)
            //console.log(tileLayer.getSource().getLayer() + " : Start auto refresh for layer (" + layer.id + ") with interval " + layer.refresh)
        }

        // hook to swap the tile layer when timeIndex changes
        tileLayer.on('propertychange', function (event) {
          if (event.key === 'timeIndex') {
            if (options.timeline) {
                if (!(options.timeline[event.target.get(event.key)][2])) {
                    options.timeline[event.target.get(event.key)][2] = new ol.source.WMTS({
                      url: layer.wmts_url,
                      layer: options.timeline[event.target.get(event.key)][1],
                      matrixSet: matrixSet.name,
                      format: layer.format,
                      style: layer.style,
                      projection: layer.projection,
                      wrapX: true,
                      tileGrid: tileGrid
                    })
                    options.timeline[event.target.get(event.key)][2].setTileLoadFunction(vm.tileLoaderHook(options.timeline[event.target.get(event.key)][2], tileLayer))
                    vm.setUrlTimestamp(options.timeline[event.target.get(event.key)][2],moment.utc().unix())
                }
                tileLayer.setSource(options.timeline[event.target.get(event.key)][2] )

                if (options.refresh && options.autoRefreshStopped !== true ) {
                    tileLayer.stopAutoRefresh()
                    tileLayer.startAutoRefresh()
                }
            }
          }
        })

        if (!options.refreshTimeline && options.timelineRefresh && options.fetchTimelineUrl) {
            options.refreshTimeline = function(){
                var _func = null
                options.getCurrentRefreshTime = function() {
                    if (!options.lastTimelineRefreshTime) {
                        return moment.tz("Australia/Perth")
                    } else if ( moment.tz("Australia/Perth") - options.lastTimelineRefreshTime > options.timelineRefresh * 1000) {
                        return moment.tz("Australia/Perth")
                    } else {
                        return options.lastTimelineRefreshTime
                    }
                }
                options.getNextRefreshTime = function() {
                    var nextTime = moment(options.getCurrentRefreshTime())
                    nextTime.seconds(nextTime.seconds() + options.timelineRefresh )
                    return nextTime
                }
                options.getTimeIndexForTime = function(d) {
                    if (!options.timeline) {
                        return null
                    }
                    d = d || moment.tz("Australia/Perth")
                    $.each(options.timeline,function(index,timelineLayer) {
                        var timediff = d - moment.fromLocaleString(timelineLayer[0])
                        if (timediff < 0) {
                            timeIndex = (index == 0)?0:index - 1
                            return false
                        } else if (timediff === 0) {
                            timeIndex = index
                            return false
                        }
                    })
                    timeIndex = (timeIndex == null)?(options.timeline.length - 1):timeIndex
                    return timeIndex
                }
                _func = function(layer,tileLayer,auto,taskId) {
                    //console.log(moment().toLocaleString() + " : " + tileLayer.autoTimelineRefresh + " - Begin to refresh the timeline of " + layer.name)
                    var currentRefreshTime = layer.getCurrentRefreshTime()
                    if (layer.lastTimelineRefreshTime && currentRefreshTime - layer.lastTimelineRefreshTime === 0) {
                        if (!tileLayer.get("timeIndex")) { tileLayer.set('timeIndex',layer.getTimeIndexForTime())}
                        if (layer.previewLayer) {return}
                        if (!auto) {return}
                        var waitTimes = layer.getNextRefreshTime() - moment()
                        tileLayer.autoTimelineRefresh = setTimeout(function(){_func(layer,tileLayer,true)},waitTimes)
                        //console.log(moment().toLocaleString() + " : " + tileLayer.autoTimelineRefresh + " - Next timeline refresh time for " + layer.name + " is " + waitTimes + " milliseconds later" )
                    } else {
                        //console.log(moment().toLocaleString() + " : refresh timeline " + layer.id + "'s timeline. ")
                        var layerTime = moment(currentRefreshTime)
                        var layerId = null
                        var choosedTimelineLayerTime= null
                        if (layer.lastTimelineRefreshTime && tileLayer.get('timeIndex')) {
                            choosedTimelineLayerTime = moment.fromLocaleString(layer.timeline[tileLayer.get('timeIndex')][0])
                        }
                        var fetchTimelineFailed = function(status,statusText){
                            if (!layer.previewLayer && vm.getMapLayer(layer) !== tileLayer) {
                                //console.log(moment().toLocaleString() + " : " + tileLayer.autoTimelineRefresh + " - Stop run because " + layer.name + " is removed from map" )
                                return
                            }
                            if (!tileLayer.get("timeIndex")) { tileLayer.set('timeIndex',layer.getTimeIndexForTime())}
                            if (layer.previewLayer) {return}
                            tileLayer.progress = "error"
                            tileLayer.set('updated',layer.lastUpdatetime + "\r\n" + status + " : " + statusText)
                            vm.active.refreshRevision += 1
                            //console.warn(moment().toLocaleString() + " : Update the timeline of " + layer.name + " failed. code = " + status + ", reason = " + statusText )
                            if (!auto) {return}
                            var waitTimes = layer.getNextRefreshTime() - moment()
                            tileLayer.autoTimelineRefresh = setTimeout(function(){_func(layer,tileLayer,true)},waitTimes)
                            //console.log(moment().toLocaleString() + " : " + tileLayer.autoTimelineRefresh + " - Next timeline refresh time for " + layer.name + " is " + waitTimes + " milliseconds later" )
                        }
                        var timelineNotChanged = function(){
                            if (!layer.previewLayer && vm.getMapLayer(layer) !== tileLayer) {
                                //console.log(moment().toLocaleString() + " : " + tileLayer.autoTimelineRefresh + " - Stop run because " + layer.name + " is removed from map" )
                                return
                            }
                            if (!tileLayer.get("timeIndex")) { tileLayer.set('timeIndex',layer.getTimeIndexForTime())}
                            if (layer.previewLayer) {return}
                            tileLayer.progress = ""
                            tileLayer.set('updated',layer.lastUpdatetime )
                            vm.active.refreshRevision += 1
                            if (!auto) {return}
                            var waitTimes = layer.getNextRefreshTime() - moment()
                            tileLayer.autoTimelineRefresh = setTimeout(function(){_func(layer,tileLayer,true)},waitTimes)
                            //console.log(moment().toLocaleString() + " : " + tileLayer.autoTimelineRefresh + " - Next timeline refresh time for " + layer.name + " is " + waitTimes + " milliseconds later" )
                        }
                        var processTimeline = function(timeline){
                            if (!layer.previewLayer && vm.getMapLayer(layer) !== tileLayer) {
                                //console.log(moment().toLocaleString() + " : " + tileLayer.autoTimelineRefresh + " - Stop run because " + layer.name + " is removed from map" )
                                return
                            }
                            tileLayer.progress = ""
                            if (layer.timeline) {
                                //reuse already created tile source
                                $.each(timeline,function(index,timelineLayer) {
                                    if (layer.timeline.length > index && layer.timeline[index][2] && layer.timeline[index][1] === timelineLayer[1]) {
                                        timelineLayer[2] = layer.timeline[index][2]
                                        //clear browser cache and tile cache
                                        vm.setUrlTimestamp(timelineLayer[2],moment.utc().unix())
                                        timelineLayer[2].tileCache.clear()
                                    }
                                })
                            }
                            layer.timeline = timeline

                            //get new time index for current displayed timeline layer
                            var timeIndex = layer.getTimeIndexForTime(choosedTimelineLayerTime)
                            tileLayer.set('timeIndex', timeIndex)

                            tileLayer.set('updated',layer.lastUpdatetime)
                            vm.active.refreshRevision += 1

                            if (layer.previewLayer) {return}
                            if (!auto) {return}
                            var waitTimes = layer.getNextRefreshTime() - moment()
                            tileLayer.autoTimelineRefresh = setTimeout(function(){_func(layer,tileLayer,true)},waitTimes)
                            //console.log(moment().toLocaleString() + " : " + tileLayer.autoTimelineRefresh + " - Next timeline refresh time for " + layer.name + " is " + waitTimes + " milliseconds later" )
                        }

                        layer.lastTimelineRefreshTime = currentRefreshTime
                        tileLayer.progress = "loading"
                        $.ajax(layer.fetchTimelineUrl(layer.lastUpdatetime || "") ,{
                            xhrFields:{
                                withCredentials: true
                            },
                            dataType:"json",
                            success:function(data,status,jqXHR) {
                                if (jqXHR.status === 290) {
                                    timelineNotChanged()
                                    return
                                }
                                layer.lastUpdatetime = data.updatetime
                                processTimeline(data.layers)
                            },
                            error:function(jqXHR) {
                                fetchTimelineFailed(jqXHR.status,jqXHR.statusText)
                            }
                        })
        
                    }

                }
                
                return _func
           }()
        }

        if (options.refreshTimeline) {
            tileLayer.autoTimelineRefresh = null
            options.refreshTimeline(options,tileLayer,true)
        } else {
            tileSource.setTileLoadFunction(this.tileLoaderHook(tileSource, tileLayer))
        }

        // if the "refresh" option is set, set a timer
        // to force a reload of the tile content
        if (options.refresh) {
          tileLayer.set('updated', moment().toLocaleString())
          vm.$root.active.refreshRevision += 1
          tileLayer.autoRefresh = setInterval(function () {
            vm.refreshLayerTile(tileLayer)
          }, options.refresh * 1000)
        }

        return tileLayer
      },

      getMapLayer: function (id) {
        if (!this.olmap) { return undefined}
        if (id && id.id) { id = id.id } // if passed a catalogue layer, get actual id
        return this.olmap.getLayers().getArray().find(function (layer) {
          return layer.get('id') === id
        })
      },
      // initialise map
      init: function (options) {
        var vm = this
        options = options || {}

        // add some extra projections
        proj4.defs("EPSG:28349","+proj=utm +zone=49 +south +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs");
        proj4.defs("EPSG:28350","+proj=utm +zone=50 +south +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs");
        proj4.defs("EPSG:28351","+proj=utm +zone=51 +south +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs");
        proj4.defs("EPSG:28352","+proj=utm +zone=52 +south +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs");
        proj4.defs("EPSG:28353","+proj=utm +zone=53 +south +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs");
        proj4.defs("EPSG:28354","+proj=utm +zone=54 +south +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs");
        proj4.defs("EPSG:28355","+proj=utm +zone=55 +south +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs");
        proj4.defs("EPSG:28356","+proj=utm +zone=56 +south +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs");

        // bump search bar over if there's no fullscreen button
        if (!ol.control.FullScreen.isFullScreenSupported()) {
          $('#map-search').addClass('noFullScreen')
          $('#map-search-button').addClass('noFullScreen')
        }

        this.olmap = new ol.Map({
          logo: false,
          renderer: 'canvas',
          target: 'map',
          view: new ol.View({
            projection: 'EPSG:4326',
            center: vm.view.center,
            zoom: 6,
            maxZoom: 21,
            minZoom: 5
          }),
          controls:[],
          interactions: ol.interaction.defaults({
            altShiftDragRotate: false,
            pinchRotate: false,
            dragPan: false,
            doubleClickZoom: false,
            keyboard: false
          })
        })

        this.setScale(this.view.scale / 1000)

        // add some default interactions
        this.olmap.addInteraction(this.dragPanInter)
        this.olmap.addInteraction(this.doubleClickZoomInter)
        this.olmap.addInteraction(this.keyboardPanInter)
        this.olmap.addInteraction(this.keyboardZoomInter)
        this.olmap.addInteraction(this.middleDragPanInter)

        // Create the graticule component
        this.graticule.setMap(this.olmap)

        // setup scale events
        this.olmap.on('postrender', function () {
          vm.scale = vm.getScale()
        })

      },
      initLayers: function (fixedLayers, activeLayers) {
        var vm = this
        //add fixed layers to category
        $.each(fixedLayers,function(index,fixedLayer) {
            var catLayer = vm.$root.catalogue.getLayer(fixedLayer.id)
            if (catLayer) {
                //fixed layer already exist, update the properties 
                $.extend(catLayer,fixedLayer)
            } else {
                //fixed layer not exist, add it
                vm.$root.catalogue.catalogue.push(fixedLayer)
            }
        })
        //ignore the active layers which does not exist in the catalogue layers.
        activeLayers = activeLayers.filter(function(activeLayer){
            return vm.$root.catalogue.getLayer(activeLayer[0]) && true
        })
        //create active open layers 
        var initialLayers = activeLayers.reverse().map(function (activeLayer) {
          var layer = $.extend(vm.$root.catalogue.getLayer(activeLayer[0]), activeLayer[1])
          return vm['create' + layer.type](layer)
        })
        //add active layers into map
        $.each(initialLayers,function(index,layer){
            vm.olmap.addLayer(layer)
        })
        //enable controls
        var overviewLayer = vm.$root.catalogue.getLayer("dpaw:mapbox_outdoors")
        vm.mapControls = {
            "zoom": {
                enabled:false,
                autoenable:false,
                controls:new ol.control.Zoom({
                  target: $('#external-controls').get(0)   
                })
            },
            "overviewMap": {
                enabled:false,
                autoenable:false,
                controls:new ol.control.OverviewMap({
                    className: 'ol-overviewmap ol-custom-overviewmap',
                    layers: [],
                    collapseLabel: '\u00BB',
                    label: '\u00AB',
                    collapsed: false,
                    view: new ol.View({
                        projection: 'EPSG:4326',
                    })
                }),
                preenable:function(enable){
                    if (enable) {
                        this.controls.getOverviewMap().addLayer(vm['create' + overviewLayer.type](overviewLayer))
                    } else {
                        if (this._interact) {
                            this._interact.unset()
                            this._interact = null
                        }
                        try {
                            this.controls.getOverviewMap().removeLayer(this.controls.getOverviewMap().getLayers().get(0))
                        } catch (ex) {
                        }
                    }
                },
                postenable:function(enable) {
                    if (enable) {
                        var overviewMapControl = this.controls
                        var extentbox = $(".ol-custom-overviewmap").find(".ol-overlay-container")
                        var overviewMap = $(".ol-custom-overviewmap").find(".ol-overviewmap-map")
                        if (extentbox.length) {
                            this._interact = interact(extentbox.get(0),{})
                            .draggable({
                                intertia:true,
                                restrict:{
                                    restriction:overviewMap.get(0),
                                    endOnly:true,
                                    elementRect:{top:0,left:0,bottom:1,right:1}
                                },
                                autoScroll:true,
                                onmove: function(event){
                                    // keep the dragged position in the data-x/data-y attributes
                                    //console.log(extentbox.get(0).style.left + "\t" + extentbox.get(0).style.right + "\t" + extentbox.get(0).style.top + "\t" + extentbox.get(0).style.bottom)
                                    //console.log("x0 = " + event.x0 +",y0= " + event.y0 + ",clientX0=" + event.clientX0 + ",clientY0=" + event.clientY0 + ",dx=" + event.dx + ",dy=" + event.dy)
                                    if (extentbox.get(0).style.left) {
                                        extentbox.get(0).style.left = (parseInt(extentbox.get(0).style.left) + event.dx) + "px"
                                    }
                                    if (extentbox.get(0).style.right) {
                                        extentbox.get(0).style.right = (parseInt(extentbox.get(0).style.right) + event.dx) + "px"
                                    }
                                    if (extentbox.get(0).style.bottom) {
                                        extentbox.get(0).style.bottom = (parseInt(extentbox.get(0).style.bottom) - event.dy) + "px"
                                    }
                                    if (extentbox.get(0).style.top) {
                                        extentbox.get(0).style.top = (parseInt(extentbox.get(0).style.top) - event.dy) + "px"
                                    }
                                },
                                onend:function(event) {
                                    var centralPosition = [
                                        (extentbox.get(0).style.left)?(parseInt(extentbox.get(0).style.left) + extentbox.width() / 2):(parseInt(extentbox.get(0).style.right) - extentbox.width() / 2) ,
                                        (extentbox.get(0).style.bottom)?(overviewMap.height() - parseInt(extentbox.get(0).style.bottom) - extentbox.height() / 2):(overviewMap.height() - parseInt(extentbox.get(0).style.top) + extentbox.height() / 2)
                                    ]
                                    //console.log(extentbox.get(0).style.left + "\t" + extentbox.get(0).style.bottom + "\t" + extentbox.width() + "\t" + extentbox.height() + "\t" + centralPosition + "\t" + overviewMapControl.getOverviewMap().getCoordinateFromPixel(centralPosition))
                                    overviewMapControl.getMap().getView().setCenter(overviewMapControl.getOverviewMap().getCoordinateFromPixel(centralPosition))
                                }
                            })
                        }
                    }
                }
            },
            "scaleLine": {
                enabled:false,
                autoenable:false,
                controls:new ol.control.ScaleLine()
            },
            "mousePosition": {
                enabled:false,
                controls:new ol.control.MousePosition({
                    coordinateFormat: function(coordinate) {
                        return vm.getDeg(coordinate)+'<br/>'+vm.getDMS(coordinate)+'<br/>'+vm.getMGA(coordinate)
                    }
                })
            },
            "fullScreen": {
                enabled:false,
                controls:new ol.control.FullScreen({
                    source: $('body').get(0),
                    target: $('#external-controls').get(0),
                    label: $('<i/>', {
                        class: 'fa fa-expand'
                    })[0]
                })
            },
            "scale": {
                enabled:false,
                autoenable:false,
                controls:new ol.control.Control({
                    element: $('#menu-scale').get(0),
                    target: $('#external-controls').get(0)
            })},
            "search": {
                enabled:false,
                controls: [
                    new ol.control.Control({
                        element: $('#map-search').get(0),
                        target: $('#external-controls').get(0)
                      }),
                    new ol.control.Control({
                        element: $('#map-search-button').get(0),
                        target: $('#external-controls').get(0)
                    })
                ]
            },
            "attribution": {
                enabled:false,
                controls:new ol.control.Attribution()
            },
            "measure": {
                enabled:false,
                autoenable:false,
                controls:vm.measure.mapControl
            }
        }
        $.each(vm.mapControls,function(key,control){
            if (control.autoenable === undefined || control.autoenable) {
                vm.enableControl(key,true)
            }
        })
      },
      zoomToSelected: function () {
        var selectedFeatures = this.annotations.selectedFeatures
        if (selectedFeatures.getLength() === 0) {
            return
        } else {
            var extent = null
            if (selectedFeatures.getLength() === 1) {
                extent = selectedFeatures.item(0).getGeometry().getExtent()
                extent = ol.extent.isEmpty(extent)?null:extent
            } else {
                selectedFeatures.forEach(function (f) {
                    if (!ol.extent.isEmpty(f.getGeometry().getExtent())) {
                      extent = extent || ol.extent.createEmpty()
                      ol.extent.extend(extent, f.getGeometry().getExtent())
                    }
                })
            }
            if (extent) {
                this.olmap.getView().fit(extent, this.olmap.getSize())
            }
        }
      }
    },
    ready: function () {
      var vm = this
      var mapStatus = this.loading.register("olmap","Open layer map Component","Initialize")
      this.svgBlobs = {}
      this.svgTemplates = {}
      this.cachedStyles = {}
      this.jobs = {}

      // generate matrix IDs from name and level number
      $.each(this.matrixSets, function (projection, innerMatrixSets) {
        $.each(innerMatrixSets, function (tileSize, matrixSet) {
          var matrixIds = new Array(matrixSet.maxLevel - matrixSet.minLevel + 1)
          for (var z = matrixSet.minLevel; z <= matrixSet.maxLevel; ++z) {
            matrixIds[z] = matrixSet.name + ':' + z
          }
          matrixSet.matrixIds = matrixIds
        })
      })

      mapStatus.wait(30,"Listen 'gk-init' event")
      this.$on('gk-init', function() {
        mapStatus.progress(80,"Process 'gk-init' event")
        
        if ($("#map .ol-viewport canvas").attr("width")) {
            vm.displayResolution[0] = Math.round(($("#map .ol-viewport canvas").attr("width") /  $("#map .ol-viewport canvas").width()) * 100) / 100
        }
        if ($("#map .ol-viewport canvas").attr("height")) {
            vm.displayResolution[1] = Math.round(($("#map .ol-viewport canvas").attr("height") /  $("#map .ol-viewport canvas").height()) * 100) / 100
        }

        vm.showGraticule(vm.displayGraticule)

        mapStatus.end()
        return true
      })
    }
  }
</script>
