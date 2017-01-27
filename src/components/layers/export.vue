<template>
  <div class="tabs-panel" id="layers-export" v-cloak>
    <div id="map-export-controls">
      <!--div class="tool-slice row collapse">
        <div class="small-3">
          <label class="tool-label">Vector format:</label>
        </div>
        <div class="small-9">
          <select name="select" v-model="vectorFormat">
            <option value="json" selected>GeoJSON (web GIS)</option> 
            <option value="kml">KML (Google Earth)</option>
            <option value="geopkg">Geopackage (high performance)</option>
            <option value="shapefile">Shapefile (legacy desktop GIS)</option>
            <option value="csv">CSV (Spreadsheet/Excel)</option>
          </select>
        </div>
      </div-->
      <div class="tool-slice row collapse">
        <div class="small-3">
          <label class="tool-label">Name:</label>
        </div>
        <div class="small-9">
          <input id="export-name" type="text" v-model="title" placeholder="Map Name"/>
        </div>
      </div>
      <div class="tool-slice row collapse">
        <div class="small-3">
          <label class="tool-label">Paper size:</label>
        </div>
        <div class="small-9">
          <select v-model="paperSize">
                    <option v-for="size in paperSizes" v-bind:value="$key">{{ $key }} ({{ size[0] }}mm &times; {{ size[1] }}mm)</option>
                  </select>
        </div>
      </div>

      <div class="tool-slice row collapse">
        <div class="small-3">
          <label class="tool-label">Download:</label>
        </div>
        <div class="small-9">
          <div class="expanded button-group">
            <a class="button" title="JPG for quick and easy printing" @click="print('jpg')"><i class="fa fa-file-image-o"></i><br>JPG</a>
            <a class="button" title="Geospatial PDF for use in PDF Maps and Adobe Reader" @click="print('pdf')"><i class="fa fa-print"></i><br>PDF</a>
            <a class="button" title="GeoTIFF for use in QGIS on the desktop" @click="print('tif')"><i class="fa fa-picture-o"></i><br>GeoTIFF</a>
            <a class="button" title="Legends of active layers" @click="layerlegends.toggleLegends()"><i class="fa fa-file-pdf-o"></i><br>Legend</a>
          </div>
        </div>
      </div>

      <div class="tool-slice row collapse">
        <div class="small-3">
          <div class="switch tiny">
            <input class="switch-input" id="toggleMaintainScaleWhenPrinting" type="checkbox" v-bind:checked="settings.maintainScaleWhenPrinting" @change="toggleMaintainScaleWhenPrinting"/>
            <label class="switch-paddle" for="toggleMaintainScaleWhenPrinting">
              <span class="show-for-sr">Retain print scale when printing</span>
            </label>
          </div>
        </div>
        <div class="small-9">
          <label for="toggleMaintainScaleWhenPrinting" >Retain print scale when printing</label>
        </div>
      </div>
      
      <hr class="row"/>

      <div class="tool-slice row collapse">
        <div class="small-3">
          <label class="tool-label">Save view:</label>
        </div>
        <div class="small-9 columns">
          <div class="input-group">
            <input v-el:savestatename class="input-group-field" type="text" placeholder="Name for saved view"/>
            <div class="input-group-button">
              <a class="button" @click="saveStateButton()">Save</a>
            </div>
          </div>
        </div>
      </div>
      <div class="tool-slice row collapse">
        <div class="small-3">
          <label class="tool-label">Export view:</label>
        </div>
        <div class="small-9 columns">
          <div class="expanded button-group">
            <a class="button expanded" @click="download()"><i class="fa fa-download"></i> Download current view</a>
          </div>
        </div>
      </div>
      <div class="tool-slice row collapse">
        <div class="small-3">
          <label class="tool-label">Load view:</label>
        </div>
        <div class="small-9 columns">
          <div class="expanded button-group">
            <label class="button expanded" for="uploadFile"><i class="fa fa-upload"></i> Upload view file</label><input type="file" id="uploadFile" class="show-for-sr" name="statefile" accept="application/json" v-model="statefile" v-el:statefile @change="load()"/>
          </div>
          <div v-for="state in states" class="feature-row" style="overflow: hidden">
            <div class="float-right button-group small">
              <a class="button" title="Open view" @click="open(state)"><i class="fa fa-folder-open"></i></a>
              <a class="button" title="Download view" @click="download(state)"><i class="fa fa-download"></i></a>
              <a class="button alert" title="Delete view" @click="remove(state)">✕</a>
            </div>
            {{ state }}
          </div>
          <div v-if="states.length == 0" class="feature-row">
            No saved views yet
          </div>
        </div>
      </div>

      <div class="hide" v-el:legendsvg>
        <gk-legend></gk-legend>
      </div>

      <img id="map-disclaimer" class="hide" src="/dist/static/images/map-disclaimer.svg"/>

      <gk-layerlegends v-ref:layerlegends></gk-layerlegends>
    </div>
  </div>
