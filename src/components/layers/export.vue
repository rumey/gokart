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
          <div class="expanded button-group">
            <label class="button expanded" for="uploadFile"><i class="fa fa-upload"></i> Upload view file</label><input type="file" id="uploadFile" class="show-for-sr" name="statefile" accept="application/json" v-model="statefile" v-el:statefile @change="load()"/>
          </div>
        </div>
      </div>
      <hr class="row"/>
      <div class="tool-slice row collapse">
        <div class="small-3">
          <label class="tool-label">Name:</label>
        </div>
        <div class="small-9">
          <input id="export-name" type="text" v-model="title" placeholder="Quick Print"/>
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

      <div class="hide" v-el:legendsvg>
        <gk-legend></gk-legend>
      </div>

      <gk-layerlegends v-ref:layerlegends></gk-layerlegends>
    </div>
  </div>
</template>
<script>
  import { kjua, saveAs, moment, $, localforage} from 'src/vendor.js'
  import gkLegend from './legend.vue'
  import gkLayerlegends from './layerlegends.vue'
  export default {
    store: ['whoami', 'dpmm', 'view', 'mmPerInch', 'gokartService'],
    components: { gkLegend,gkLayerlegends },
    data: function () {
      return {
        minDPI: 300,
        paperSizes: {
          A0: [1189, 841],
          A1: [841, 594],
          A2: [594, 420],
          A3: [420, 297],
          A4: [297, 210]
        },
        paperSize: 'A3',
        layout: {},
        oldLayout: {},
        title: '',
        statefile: '',
        vectorFormat: 'json',
        states: [],
        vectorFormats:[
            {format:"json",title:"GeoJSON (web GIS)",name:"GeoJSON"},
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
      olmap: function () {
        return this.$root.map.olmap
      },
      // map viewport settings to use for generating the print raster
      mapLayout: function () {
        var dims = this.paperSizes[this.paperSize]
        var size = this.olmap.getSize()
        return {
          width: dims[0], height: dims[1], size: size,
          extent: this.olmap.getView().calculateExtent(size),
          scale: this.scale, dpmm: this.dpmm
        }
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
      }
    },
    // methods callable from inside the template
    methods: {
      // info for the legend block on the print raster
      legendInfo: function () {
        var result = {
          title: this.finalTitle,
          author: this.whoami.email,
          date: 'Map last amended ' + moment().toLocaleString()
        }
        if (this.$root.map) {
          result.km = (Math.round(this.$root.map.getScale() * 40) / 1000).toLocaleString()
          result.scale = this.paperSize + ' ' + this.$root.map.scaleString
        }
        return result
      },
      exportVector: function(features, name) {
        var vm = this
        var name = name || ''
        var result = this.$root.geojson.writeFeatures(features)
        var blob = new window.Blob([result], {type: 'application/json;charset=utf-8'})
        if (this.vectorFormat === 'json') {
          saveAs(blob, name + '_' + moment().add(moment().utcOffset(), 'minutes').toISOString().split('.')[0] + '.geo.json')
        } else {
          var formData = new window.FormData()
          formData.append('json', blob, name + '.json')
          var req = new window.XMLHttpRequest()
          req.open('POST', this.gokartService + '/ogr/' + this.vectorFormat)
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
                    filename = (matches && matches[1])? matches[1]: (name + "." + this.vectorFormat)
                } else {
                    filename = name + "." + this.vectotFormat
                }
                saveAs(req.response, filename)
            }
          }
          req.send(formData)
        }
      },
      // resize map to page dimensions (in mm) for printing, save layout
      setSize: function () {
        $('body').css('cursor', 'progress')
        this.oldLayout.size = this.olmap.getSize()
        this.oldLayout.scale = this.$root.map.getScale()
        this.oldLayout.dpmm = this.dpmm
        this.layout = this.mapLayout
        this.dpmm = this.minDPI / this.mmPerInch
        this.olmap.setSize([this.dpmm * this.layout.width, this.dpmm * this.layout.height])
        this.olmap.getView().fit(this.layout.extent, this.olmap.getSize())
        this.$root.map.setScale(this.$root.map.getFixedScale())
        //extent is changed because the scale is adjusted to the closest fixed scale, recalculated the extent again
        this.layout.extent = this.olmap.getView().calculateExtent(this.olmap.getSize())
      },
      // restore map to viewport dimensions
      resetSize: function () {
        this.dpmm = this.oldLayout.dpmm
        this.olmap.setSize(this.oldLayout.size)
        this.$root.map.setScale(this.oldLayout.scale)
        // this.olmap.getView().fit(this.layout.extent, this.olmap.getSize())
        $('body').css('cursor', 'default')
      },
      // generate legend block, scale ruler is 40mm wide
      renderLegend: function () {
        var qrcanvas = kjua({text: 'http://dpaw.io/sss?' + this.shortUrl, render: 'canvas', size: 100})
        return ['data:image/svg+xml;utf8,' + encodeURIComponent(this.$els.legendsvg.innerHTML), qrcanvas]
      },
      // POST a generated JPG to the gokart server backend to convert to GeoPDF
      blobGDAL: function (blob, name, format) {
        var formData = new window.FormData()
        formData.append('extent', this.layout.extent.join(' '))
        formData.append('jpg', blob, name + '.jpg')
        formData.append('dpi', Math.round(this.layout.canvasPxPerMM * 25.4))
        formData.append('title', this.finalTitle)
        formData.append('author', this.legendInfo().author)
        var req = new window.XMLHttpRequest()
        req.open('POST', this.gokartService + '/gdal/' + format)
        req.withCredentials = true
        req.responseType = 'blob'
        var vm = this
        req.onload = function (event) {
          saveAs(req.response, name + '.' + format)
          vm.resetSize()
        }
        req.send(formData)
      },
      // make a printable raster from the map
      print: function (format) {
        // rig the viewport to have printing dimensions
        this.setSize()
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

        var composing = vm.olmap.on('postcompose', function (event) {
          timer && clearTimeout(timer)
          timer = setTimeout(function () {
            // remove composing watcher
            vm.olmap.unByKey(whiteout)
            vm.olmap.unByKey(composing)
            var canvas = event.context.canvas
            var ctx = canvas.getContext('2d')
            var img = new window.Image()
            var legend = vm.renderLegend()
            var url = legend[0]
            var qrcanvas = legend[1]
            // wait until legend is rendered
            img.onerror = function (err) {
              window.alert(JSON.stringify(err))
            }
            img.onload = function () {
              // legend is 12cm wide
              vm.layout.canvasPxPerMM = canvas.width / vm.layout.width
              var height = 120 * vm.layout.canvasPxPerMM * img.height / img.width
              ctx.drawImage(img, 0, 0, 120 * vm.layout.canvasPxPerMM, height)
              ctx.drawImage(qrcanvas, 8, height)
              window.URL.revokeObjectURL(url)
              // generate a jpg copy of the canvas contents
              var filename = vm.finalTitle.replace(' ', '_')
              canvas.toBlob(function (blob) {
                if (format === 'jpg') {
                  saveAs(blob, filename + '.jpg')
                  vm.resetSize()
                } else {
                  vm.blobGDAL(blob, filename, format)
                }
              }, 'image/jpeg', 0.9)
            }
            img.src = url
          // only output after 5 seconds of no tiles
          }, 5000)
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
          if (fileFormat === ".json") {
              //geo json file 
              features = new ol.format.GeoJSON().readFeatures(data,{dataProjection:"EPSG:4326"})
              if (features && features.length) {
                  if (!features[0].get("toolName")) {
                      features = null
                      alert("External json file not supported")
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
                          console.warn("Ignore point(" + JSON.stringify(feature.getGeometry().getCoordinates()) + ")")
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
                          console.warn("Ignore " + feature.getGeometryName() + "(" + JSON.stringify(feature.getGeometry().getCoordinates()) + ")")
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