</template>
<script>
  import { kjua, saveAs, moment, $, localforage,hash} from 'src/vendor.js'
  import gkLegend from './legend.vue'
  import gkLayerlegends from './layerlegends.vue'
  export default {
    store: ['whoami', 'dpmm', 'view', 'mmPerInch', 'gokartService','drawingSequence','s3Service','settings','displayResolution'],
    components: { gkLegend,gkLayerlegends },
    data: function () {
      return {
        minDPI: 150,
        paperSizes: {
          A0: [1189, 841],
          A1: [841, 594],
          A2: [594, 420],
          A3: [420, 297],
          A4: [297, 210]
        },
        paperSize: 'A3',
        printStatus: {
            oldLayout: {},
            layout:{},
            overviewMap:{},
            jobs:0
        },
        title: '',
        statefile: '',
        vectorFormat: 'geojson',
        states: [],
        vectorFormats:[
            {format:"geojson",title:"GeoJSON (web GIS)",name:"GeoJSON"},
            {format:"sqlite",title:"SQLite",name:"SQLite"},
            {format:"gpkg",title:"GeoPackage",name:"GeoPackage"},
            {format:"csv",title:"CSV (Spreadsheet/Excel)",name:"CSV"}
        ]
      }
    },
    // parts of the template to be computed live
    computed: {
      loading: function () { return this.$root.loading },
      annotations: function () { return this.$root.annotations },
      layerlegends:function() {return this.$refs.layerlegends},
      map:function() {return this.$root.map},
      olmap: function () {
        return this.$root.map.olmap
      },
      shortUrl: {
        cache: false,
        get: function () {
          if (!this.olmap) { return }
          var lonlat = this.olmap.getView().getCenter()
          return $.param({ lon: lonlat[0], lat: lonlat[1], scale: Math.round(this.$root.map.getScale() * 1000) })
        }
      },
      finalTitle:function() {
        this.title = this.title.trim()
        return (this.title.length == 0)?"Quick Print":this.title
      },
      bucketKey: function() {
        return hash.MD5({
            'extent':this.printStatus.layout.extent.join(' '),
            'author': this.legendInfo().author,
            'filename':this.finalTitle,
            'time': Date.now()
        })
      },
    },
    // methods callable from inside the template
    methods: {
      toggleMaintainScaleWhenPrinting:function(ev) {
        this.settings.maintainScaleWhenPrinting = !this.settings.maintainScaleWhenPrinting
        this.saveState()
      },
      // info for the legend block on the print raster
      legendInfo: function () {
        var result = {
          title: this.finalTitle,
          author: "Produced by the Department of Parks and Wildlife", //this.whoami.email,
          date: 'Map last amended ' + moment().toLocaleString()
        }
        if (this.$root.map) {
          result.km = (Math.round(this.$root.map.getScale() * 40) / 1000).toLocaleString()
          result.scale = this.paperSize + ' ' + this.$root.scales.scaleString
        }
        return result
      },
      exportVector: function(features, name,format) {
        var vm = this
        //add applicaiton name and timestamp
        var name = (name || '') + "." + this.$root.profile.name + "_export_" + moment().format("YYYYMMDD_HHmm")
        var result = this.$root.geojson.writeFeatures(features)
        var blob = new window.Blob([result], {type: 'application/json;charset=utf-8'})
        format = format || this.vectorFormat
        if (format === 'geojson') {
          saveAs(blob, name + '.geojson')
        } else {
          var formData = new window.FormData()
          formData.append('json', blob, name + '.json')
          var req = new window.XMLHttpRequest()
          req.open('POST', this.gokartService + '/ogr/' + format)
          req.responseType = 'blob'
          req.withCredentials = true
          req.onload = function (event) {
            if (req.status >= 400) {
                var reader = new FileReader()
                reader.readAsText(req.response)
                reader.addEventListener("loadend",function(e){
                    alert(e.target.result)
                })
            } else {
                var filename = null
                if (req.getResponseHeader("Content-Disposition")) {
                    if (!vm._filename_re) {
                        vm._filename_re = new RegExp("filename=[\'\"](.+)[\'\"]")
                    }
                    var matches = vm._filename_re.exec(req.getResponseHeader("Content-Disposition"))
                    filename = (matches && matches[1])? matches[1]: null
                }
                if (!filename) {
                    filename = name + "." + this.vectotFormat
                }
                saveAs(req.response, filename)
            }
          }
          req.send(formData)
        }
      },
      // resize map to page dimensions (in mm) for printing, save layout
      prepareMapForPrinting: function () {
        var vm = this
        $('body').css('cursor', 'progress')
        if (this.printStatus.jobs <= 0) {
            //save overviewMap status and enable overviewMap if not enabled
            this.printStatus.overviewMap.enabled = this.map.isControlEnabled("overviewMap")
            this.printStatus.overviewMap.collapsed = this.map.getControl("overviewMap").getCollapsed()
            if (this.printStatus.overviewMap.collapsed) {
                this.map.getControl("overviewMap").setCollapsed(false)
            }
            if (!this.printStatus.overviewMap.enabled) {
                this.map.enableControl("overviewMap",true)
            }
        
            //no print job is processing, get the map size and scale for recovering.
            this.printStatus.oldLayout.size = this.olmap.getSize()
            this.printStatus.oldLayout.scale = this.$root.map.getScale()
            this.printStatus.oldLayout.extent = this.olmap.getView().calculateExtent(this.olmap.getSize())

            this.printStatus.dpmm = this.minDPI / this.mmPerInch

            //disable the interactions to prevent the user from operating the map
            this.printStatus.interactions = this.olmap.getInteractions().getArray().slice(0)
            $.each(this.printStatus.interactions,function(index,interact) {
                vm.olmap.removeInteraction(interact)
            })

            //disable the controls to prevent the user from operating the map
            this.printStatus.controls = []
            $.each(this.map.mapControls,function(key,control) {
                if (key === "overviewMap") {
                    //overviewMap has been processed, ignore here
                    return
                }
                if (control.enabled) {
                    vm.printStatus.controls.push(key)
                    vm.map.enableControl(key,false)
                }
            })


            this.printStatus.startTime = new Date()
        }

        this.printStatus.layout.width = this.paperSizes[this.paperSize][0]
        this.printStatus.layout.height = this.paperSizes[this.paperSize][1]
        //adjust the map for printing.
        if (this.settings.maintainScaleWhenPrinting) {
            this.printStatus.layout.scale = this.$root.map.getFixedScale(this.printStatus.oldLayout.scale)
            this.printStatus.layout.size = [this.printStatus.dpmm * this.printStatus.layout.width, this.printStatus.dpmm * this.printStatus.layout.height]
            this.olmap.setSize(this.printStatus.layout.size)
            this.$root.map.setScale(this.printStatus.layout.scale)
        } else {
            this.printStatus.layout.size = [this.printStatus.dpmm * this.printStatus.layout.width, this.printStatus.dpmm * this.printStatus.layout.height]
            this.olmap.setSize(this.printStatus.layout.size)
            this.olmap.getView().fit(this.printStatus.oldLayout.extent, this.olmap.getSize())
            this.printStatus.layout.scale = this.$root.map.getFixedScale()
            this.$root.map.setScale(this.printStatus.layout.scale)
        }
        //extent is changed because the scale is adjusted to the closest fixed scale, recalculated the extent again
        this.printStatus.layout.extent = this.olmap.getView().calculateExtent(this.olmap.getSize())

        this.printStatus.jobs = (this.printStatus.jobs >= 0)?(this.printStatus.jobs + 1):1
      },
      // restore map to viewport dimensions
      restoreMapFromPrinting: function () {
        var vm = this
        this.printStatus.jobs -= 1
        if (this.printStatus.jobs <= 0) {
            //all print jobs are done
            //restore overview map
            if (this.printStatus.overviewMap.collapsed) {
                this.map.getControl("overviewMap").setCollapsed(true)
            }
            if (!this.printStatus.overviewMap.enabled) {
                this.map.enableControl("overviewMap",false)
            }
            //restore the map size and map scale
            this.olmap.setSize(this.printStatus.oldLayout.size)
            this.$root.map.setScale(this.printStatus.oldLayout.scale)
            //restore the interactions
            $.each(this.printStatus.interactions,function(index,interact) {
                vm.olmap.addInteraction(interact)
            })
            //restore controls
            $.each(this.printStatus.controls,function(index,controlKey) {
                vm.map.enableControl(controlKey,true)
            })
            this.printStatus.endTime = new Date()
            $('body').css('cursor', 'default')
        }
      },
      // generate legend block, scale ruler is 40mm wide
      renderLegend: function (bucketKey) {
        var qrcanvas = bucketKey?kjua({text: this.s3Service + bucketKey, render: 'canvas', size: 100}):null
        return ['data:image/svg+xml;utf8,' + encodeURIComponent(this.$els.legendsvg.innerHTML), qrcanvas]
      },
      // POST a generated JPG to the gokart server backend to convert to GeoPDF
      blobGDAL: function (blob, name, format,bucketKey) {
        var vm = this
        var _func = function(legendData) {
            var formData = new window.FormData()
            formData.append('extent', vm.printStatus.layout.extent.join(' '))
            formData.append('jpg', blob, name + '.jpg')
            if (format === "pdf" && legendData)  {
                formData.append('legends', legendData, name + '.legend.pdf')
            }
            formData.append('dpi', Math.round(vm.printStatus.layout.canvasPxPerMM * 25.4))
            formData.append('title', vm.finalTitle)
            formData.append('author', vm.legendInfo().author)
            if (bucketKey) {
                formData.append('bucket_key',bucketKey)
            }
            var req = new window.XMLHttpRequest()
            req.open('POST', vm.gokartService + '/gdal/' + format)
            req.withCredentials = true
            req.responseType = 'blob'
            req.onload = function (event) {
              saveAs(req.response, name + '.' + format)
            }
            req.send(formData)
        }
        if (format === "pdf") {
            vm.layerlegends.getLegendBlob(true,true,function(legendData){
                _func(legendData)
            })
        } else {
            _func()
        }
      },
      // make a printable raster from the map
      print: function (format) {
        // rig the viewport to have printing dimensions
        this.prepareMapForPrinting()
        var timer
        var vm = this
        // wait until map is rendered before continuing
        var whiteout = vm.olmap.on('precompose', function (event) {
          var canvas = event.context.canvas
          var ctx = canvas.getContext('2d')
          ctx.beginPath()
          ctx.rect(0, 0, canvas.width, canvas.height)
          ctx.fillStyle = "white"
          ctx.fill()
        })
        var mainmap_composing = null
        var overviewmap_composing = null
        var canvas = null
        var overviewmap_canvas = null

        var postcomposeFunc = function() {
          timer && clearTimeout(timer)
          timer = setTimeout(function () {
            // remove composing watcher
            vm.olmap.unByKey(whiteout)
            vm.olmap.unByKey(mainmap_composing)
            vm.map.getControl("overviewMap").getOverviewMap().unByKey(overviewmap_composing)
            var ctx = canvas.getContext('2d')

            var img = new window.Image()
            var bucketKey = (format !== 'jpg')?vm.bucketKey:null
            var legend = vm.renderLegend((format === 'pdf')?bucketKey:null)
            var url = legend[0]
            var qrcanvas = legend[1]
            // wait until legend is rendered
            img.onerror = function (err) {
              window.alert(JSON.stringify(err))
              vm.restoreMapFromPrinting()
            }
            img.onload = function () {
              //draw overview map
              ctx.drawImage(overviewmap_canvas,canvas.width - overviewmap_canvas.width - 2,2,overviewmap_canvas.width ,overviewmap_canvas.height)
              //draw overview map rectangle
              var box = $(".ol-custom-overviewmap").find(".ol-overviewmap-box")
              if (box.length) {
                var width = box.width() * vm.displayResolution[0]
                var height = box.height() * vm.displayResolution[1]
                var x = box.parent().position().left * vm.displayResolution[0]
                var y = box.parent().position().top * vm.displayResolution[1]
                ctx.beginPath()
                ctx.rect(canvas.width - overviewmap_canvas.width - 2 + x,2 + y, width, height)
                ctx.strokeStyle = "red"
                ctx.lineWidth = 2
                ctx.stroke()
              }
              //draw overview map border
              ctx.beginPath()
              ctx.rect(canvas.width - overviewmap_canvas.width - 4, 0, overviewmap_canvas.width + 4, overviewmap_canvas.height + 4)
              ctx.strokeStyle = "black"
              ctx.lineWidth = 2
              ctx.stroke()
              // legend is 12cm wide
              vm.printStatus.layout.canvasPxPerMM = canvas.width / vm.printStatus.layout.width
              var height = 120 * vm.printStatus.layout.canvasPxPerMM * img.height / img.width
              ctx.drawImage(img, 0, 0, 120 * vm.printStatus.layout.canvasPxPerMM, height)

              var disclaimerImg = $("#map-disclaimer").get(0)
              height = disclaimerImg.height
              ctx.drawImage(disclaimerImg, 
                canvas.width - disclaimerImg.width, 
                canvas.height - height, 
                disclaimerImg.width, 
                height)
              //draw qr code
              if (qrcanvas) {
                  ctx.drawImage(qrcanvas, 2, canvas.height - qrcanvas.height - 2)
              }
              window.URL.revokeObjectURL(url)
              // generate a jpg copy of the canvas contents
              var filename = vm.finalTitle.replace(/ +/g, '_')
              canvas.toBlob(function (blob) {
                vm.restoreMapFromPrinting()
                if (format === 'jpg') {
                  saveAs(blob, filename + '.jpg')
                } else {
                  vm.blobGDAL(blob, filename, format,bucketKey)
                }
              }, 'image/jpeg', 0.9)
            }
            img.src = url
          // only output after 5 seconds of no tiles
          }, 5000)
        }
        mainmap_composing = vm.olmap.on('postcompose', function (event) {
            canvas = event.context.canvas
            if (!overviewmap_composing) {
                overviewmap_composing = vm.map.getControl("overviewMap").getOverviewMap().on('postcompose', function (event) {
                    overviewmap_canvas = event.context.canvas
                    postcomposeFunc()
                })
                vm.map.getControl("overviewMap").getOverviewMap().renderSync()
            }
        })
        vm.olmap.renderSync()
      },
      download: function (key) {
        if (key) {
          // download JSON blob from the state store
          localforage.getItem('sssStateStore').then(function (store) {
            if (key in store) {
              var blob = new window.Blob([JSON.stringify(store[key], null, 2)], {type: 'application/json;charset=utf-8'})
              saveAs(blob, key+'.sss')
            }
          })
        } else {
          // download JSON blob of the current state
          localforage.getItem('sssOfflineStore').then(function (store) {
            var blob = new window.Blob([JSON.stringify(store, null, 2)], {type: 'application/json;charset=utf-8'})
            saveAs(blob, 'sss_view_' +moment().format('YYYY-MM-DD-HHmm')+'.sss')
          })
        }
      },
      open: function (key) {
        // load the JSON blob from the state store into the offline store
        localforage.getItem('sssStateStore').then(function (store) {
          if (key in store) {
            localforage.setItem('sssOfflineStore', store[key]).then(function (v) {
              document.location.reload()
            })
          }
        })
      },
      remove: function (key) {
        // if there's a key matching in the state store, remove it
        var vm = this
        localforage.getItem('sssStateStore').then(function (store) {
          if (key in store) {
            delete store[key]
            vm.states = Object.keys(store)
            localforage.setItem('sssStateStore', store)
          }
        })
      },
      load: function () {
        // upload JSON into a state slot 
        var vm = this
        var reader = new window.FileReader()
        if (this.$els.statefile.files.length > 0) {
          var key = this.$els.statefile.files[0].name.split('.', 1)[0]
          reader.onload = function (e) {
            localforage.getItem('sssStateStore', function (err, value) {
              var store = {}
              if (value) {
                store = value
              }
              store[key] = JSON.parse(e.target.result)
              localforage.setItem('sssStateStore', store).then(function (v) {
                vm.states = Object.keys(store)
              })
            })
          }
          reader.readAsText(this.$els.statefile.files[0])
        }
      },
      importVector: function(file) {
        // upload vector  
        var vm = this
        var reader = new window.FileReader()
        reader.onload = function (e) {
          var data = e.target.result
          var p = file.name.lastIndexOf('.')
          var fileFormat = file.name
          if (p>=0) {
              fileFormat = file.name.substring(p).toLowerCase()
          } 
          var features = null
          var ignoredFeatures = []
          var feature = null
          if ((fileFormat === ".geojson") || (fileFormat === ".json")) {
              //geo json file
              features = new ol.format.GeoJSON().readFeatures(data,{dataProjection:"EPSG:4326"})
              var f = null
              var clearProperties = function(feature){
                  $.each(feature.getKeys(),function(index,key){
                        if ([feature.getGeometryName()].indexOf(key) < 0) {
                            feature.unset(key)
                        }
                    })
              }
              for(var i = features.length - 1;i >= 0;i--) {
                feature = features[i]
                if (!vm.annotations.getTool(feature.get("toolName"))) {
                    //external feature.
                    if (feature.getGeometry() instanceof ol.geom.Point) {
                        clearProperties(feature)
                        feature.set('toolName','Custom Point',true)
                        feature.set('shape',vm.annotations.pointShapes[0],true)
                        feature.set('colour',"#000000",true)
                    } else if (feature.getGeometry() instanceof ol.geom.LineString) {
                        clearProperties(feature)
                        feature.set('toolName','Custom Line',true)
                        feature.set('size',2,true)
                        feature.set('colour',"#000000",true)
                    } else if (feature.getGeometry() instanceof ol.geom.Polygon) {
                        clearProperties(feature)
                        feature.set('toolName','Custom Area',true)
                        feature.set('size',2,true)
                        feature.set('colour',"#000000",true)
                    } else if (
                            feature.getGeometry() instanceof ol.geom.MultiPoint ||
                            feature.getGeometry() instanceof ol.geom.MultiLineString ||
                            feature.getGeometry() instanceof ol.geom.MultiPolygon ||
                            feature.getGeometry() instanceof ol.geom.GeometryCollection
                        ) {
                        //remove the MultiPoint feature
                        features.splice(i,1)
                        //split the gemoetry collection into mutiple features
                        var geometries = null
                        if (feature.getGeometry() instanceof ol.geom.MultiPoint) {
                            geometries = feature.getGeometry().getPoints()
                        } else if (feature.getGeometry() instanceof ol.geom.MultiLineString) {
                            geometries = feature.getGeometry().getLineStrings()
                        } else if (feature.getGeometry() instanceof ol.geom.MultiPolygon) {
                            geometries = feature.getGeometry().getPolygons()
                        } else if (feature.getGeometry() instanceof ol.geom.GeometryCollection) {
                            geometries = feature.getGeometry().getGeometries()
                        }
                                        
                        //split MultiPoint to multiple point feature
                        $.each(geometries,function(index,geometry){
                            f = new ol.Feature({ geometry:geometry}) 
                            features.splice(i,0,f)
                            i += 1
                        })

                    } else {
                        ignoredFeatures.push(feature)
                    }  
                }
              }
          } else if (fileFormat === ".gpx") {
              //gpx file
              var vectors = new ol.format.GPX().readFeatures(data,{dataProjection:"EPSG:4326"})
              features = []
              if (vectors && vectors.length) {
                  $.each(vectors,function(index,feature) {
                      if (feature.getGeometry() instanceof ol.geom.Point) {
                          //feature.set('toolName','Spot Fire')
                          ignoredFeatures.push(feature)
                      } else if(feature.getGeometry() instanceof ol.geom.LineString) {
                          var coordinates = feature.getGeometry().getCoordinates()
                          coordinates.push(coordinates[0])
                          feature.setGeometry(new ol.geom.Polygon([coordinates]))
                          feature.set('toolName','Fire Boundary')
                          features.push(feature)
                      } else if(feature.getGeometry() instanceof ol.geom.MultiLineString) {
                          //convert each linstring in MultiLineString as a fire boundary
                          var geom = feature.getGeometry()
                          feature.setGeometry(null)
                          var coordinates = null
                          var f = null
                          $(geom.getLineStrings(),function(index,linestring) {
                            f = feature.clone()
                            coordinates = linestring.getCoordinates()
                            coordinates.push(coordinates[0])
                            f.setGeometry(new ol.geom.Polygon([coordinates]))
                            f.set('toolName','FireBoundary')
                            features.push(f)
                          })
                      } else {
                          ignoredFeatures.push(feature)
                      }
                  })
              }
          } else {
              if (fileFormat === file.name) {
                  alert("Unknown file format (" + file.name + ")")
              } else {
                  alert("File format(" + fileFormat + ") not support")
              }
          }
          if (ignoredFeatures.length) {
            console.warn("The following features are ignored.\r\n" + vm.$root.geojson.writeFeatures(features))
          }
          if (features && features.length > 0) {
              $.each(features,function(index,feature){
                vm.drawingSequence += 1
                feature.set('id',vm.drawingSequence)
                vm.annotations.initFeature(feature)
              })            
              vm.annotations.features.extend(features)
          }
        }
        reader.readAsText(file)
      },
      saveStateButton: function () {
        var key = this.$els.savestatename.value
        if (!key) {
          key = moment().format('DD/MM/YYYY HH:mm')
        }
        this.saveState(key)
      },
      saveState: function (key) {
        var vm = this
        var store = this.$root.store
        // don't save if user is in tour
        if (vm.$root.touring) { return }

        // store attributes
        store.view.center = vm.olmap.getView().getCenter()
        store.view.scale = Math.round(vm.$root.map.getScale() * 1000)
        var activeLayers = vm.$root.active.activeLayers()
        if (activeLayers === false) {
          return
        }
        store.activeLayers = activeLayers || []
        store.annotations = JSON.parse(vm.$root.geojson.writeFeatures(vm.$root.annotations.features.getArray()))

        // save in the offline store
        localforage.setItem('sssOfflineStore', vm.$root.persistentData).then(function (value) {
          vm.$root.saved = moment().toLocaleString()
        })

        // if key is defined, store in state store
        if (key) {
          localforage.getItem('sssStateStore', function (err, value) {
            var states = {}
            if (value) {
              states = value
            }
            states[key] = vm.$root.persistentData
            localforage.setItem('sssStateStore', states).then(function (value) {
              vm.states = Object.keys(states)
            })
            
          })
        }
      }
    },
    ready: function () {
      var vm = this
      var exportStatus = vm.loading.register("export","Export Component","Initialize")
      exportStatus.wait(10,"Listen 'gk-init' event")
      this.$on('gk-init', function () {
        exportStatus.progress(80,"Process 'gk-init' event")
        // save state every render
        vm.olmap.on('postrender', global.debounce(function (ev) {vm.saveState()}, 1000, true))
        var stateStore = localforage.getItem('sssStateStore', function (err, value) {
          if (value) {
            vm.states = Object.keys(value)
          }
        })
        exportStatus.end()
      })
    }
  }
</script>
