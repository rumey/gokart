<template>
  <div class="tabs-panel" id="menu-tab-annotations" v-cloak>
    <div class="row collapse">
      <div class="columns">
        <ul class="tabs" id="annotations-tabs">
          <li class="tabs-title is-active"><a class="label" aria-selected="true">Drawing Tools</a></li>
        </ul>
      </div>
    </div>
    <div class="row collapse" id="annotations-tab-panels">
      <div class="columns">
        <div class="tabs-content vertical" data-tabs-content="annotations-tabs">

          <div class="tabs-panel is-active" id="annotations-edit" v-cloak>
            <div class="tool-slice row collapse">
              <div class="small-12">
                <div class="expanded button-group">
                  <a v-for="t in annotationTools | filterIf 'showName' undefined" class="button button-tool" v-bind:class="{'selected': t.name == tool.name}"
                    @click="setTool(t)" v-bind:title="t.label">{{{ icon(t) }}}</a>
                </div>
                <div class="row resetmargin">
                  <div v-for="t in annotationTools | filterIf 'showName' true" class="small-6" v-bind:class="{'rightmargin': $index % 2 === 0}" >
                    <a class="expanded secondary button" v-bind:class="{'selected': t.name == tool.name}" @click="setTool(t)"
                      v-bind:title="t.label">{{{ icon(t) }}} {{ t.label }}</a>
                  </div>
                </div>
              </div>
            </div>

            <div class="tool-slice row collapse">
              <div class="small-12">
                <div class="expanded button-group hide">
                  <a class="button"><i class="fa fa-cut" aria-hidden="true"></i> Cut</a>
                  <a class="button"><i class="fa fa-copy" aria-hidden="true"></i> Copy</a>
                  <a class="button"><i class="fa fa-paste" aria-hidden="true"></i> Paste</a>
                </div>

                <div class="expanded button-group">
                  <gk-drawinglogs v-ref:drawinglogs></gk-drawinglogs>
                </div>

                <div class="expanded button-group">
                  <label class="button " for="uploadAnnotations" title="Support GeoJSON(.geojson .json), GPS data(.gpx)"><i class="fa fa-upload"></i> Import Editing </label><input type="file" id="uploadAnnotations" class="show-for-sr" name="annotationsfile" accept=".json,.geojson,.gpx" v-model="annotationsfile" v-el:annotationsfile @change="importAnnotations()"/>
                  <a class="button" @click="downloadAnnotations('geojson')" title="Export Editing as GeoJSON"><i class="fa fa-download" aria-hidden="true"></i> Export Editing <br>(geojson) </a>
                  <a class="button" @click="downloadAnnotations('gpkg')" title="Export Editing as GeoPackage"><i class="fa fa-download" aria-hidden="true"></i> Export Editing <br>(gpkg)</a>
                </div>
              </div>
            </div>

            <div v-show="shouldShowShapePicker" class="tool-slice row collapse">
              <div class="small-2"><label class="tool-label">Shape:</label></div>
              <div class="small-10">
                <div class="expanded button-group">
                  <template v-for="s in pointShapes" >
                    <a @click="setProp('shape', s)" v-bind:class="{'selected': shape && (s[0] === shape[0])}" class="button pointshape"><img v-bind:src="s[0]"/></a>
                  </template>
                </div>
              </div>
            </div>

            <div v-show="shouldShowSizePicker" class="tool-slice row collapse">
              <div class="small-2"><label class="tool-label">Size:<br/>({{ size }})</label></div>
              <div class="small-10">
                <div class="expanded button-group">
                  <a @click="setProp('size', 1)" v-bind:class="{'selected': size == 1}" class="button"><img src="dist/static/images/thick-1.svg"/></a>
                  <a @click="setProp('size', 2)" v-bind:class="{'selected': size == 2}" class="button"><img src="dist/static/images/thick-2.svg"/></a>
                  <a @click="setProp('size', 4)" v-bind:class="{'selected': size == 4}" class="button"><img src="dist/static/images/thick-4.svg"/></a>
                </div>
              </div>
            </div>

            <div v-show="shouldShowColourPicker" class="tool-slice row collapse">
              <div class="small-2"><label class="tool-label">Colour:</label></div>
              <div class="small-10">
                <div @click="updateNote(false)" class="expanded button-group">
                  <a v-for="c in colours" class="button" title="{{ c[0] }}" @click="setProp('colour', c[1])" v-bind:class="{'selected': c[1] == colour}"
                    v-bind:style="{ backgroundColor: c[1] }"></a>
                </div>
              </div>
            </div>

            <div v-show="shouldShowNoteEditor" class="tool-slice row collapse">
              <div class="small-2"><label class="tool-label">Note:</label></div>
              <div class="small-10">
                <select name="select" @change="note.text = $event.target.value.split('<br>').join('\n')">
                  <option value="">Text Templates</option> 
                  <option value="Sector: <br>Channel: <br>Commander: " selected>Sector Details</option>
                </select>
                <textarea @blur="updateNote(true)" class="notecontent" v-el:notecontent @keyup="updateNote(false)" @click="updateNote(true)" @mouseup="updateNote(false)">{{ note.text }}</textarea>
              </div>
            </div>

            <div v-show="shouldShowComments" class="tool-slice row collapse">
              <hr class="small-12"/>
              <template v-for="comment in tool.comments">
                  <div class="small-2">{{comment.name}}:</div>
                  <div class="small-10">
                    <template v-for="description in comment.description">
                        {{description}}
                        <br>
                    </template>
                  </div>
              </template>
            </div>

            <div class="tool-slice row collapse">
              <div class="small-12 canvaspane">
                <canvas v-show="shouldShowNoteEditor" v-el:textpreview></canvas>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>

  </div>
</template>

<style>
  .notecontent {
    width: 100%;
    height: 100px;
    resize: both;
    background-image: url('dist/static/images/boxresize.svg');
    background-repeat: no-repeat;
    background-position: right bottom;
  }
  .canvaspane {
    overflow: hidden;
    width: 100px;
    height: 30vh;
  }
  .row.resetmargin {
    margin: 0px;
  }
  .resetmargin .small-6.rightmargin {
    margin-right: 1px;
  }
  .resetmargin .small-6 {
    margin-right: -1px;
    padding-right: 1px;
  }
  .resetmargin .expanded.button {
    margin-bottom: 2px;
  }
  .fa.red {
    color: #b43232;
  }
  .pointshape {
    padding-left:5px;
    padding-right:5px;
  }
</style>

<script>
  import { $, ol, Vue } from 'src/vendor.js'
  import gkDrawinglogs from './drawinglogs.vue'

  Vue.filter('filterIf', function (list, prop, value) {
    if (!list) { return }
    return list.filter(function (val) {
      return val && val[prop] === value
    })
  })

  var noteOffset = 0
  var notePadding = 10

  var noteStyles = {
    'general': function (note) {
      var textTmpl = {
        fontSize: '16px',
        fontFamily: '"Helvetica Neue",Helvetica,Roboto,Arial,sans-serif',
        text: note.text,
        x: noteOffset + notePadding, y: notePadding,
        align: 'left',
        fromCenter: false
      }
      return [
        ['drawText', $.extend({layer:true,name:"decorationLayer",strokeWidth: 3, strokeStyle: 'rgba(255, 255, 255, 0.9)'}, textTmpl)],
        ['drawText', $.extend({layer:true,name:"textLayer",fillStyle: note.colour}, textTmpl)]
      ]
    }
  }

  export default {
    store: ['dpmm','drawingSequence','whoami','activeMenu'],
    components: { gkDrawinglogs },
    data: function () {
      return {
        ui: {},
        tool: {},
        tools: [],
        annotationTools: [],
        features: new ol.Collection(),
        selectedFeatures: new ol.Collection(),
        // array of layers that are selectable
        selectable: [],
        featureOverlay: {},
        annotationsfile:'',
        note: {
          style: 'general',
          text: 'Sector: \nChannel: \nCommander: ',
          colour: '#000000'
        },
        notes: {},
        size: 2,
        colour: '#000000',
        colours: [
          ['red', '#cc0000'],
          ['orange', '#f57900'],
          ['yellow', '#edd400'],
          ['green', '#73d216'],
          ['blue', '#3465a4'],
          ['violet', '#75507b'],
          ['brown', '#8f5902'],
          ['grey', '#555753'],
          ['black', '#000000']
        ],
        advanced: false,
        tints: {
        },
        pointShapes:[
            // point image url, point title, [border colur,filling colour]
            ["dist/static/symbols/points/circle.svg","Circle",[null,'#000000']],
            ["dist/static/symbols/points/square.svg","Square",[null,'#000000']],
            ["dist/static/symbols/points/triangle.svg","Triangle",[null,'#000000']],
            ["dist/static/symbols/points/star.svg","Star",[null,'#000000']],
            ["dist/static/symbols/points/plus.svg","Star",[null,'#000000']],
            ["dist/static/symbols/points/minus.svg","Star",[null,'#000000']],
            ["dist/static/symbols/points/Fire_Advice.svg","Star",['#000000','#000000']],
        ],
        shape: null
      }
    },
    computed: {
      map: function () { return this.$root.$refs.app.$refs.map },
      export: function () { return this.$root.export },
      active: function () { return this.$root.active },
      search: function () { return this.$root.search },
      measure: function () { return this.$root.measure },
      loading: function () { return this.$root.loading },
      drawinglogs: function () { return this.$refs.drawinglogs    },
      featureEditing: function() {
        if (this.tool == this.ui.editStyle && this.selectedFeatures.getLength() > 0) {
            return this.selectedFeatures.item(0)
        } else {
            return null
        }
      },
      shouldShowNoteEditor: function () {
        if (!this.tool || !this.tool.name) {
          return false
        }
        // FIXME: replace this with a tool property
        return this.tool === this.ui.defaultText || 
            (this.tool === this.ui.editStyle && this.featureEditing && this.getTool(this.featureEditing.get('toolName')) === this.ui.defaultText)
      },
      shouldShowShapePicker: function () {
        if (!this.tool || !this.tool.name) {
          return false
        }
        // FIXME: replace this with a tool property
        return this.tool === this.ui.defaultPoint ||
               (this.tool == this.ui.editStyle && this.featureEditing && this.getTool(this.featureEditing.get('toolName')) === this.ui.defaultPoint)
      },
      shouldShowSizePicker: function () {
        if (!this.tool || !this.tool.name) {
          return false
        }
        // FIXME: replace this with a tool property
        return this.tool === this.ui.defaultLine || 
               this.tool === this.ui.defaultPolygon || 
               (this.tool == this.ui.editStyle && this.featureEditing && ([this.ui.defaultLine,this.ui.defaultPolygon].indexOf(this.getTool(this.featureEditing.get('toolName'))) >= 0))
      },
      shouldShowColourPicker: function () {
        if (!this.tool || !this.tool.name) {
          return false
        }
        // FIXME: replace this with a tool property
        return this.tool === this.ui.defaultLine || 
               this.tool === this.ui.defaultPolygon || 
               this.tool == this.ui.defaultText || 
               this.tool == this.ui.defaultPoint || 
               (this.tool === this.ui.editStyle && this.featureEditing && ([this.ui.defaultLine,this.ui.defaultPolygon,this.ui.defaultPoint,this.ui.defaultText].indexOf(this.getTool(this.featureEditing.get('toolName'))) >= 0))
      },
      shouldShowComments: function () {
        if (!this.tool || !this.tool.name) {
          return false
        }
        return this.tool.comments && true
      },
      currentTool:{
        get:function() {
            var t = this._currentTool[this.activeMenu]
            if (!t) {
                t = this.ui.defaultPan
                this._currentTool[this.activeMenu] = t
            }
            return t
        },
        set:function(t) {
            this._currentTool[this.activeMenu] = t
        }
      },
    },
    watch:{
      'featureEditing': function(val,oldVal) {
        if (val && val instanceof ol.Feature && val.get) {
            if (val.get('note')) {
                //it is a text note
                this.note = val.get('note')
                this.drawNote(this.note)
                this.colour = this.note.colour || this.colour
            } else if (val.get('shape')) {
                this.shape = val.get('shape') || this.shape
                this.colour = val.get('colour') || this.colour
            } else {
                this.size = val.get('size') || this.size
                this.colour = val.get('colour') || this.colour
            }
        }
      }
    },
    methods: {
      createEvent:function(interaction,type,options) {
        try {
            return new this._event(type,options)
        } catch(ex) {
            this._event = function(type,options) {
                ol.events.Event.call(this,type)
                if (options) {
                    $.each(options,function(k,v){
                        this.k = v
                    })
                }
            }
            ol.inherits(this._event,ol.events.Event)
            return new this._event(type,options)
        }
      },
      importAnnotations:function() {
        if (this.$els.annotationsfile.files.length === 0) {
            return
        }
        var vm = this
        this.export.importVector(this.$els.annotationsfile.files[0],function(features,fileFormat){
            var ignoredFeatures = []
            var f = null
            if ((fileFormat === ".geojson") || (fileFormat === ".json")) {
                //geo json file
                for(var i = features.length - 1;i >= 0;i--) {
                    feature = features[i]
                    if (!vm.getTool(feature.get("toolName"))) {
                        //external feature.
                        if (feature.getGeometry() instanceof ol.geom.Point) {
                            vm.map.clearFeatureProperties(feature)
                            feature.set('toolName','Custom Point',true)
                            feature.set('shape',vm.annotations.pointShapes[0],true)
                            feature.set('colour',"#000000",true)
                        } else if (feature.getGeometry() instanceof ol.geom.LineString) {
                            vm.map.clearFeatureProperties(feature)
                            feature.set('toolName','Custom Line',true)
                            feature.set('size',2,true)
                            feature.set('colour',"#000000",true)
                        } else if (feature.getGeometry() instanceof ol.geom.Polygon) {
                            vm.map.clearFeatureProperties(feature)
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
                            features.splice(i,1)
                        }  
                    }
                }
            } else if (fileFormat === ".gpx") {
                //gpx file
                for(var i = features.length - 1;i >= 0;i--) {
                    feature = features[i]
                    if (feature.getGeometry() instanceof ol.geom.Point) {
                        //feature.set('toolName','Spot Fire')
                        ignoredFeatures.push(feature)
                        features.splice(i,1)
                    } else if(feature.getGeometry() instanceof ol.geom.LineString) {
                        vm.map.clearFeatureProperties(feature)
                        var coordinates = feature.getGeometry().getCoordinates()
                        coordinates.push(coordinates[0])
                        feature.setGeometry(new ol.geom.Polygon([coordinates]))
                        feature.set('toolName','Fire Boundary')
                    } else if(feature.getGeometry() instanceof ol.geom.MultiLineString) {
                        //convert each linstring in MultiLineString as a fire boundary
                        vm.map.clearFeatureProperties(feature)
                        features.splice(i,1)
                        var geom = feature.getGeometry()
                        var coordinates = null
                        $.each(geom.getLineStrings(),function(index,linestring) {
                            f = feature.clone()
                            coordinates = linestring.getCoordinates()
                            coordinates.push(coordinates[0])
                            f.setGeometry(new ol.geom.Polygon([coordinates]))
                            f.set('toolName','Fire Boundary')
                            features.splice(i,0,f)
                        })
                    } else {
                        ignoredFeatures.push(feature)
                        features.splice(i,1)
                    }
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
                    vm.initFeature(feature)
                })            
                vm.features.extend(features)
            }
        })
      },
      downloadAnnotations: function(fmt) {
        this.$root.export.exportVector(this.features.getArray(), 'annotations',fmt)
      },
      getPerpendicular : function (coords) {
        // find the nearest Polygon or lineString in the annotations layer
        var nearestFeature = gokart.annotations.featureOverlay.getSource().getClosestFeatureToCoordinate(
          coords, function (feat) {
            var geom = feat.getGeometry()
            return ((geom instanceof ol.geom.Polygon) || (geom instanceof ol.geom.LineString))
          }
        )
        if (!nearestFeature) {
          // no feature == no rotation
          return 0.0
        }
        var segments = []
        var source = []
        var segLength = 0
        // if a Polygon, join the last segment to the first
        if (nearestFeature.getGeometry() instanceof ol.geom.Polygon) {
          source = nearestFeature.getGeometry().getCoordinates()[0]
          segLength = source.length
        } else {
        // if a LineString, don't include the last segment
          source = nearestFeature.getGeometry().getCoordinates()
          segLength = source.length-1
        }
        for (var i=0; i < segLength; i++) {
          segments.push([source[i], source[(i+1)%source.length]])
        }
        // sort segments by ascending distance from point
        segments.sort(function (a, b) {
          return ol.coordinate.squaredDistanceToSegment(coords, a) - ol.coordinate.squaredDistanceToSegment(coords, b)
        })

        // head of the list is our target segment. reverse this to get the normal angle
        var offset = [segments[0][1][0] - segments[0][0][0], segments[0][1][1] - segments[0][0][1]]
        var normal = Math.atan2(-offset[1], offset[0])
        return normal
      },
      snapToLineFactory: function(options) {
        return new ol.interaction.Snap({
            features: (options && options.features) || this.features,
            edge: (!options || options.edge === undefined)?true:options.edge,
            vertex: (!options || options.vertex == undefined)?false:options.vertex,
            pixelTolerance: (options && options.pixelTolerance) || 16
          })
      },
      linestringDrawFactory : function (options) {
        var vm = this
        return function(tool) {
            var draw =  new ol.interaction.Draw($.extend({
              type: 'LineString',
              features: (tool && tool.features) || vm.features,
            },(options && options.drawOptions)||{}))
            draw.on('drawend', function (ev) {
              // set parameters
              vm.drawingSequence += 1
              ev.feature.set('id',vm.drawingSequence)
              ev.feature.set('toolName',tool.name)
              ev.feature.setStyle(tool.style)
              ev.feature.set('author',vm.whoami.email)
              ev.feature.set('createTime',Date.now())
            })

            draw.events = {
              addfeaturegeometry:(options && options.addfeaturegeometry)||false
            }
            return draw
        }
      },
      polygonDrawFactory : function (options) {
        var vm = this
        return function(tool) {
            var draw =  new ol.interaction.Draw($.extend({
              type: 'Polygon',
              features: (tool && tool.features) || vm.features,
            },(options && options.drawOptions)||{}))
            draw.on('drawend', function (ev) {
              // set parameters
              vm.drawingSequence += 1
              ev.feature.set('id',vm.drawingSequence)
              ev.feature.set('toolName',tool.name)
              ev.feature.setStyle(tool.style)
              ev.feature.set('author',vm.whoami.email)
              ev.feature.set('createTime',Date.now())
            })

            draw.events = {
              addfeaturegeometry:(options && options.addfeaturegeometry)||false
            }
            return draw
        }
      },
      pointDrawFactory : function (options) {
        var vm = this
        return function(tool) {
            var sketchStyle = undefined
            if (tool && tool.sketchStyle) {
                var defaultFeat = new ol.Feature($.extend({'toolName': tool.name},options||{}))
                sketchStyle = function(res) {return tool.sketchStyle.apply(defaultFeat,res);}
            }

            var draw =  new ol.interaction.Draw($.extend({
              type: 'Point',
              features: (options && options.features) || (tool && tool.features) || vm.features,
              style: sketchStyle
            },(options && options.drawOptions)||{}))

            draw.on('drawend', function (ev) {
              // set parameters
              vm.drawingSequence += 1
              ev.feature.set('id',vm.drawingSequence)
              ev.feature.set('toolName',tool.name)
              ev.feature.setStyle(tool.style)
              ev.feature.set('author',vm.whoami.email)
              ev.feature.set('createTime',Date.now())
              if (tool.perpendicular) {
                var coords = ev.feature.getGeometry().getCoordinates()
                ev.feature.set('rotation', vm.getPerpendicular(coords))
              }
            })

            draw.events = {
              addfeaturegeometry:(options && options.addfeaturegeometry)||false
            }
            return draw
        }
      },
      translateInterFactory:function(options) {
        var vm = this
        return function(tool) {
          // allow translating of features by click+dragging
          var translateInter = new ol.interaction.Translate({
            layers: (tool && tool.mapLayers) || [vm.featureOverlay],
            features: (tool && tool.selectedFeatures) || vm.selectedFeatures
          })
          translateInter.on("translateend",function(ev){
              ev.features.forEach(function(f){
                if (f.get('toolName')) {
                    tool = vm.getTool(f.get('toolName'))
                    if (tool && tool.typeIcon) {
                        delete f['typeIconStyle']
                        f.set('typeIconMetadata',undefined,true)
                        f.changed()
                    }
                }
              })
          })
          return translateInter
        }
      },
      dragSelectInterFactory: function(options) {
        var vm = this
        return function(tool) {
          selectedFeatures = (tool && tool.selectedFeatures) || vm.selectedFeatures
          // allow dragbox selection of features
          var dragSelectInter = new ol.interaction.DragBox()
          // modify selectedFeatures after dragging a box
          dragSelectInter.on('boxend', function (event) {
            selectedFeatures.clear()
            var extent = event.target.getGeometry().getExtent()
            var multi = (this.multi_ == undefined)?true:this.multi_
            vm.selectable.forEach(function(layer) {
              if (!multi && selectedFeatures.getLength() > 0) {return true}
              if (layer == vm.featureOverlay) {
                  //select all annotation features except text note
                  layer.getSource().forEachFeatureIntersectingExtent(extent, function (feature) {
                    if (!multi && vm.selectedFeatures.getLength() > 0) {return true}
                    if (!feature.get('note')) {
                        vm.selectedFeatures.push(feature)
                        return !multi
                    }
                  })
                  //select text note
                  vm.features.forEach(function(feature){
                    if (!multi && vm.selectedFeatures.getLength() > 0) {return}
                    if (feature.get('note')) {
                      if (ol.extent.intersects(extent,vm.getNoteExtent(feature))) {
                        vm.selectedFeatures.push(feature)
                      }
                    }
                  })
              } else {
                  layer.getSource().forEachFeatureIntersectingExtent(extent, function (feature) {
                    if (!multi && vm.selectedFeatures.getLength() > 0) {return true}
                    vm.selectedFeatures.push(feature)
                    return !multi
                  })
              }
            })
          })
          // clear selectedFeatures before dragging a box
          dragSelectInter.on('boxstart', function () {
            //selectedFeatures.clear()
          })
          dragSelectInter.setMulti = function(multi) {
            this.multi_ = multi
          }
          return dragSelectInter
        }
      },
      isGeometrySelected:function(geom,mapBrowserEvent) {
        if (geom instanceof ol.geom.Point) {
            var geomPosition  = this.map.olmap.getPixelFromCoordinate(geom.getCoordinates())
            var position = mapBrowserEvent.pixel
            return (Math.abs(position[0] - geomPosition[0]) <= 5  && Math.abs(position[1] - geomPosition[1]) <= 5)
        } else {
            return geom.intersectsCoordinate(mapBrowserEvent.coordinate) 
        }
      },
      getSelectedGeometry:function(f,end) {
        var indexes = f['selectedIndex']
        if (indexes) {
            end = (end === null || end === undefined)?(indexes.length - 1):end
            if (end >= indexes.length || end < 0) {return null}
            var geom = f.getGeometry()
            for (i = 0;i <= end;i++) {
                if (geom instanceof ol.geom.GeometryCollection) {
                    if (indexes[i] < geom.getGeometriesArray().length) {
                        geom = geom.getGeometriesArray()[indexes[i]]
                    } else {
                        return null
                    }
                } else if (geom instanceof ol.geom.MultiPolygon) {
                    if (indexes[i] < geom.getPolygons().length) {
                        geom = geom.getPolygon(indexes[i])
                    } else {
                        return null
                    }
                } else if (geom instanceof ol.geom.MultiPoint) {
                    if (indexes[i] < geom.getPoints().length) {
                        geom = geom.getPoint(indexes[i])
                    } else {
                        return null
                    }
                } else if (geom instanceof ol.geom.MultiLineString) {
                    if (indexes[i] < geom.getLineStrings().length) {
                        geom = geom.getLineString(indexes[i])
                    } else {
                        return null
                    }
                } else {
                    return null
                }
            }
            return geom
        } else {
            //no in geometry select mode
            return null
        }
      },
      deleteSelectedGeometry:function(f,interaction) {
        var indexes = f['selectedIndex']
        if (!indexes) {return}

        var geom = this.getSelectedGeometry(f,indexes.length - 2)
        if (geom) {
            var deleteIndex = indexes[indexes.length - 1]
            if (geom instanceof ol.geom.GeometryCollection) {
                if (deleteIndex < geom.getGeometriesArray().length) {
                    geom.getGeometriesArray().splice(deleteIndex,1)
                    geom.setGeometriesArray(geom.getGeometriesArray())
                    delete f['selectedIndex']
                    interaction.dispatchEvent(this.createEvent(interaction,"deletefeaturegeometry",{feature:f,indexes:indexes}))
                    f.getGeometry().changed()
                }
            } else if (geom instanceof ol.geom.MultiPolygon || geom instanceof ol.geom.MultiPoint || geom instanceof ol.geom.MultiLineString) {
                var coordinates = geom.getCoordinates()
                if (deleteIndex < coordinates.length) {
                    coordinates.splice(deleteIndex,1)
                    geom.setCoordinates(coordinates)
                    delete f['selectedIndex']
                    interaction.dispatchEvent(this.createEvent(interaction,"deletefeaturegeometry",{feature:f,indexes:indexes}))
                    f.getGeometry().changed()
                } else {
                    return null
                }
            }
        }
      },
      getSelectedGeometryIndex:function(geom,mapBrowserEvent) {
        var vm = this
        var indexes = null
        if (geom instanceof ol.geom.GeometryCollection) {
            $.each(geom.getGeometriesArray(),function(index,g){
                if (g instanceof ol.geom.MultiPoint || g instanceof ol.geom.MultiLineString || g instanceof ol.geom.MultiPolygon || g instanceof ol.geom.GeometryCollection) {
                    indexes = vm.getSelectedGeometryIndex(g,mapBrowserEvent)
                    if (indexes) {
                        indexes.splice(0,0,index)
                        return false
                    }
                    
                } else {
                    if (vm.isGeometrySelected(g,mapBrowserEvent)) {
                        indexes = [index]
                        return false
                    }
                }
            })
        } else if (geom instanceof ol.geom.MultiPolygon) {
            $.each(geom.getPolygons(),function(index,g){
                if (vm.isGeometrySelected(g,mapBrowserEvent)) {
                    indexes = [index]
                    return false
                }
            })
        } else if (geom instanceof ol.geom.MultiPoint) {
            $.each(geom.getPoints(),function(index,g){
                if (vm.isGeometrySelected(g,mapBrowserEvent)) {
                    indexes = [index]
                    return false
                }
            })
        } else if (geom instanceof ol.geom.MultiLineString) {
            $.each(geom.getLineStrings(),function(index,g){
                if (vm.isGeometrySelected(g,mapBrowserEvent)) {
                    indexes = [index]
                    return false
                }
            })
        } else {
            return false
        }
        return indexes
      },
      selectInterFactory:function(options) {
        var vm = this
        return function(tool) {
          selectedFeatures = (tool && tool.selectedFeatures) || vm.selectedFeatures
          // allow selecting multiple features by clicking
          var selectInter = new ol.interaction.Select({
            layers: function(layer) { 
              return vm.selectable.indexOf(layer) > -1
            },
            features: selectedFeatures,
            condition: (options && options.condition) || ol.events.condition.singleClick
          })
          selectInter.defaultHandleEvent = selectInter.defaultHandleEvent || selectInter.handleEvent
          selectInter.handleEvent = function(event) {
            if (this.condition_(event)) {
                try {
                    vm.selecting = true
                    if (tool && tool.selectMode === "geometry") {
                        vm.selectedFeatures.clear()
                    }
                    return this.defaultHandleEvent(event)
                } finally {
                    vm.selecting = false
                }
            } else {
                vm.selecting = false
                return this.defaultHandleEvent(event)
            }
          }
          selectInter.setMulti = function(multi) {
            this.multi_ = multi
          }
          if (tool && tool.selectMode === "geometry") {
              selectInter.on('select',function(ev) {
                if (!ev.mapBrowserEvent) {return}
                $.each(ev.selected,function(index,f){
                    var indexes = vm.getSelectedGeometryIndex(f.getGeometry(),ev.mapBrowserEvent)
                    if (indexes) {
                        f['selectedIndex'] = indexes
                    } else {
                        delete f['selectedIndex']
                    }
                })
            })
          }
          return selectInter
        }
      },
      keyboardInterFactory:function(options) { 
        var vm = this
        // OpenLayers3 hook for keyboard input
        vm._deleteSelected = vm._deleteSelected || function (features,selectedFeatures,interaction) {
            features = features || this.features
            selectedFeatures = selectedFeatures || vm.selectedFeatures
            if (vm.tool.selectMode === "feature") {
                selectedFeatures.forEach(function (feature) {
                  features.remove(feature)
                })
                selectedFeatures.clear()
            } else if (vm.tool.selectMode === "geometry") {
                selectedFeatures.forEach(function (feature) {
                    vm.deleteSelectedGeometry(feature,this)
                })
            }
        }

        return function(tool) {
          var keyboardInter = new ol.interaction.Interaction({
            handleEvent: function (mapBrowserEvent) {
              var stopEvent = false
              if (mapBrowserEvent.type === ol.events.EventType.KEYDOWN) {
                var keyEvent = mapBrowserEvent.originalEvent
                switch (keyEvent.keyCode) {
                  case 65: // a
                    if (!options || options.selectEnabled === undefined || options.selectEnabled) {
                        if (keyEvent.ctrlKey) {
                          vm.selectAll( (tool && tool.features) || vm.features,(tool && tool.selectedFeatures) || vm.selectedFeatures )
                          stopEvent = true
                        }
                    }
                    break
                  case 46: // Delete
                    if (!options || options.deleteEnabled === undefined || options.deleteEnabled) {
                        if (options && options.deleteSelected) {
                            options.deleteSelected.call(keyboardInter, (tool && tool.features) || vm.features,(tool && tool.selectedFeatures) || vm.selectedFeatures )
                        } else {
                            vm._deleteSelected.call(keyboardInter, (tool && tool.features) || vm.features,(tool && tool.selectedFeatures) || vm.selectedFeatures )
                        }
                        stopEvent = true
                    }
                    break
                  default:
                    break
                }
              }
              // if we intercept a key combo, disable any browser behaviour
              if (stopEvent) {
                keyEvent.preventDefault()
              }
              return !stopEvent
            }
          })
          keyboardInter.events = {
            featuresmodified:(options && options.featuresmodified)||false
          }
          return keyboardInter
        }
      },
      modifyInterFactory:function(options) {
        var vm = this
        return function(tool) {
          // allow modifying features by click+dragging
          var modifyInter = new ol.interaction.Modify({
            features: (tool && tool.features) || vm.features
          })
          modifyInter.on("modifystart",function(ev){
            ev.features.forEach(function(feature) {
                //console.log("Modifystart : " + feature.get('label') + "\t" + feature.getGeometry().getRevision())
                feature.geometryRevision = feature.getGeometry().getRevision()
            })
          }) 
          modifyInter.on("modifyend",function(ev){
            var modifiedFeatures = new ol.Collection(ev.features.getArray().filter(function(feature){
                //console.log("Modifyend : " + feature.get('label') + "\t" + feature.geometryRevision + "\t" + feature.getGeometry().getRevision())
                return feature.geometryRevision != feature.getGeometry().getRevision()
            }))
            modifyInter.dispatchEvent(new ol.interaction.Modify.Event("featuresmodified",modifiedFeatures,ev))
          })
          modifyInter.on("featuresmodified",function(ev){
            ev.features.forEach(function(f){
                if (f.get('toolName')) {
                    tool = vm.getTool(f.get('toolName'))
                    if (tool && tool.typeIcon ) {
                        delete f['typeIconStyle']
                        f.set('typeIconMetadata',undefined,true)
                        f.changed()
                    }
                }
              })
          })
          return modifyInter
        }
      },
      icon: function (t) {
        var iconUrl = null
        if (typeof t.icon === "function") {
            iconUrl = t.icon()
        } else {
            iconUrl = t.icon
        }
        if (iconUrl.startsWith('fa-')) {
          return '<i class="fa ' + iconUrl + '" aria-hidden="true"></i>'
        } else if (iconUrl.search('#') === -1) {
          // plain svg/image
          return '<img class="icon" src="' + iconUrl + '" />'
        } else {
          // svg reference
          return '<svg class="icon"><use xlink:href="' + iconUrl + '"></use></svg>'
        }
      },
      getCustomPointTint:function(shape,colours) {
        var tint = []
        $.each(shape[2],function(index,srcColour) {
            var targetColour = Array.isArray(colours)?colours[index]:colours
            if (srcColour && targetColour && srcColour !== targetColour) {
                tint.push([srcColour,targetColour])
            }
        })
        return tint
      },
      setProp: function (prop, value) {
        this[prop] = value
        //note's property will be set by updateNote
        if (this.featureEditing instanceof ol.Feature && !this.featureEditing.get('note')) {
          this.featureEditing.set(prop, value)
        }
      },
      setDefaultTool: function(menu,tool) {
        if (typeof tool === 'string') {
          tool = this.getTool(tool)
        }
        this._currentTool[menu] = tool
      },
      getTool: function (toolName) {
        return (toolName)?this.tools.filter(function (t) {return t.name === toolName })[0]:null
      },
      setTool: function (t) {
        if (!t) {
            if (this._previousActiveMenu && this._previousActiveMenu !== this.activeMenu && this._previousTool) {
                //before switching to other menu, if a non-pan tool was enabled, choose the 'pan' tool for the current menu to preseve the changes(for example, the selected features) made by the previous non-pan tool
                t = this.ui.defaultPan
            } else {
                t = this.currentTool
            }
        }
        if (typeof t == 'string') {
          t = this.getTool(t)
        }
        if ((this.tool === t) && (t === this.ui.defaultPan || this._previousActiveMenu === this.activeMenu)) {
            //choose the same tool, do nothing,
            this.currentTool = t
            return
        } else if(this.tool.onUnset) {
            this.tool.onUnset()
        }
        var map = this.map
        // remove all custom tool interactions from map
        this.tools.forEach(function (tool) {
          tool.interactions.forEach(function (inter) {
            map.olmap.removeInteraction(inter)
          })
        })

        // add interactions for this tool
        t.interactions.forEach(function (inter) {
          map.olmap.addInteraction(inter)
        })

        // remove selections
        if (t !== this.ui.defaultPan) {
            //remove selections only if the tool is not Pan
            if ((this._previousActiveMenu && this._previousActiveMenu !== this.activeMenu) || (this._previousTool && this._previousTool !== t && !t.keepSelection)) {
                //remove selections only if the current tool is not the same tool as the previous tool.
                this.selectedFeatures.clear()
            }
            this._previousTool = t
            this._previousActiveMenu = this.activeMenu
        }

        //change the cursor
        if (t.cursor && typeof t.cursor === 'string') {
            $(map.olmap.getTargetElement()).find(".ol-viewport").css('cursor',t.cursor)
        } else if (t.cursor&& Array.isArray(t.cursor)) {
            $.each(t.cursor,function(index,value){
                $(map.olmap.getTargetElement()).find(".ol-viewport").css('cursor',value)
            })
        } else {
            $(map.olmap.getTargetElement()).find(".ol-viewport").css('cursor','default')
        }
        

        if (t.onSet) { t.onSet(this.tool) }

        if (t.selectMode !== this.tool.selectMode){
            this.selectedFeatures.forEach(function(f){f.changed()})
        }

        this.tool = t
        this.currentTool = t
      },
      selectAll: function (features,selectedFeatures) {
        features = features || this.features
        selectedFeatures = selectedFeatures || this.selectedFeatures
        var vm = this
        features.forEach(function (feature) {
          if (!(feature in selectedFeatures)) {
            selectedFeatures.push(feature)
          }
        })
      },
      updateNote: function (save) {
        var note = null
        if (this.tool ===  this.ui.editStyle) {
            //edit mode
            if (!this.featureEditing || !this.featureEditing.get('note')) {
              //this feature is not a note. return
              return
            }
            note = this.featureEditing.get('note')
        } else {
            //draw mode
            note = this.note
        }
        var previousColour = note.colour
        note.text = this.$els.notecontent.value
        note.colour = this.colour
        this.drawNote(note, save)
        if ((save || previousColour !== this.colour) && this.tool ===  this.ui.editStyle) {
            this.featureEditing.set('noteRevision', (this.featureEditing.get('noteRevision') || 0) + 1)
        }
      },
      drawNote: function (note, save) {
        if (!note) { return }
        var vm = this
        var noteCanvas = this.$els.textpreview
        $(noteCanvas).removeLayer("decorationLayer")
        $(noteCanvas).removeLayer("textLayer")
        $(noteCanvas).clearCanvas()
        if ((note.style) && (note.style in noteStyles)) {
          //draw
          $(noteCanvas).attr('height', $(this.$els.notecontent).height() + noteOffset)
          $(noteCanvas).attr('width', $(this.$els.notecontent).width() + noteOffset)
          noteStyles[note.style](note).forEach(function (cmd) {
            $(noteCanvas)[cmd[0]](cmd[1])
          })
          //measure and set canvas dimension
          var annotationSize = $(noteCanvas).measureText("decorationLayer")
          note.size = [annotationSize.width + noteOffset + notePadding, annotationSize.height + notePadding]
          $(noteCanvas).attr('width', note.size[0])
          $(noteCanvas).attr('height', note.size[1])
          $(noteCanvas).drawLayers()
            
          if (save) {
            var key = JSON.stringify(note)
            // temp placeholder
            this.notes[key] = ''
            noteCanvas.toBlob(function (blob) {
              // switch for actual image
              vm.notes[key] = window.URL.createObjectURL(blob)
              // FIXME: redraw stuff when saving blobs (broken in chrome)
              vm.features.getArray().forEach(function (f) {
                if (JSON.stringify(f.get('note')) === key) {
                  f.changed()
                }
              })
              // Set canvas back to the vm's note
              vm.drawNote(vm.note, false)
            }, 'image/png')
            
          }
        }
      },
      getNoteUrl: function (note) {
        var key = JSON.stringify(note)
        if (!(key in this.notes)) {
          this.drawNote(note, true)
        }
        return this.notes[key]
      },
      setup: function() {
        var vm = this
        // enable annotations layer, if disabled
        var catalogue = this.$root.catalogue
        if (!this.map.getMapLayer('annotations')) {
          catalogue.onLayerChange(catalogue.getLayer('annotations'), true)
        } else if (this.active.isHidden(this.map.getMapLayer('annotations'))) {
          this.active.toggleHidden(this.map.getMapLayer('annotations'))
        }
        // runs on switch to this tab
        this.selectable = [this.featureOverlay]
        this.setTool()
        //add feature to place an point based on coordinate
        this.search.setSearchPointFunc(function(searchMethod,coords,name){
            if (vm.tool && ["DMS","MGA"].indexOf(searchMethod) >= 0 && ["Origin Point","Spot Fire","Road Closure","Custom Point"].indexOf(vm.tool.name) >= 0) {
                var feat = null
                vm.map.olmap.forEachFeatureAtPixel(vm.map.olmap.getPixelFromCoordinate(coords),function(f){
                    var toolName = f.get('toolName')
                    if ( toolName && ["Origin Point","Spot Fire","Road Closure","Custom Point"].indexOf(toolName) >= 0) {
                        if (f.getGeometry().getCoordinates()[0] === coords[0] && f.getGeometry().getCoordinates()[1] === coords[1]) {
                            //already added.
                            feat = f
                            return true
                        }
                    }
                })
                if (feat) {
                    //already have a annotation point at that coordinate
                    return false
                }
                feat = new ol.Feature({
                    geometry: new ol.geom.Point(coords)
                })
                vm.drawingSequence += 1
                feat.set('id',vm.drawingSequence)
                feat.set('toolName',vm.tool.name)
                feat.setStyle(vm.tool.style)
                feat.set('author',vm.whoami.email)
                feat.set('createTime',Date.now())
                if (vm.tool.perpendicular) {
                  feat.set('rotation', vm.getPerpendicular(coords))
                }
                if (vm.tool === vm.ui.defaultPoint) {
                    feat.set('shape',vm.shape,true)
                    feat.set('colour',vm.colour,true)
                }
                vm.features.push(feat)
                return true
            }
        })
      },
      tearDown:function() {
        this.search.setSearchPointFunc(null)
        this.selectable = null
      },
      getNoteExtent: function(feature) {
        var note = feature.get('note')
        if (!note) return null
        var map = this.map.olmap
        var bottomLeftCoordinate = feature.getGeometry().getFirstCoordinate()
        var bottomLeftPosition = map.getPixelFromCoordinate(bottomLeftCoordinate)
        var upRightCoordinate = map.getCoordinateFromPixel([bottomLeftPosition[0] + note.size[0],bottomLeftPosition[1] - note.size[1]])
        return [bottomLeftCoordinate[0],bottomLeftCoordinate[1],upRightCoordinate[0],upRightCoordinate[1]]
      },
      tintSelectedFeature:function(feature) {
        var tool = feature.get('toolName')?this.getTool(feature.get('toolName')):false
        if (tool && tool.selectedTint) {
            if (typeof tool.selectedTint === "function") {
                feature['tint'] = tool.selectedTint(feature)
            } else {
                feature['tint'] = tool.selectedTint

            }
        } else {
            feature['tint'] = 'selected'
        }
        if (tool && tool.typeIcon) {
            feature['typeIconTint'] = tool.typeIconSelectedTint || 'selected'
        }
        feature.changed()
      },
      tintUnselectedFeature:function(feature) {
        delete feature['tint']
        var tool = feature.get('toolName')?this.getTool(feature.get('toolName')):false
        if (tool && tool.typeIcon) {
            delete feature['typeIconTint']
        }
        feature.changed()
      },
      getStyleProperty:function(f,property,defaultValue,tool) {
        var result = f[property] || f.get(property) || (tool || this.getTool(f.get('toolName')) || {})[property] || ((defaultValue === undefined)?'default':defaultValue)
        return (typeof result === "function")?result(f):result
      },
      getIconStyleFunction : function(tints) {
        var vm = this
        return function (res) {
            var f = this

            var selected = "none"
            var keysufix = ""
            if (f['tint'] === undefined || f['tint'] === "") {
                //not selected
                selectMode = "none"
                keySuffix = "none"
            } else if (vm.tool.selectMode !== "geometry") {
                //not in geometry selection mode
                selectMode = "all"
                keySuffix = "all"
            } else {
                var selectedGeometry =  vm.getSelectedGeometry(f) 
                if (!selectedGeometry) {
                    selectMode = "none"
                    keySuffix = f.get('tint') + ":none"
                } else if (selectedGeometry instanceof ol.geom.Point) {
                    selectMode = "partial"
                    keySuffix = f.get('tint') + ":partial"
                }  else {
                    selectMode = "none"
                    keySuffix = f.get('tint') + ":none"
                }
            }
            var style = vm.map.cacheStyle(function (f) {
                var tint = null
                var style = null
                try {
                    if ((selectMode === "none" && f["tint"]) || selectMode === "partial") {
                        tint = f["tint"]
                        delete f["tint"]
                    }

                    var src = vm.map.getBlob(f, ['icon', 'tint'],tints || {})
                    if (!src) { return false }
                    var rot = f.get('rotation') || 0.0
                    style = new ol.style.Style({
                      image: new ol.style.Icon({
                          src: src,
                          scale: 0.5,
                          rotation: rot,
                          rotateWithView: true,
                          snapToPixel: true
                        })
                    })
                } finally {
                    if (tint) {
                        f["tint"] = tint
                    }
                }

                if (selectMode === "partial") {
                    var src = vm.map.getBlob(f, ['icon', 'tint'],tints || {})
                    if (!src) { return false }
                    var rot = f.get('rotation') || 0.0
                    style = [
                        style,
                        new ol.style.Style({
                          geometry: function(f) {
                            return vm.getSelectedGeometry(f)
                          },
                          image: new ol.style.Icon({
                              src: src,
                              scale: 0.5,
                              rotation: rot,
                              rotateWithView: true,
                              snapToPixel: true
                            })
                        })
                    ]
                }
                return style

            }, f, ['icon','tint', 'rotation'],keySuffix)

            return style
        }
      },
      getLabelStyleFunc:function(tints) {
        var vm = this
        return function() {
            var f = this
            var tool = null
            if (f.get('toolName')) {
                tool = vm.getTool(f.get('toolName')) || vm.tool
            } else {
                tool = vm.tool
            }
            var tint = vm.getStyleProperty(f,"tint","",tool) + ".text"
            return new ol.style.Style({
                text: new ol.style.Text({
                  offsetX: 12,
                  text:f.get('label'),
                  textAlign: 'left',
                  font: '12px Helvetica,Roboto,Arial,sans-serif',
                  stroke: new ol.style.Stroke({
                    color: tints[tint],
                    width: 4
                  })
                }),
            })
        }
      },
      getVectorStyleFunc: function (tints) {
        var vm = this
        return function() {
            var f = this
            var tool = null
            if (f.get('toolName')) {
                tool = vm.getTool(f.get('toolName')) || vm.tool
            } else {
                tool = vm.tool
            }
            var selected = "none"
            if (f['tint'] === undefined || f['tint'] === "") {
                //not selected
                selectMode = "none"
            } else if (vm.tool.selectMode !== "geometry") {
                //not in geometry selection mode
                selectMode = "all"
            } else {
                var selectedGeometry =  vm.getSelectedGeometry(f) 
                if (!selectedGeometry) {
                    selectMode = "none"
                } else if (!(selectedGeometry instanceof ol.geom.Point)) {
                    selectMode = "partial"
                }  else {
                    selectMode = "none"
                }
            }

            var baseStyle = vm.map.cacheStyle(function (f) {
              if (  selectMode === "partial" ) {
                return [
                    new ol.style.Style({
                      fill: new ol.style.Fill({
                        color: vm.getStyleProperty(f,'fillColour','rgba(255, 255, 255, 0.2)',tool)
                      }),
                      stroke: new ol.style.Stroke({
                        color: vm.getStyleProperty(f,'colour','rgba(0,0,0,1.0)',tool),
                        width: 2 * vm.getStyleProperty(f,'size',1,tool) 
                      })
                   }),
                   new ol.style.Style({
                      geometry: function(f) {
                        return vm.getSelectedGeometry(f)
                      },
                      fill: new ol.style.Fill({
                        color: vm.getStyleProperty(f,'selectedFillColour','rgba(255, 255, 255, 0.2)',tool)
                      }),
                      stroke: new ol.style.Stroke({
                        color: vm.getStyleProperty(f,'selectedColour','#2199e8',tool),
                        width: 2 * vm.getStyleProperty(f,'size',1,tool) + 2
                      })
                   }),
                   new ol.style.Style({
                      geometry: function(f) {
                        //console.log("===============" + f.get('label'))
                        return vm.getSelectedGeometry(f)
                      },
                      stroke: new ol.style.Stroke({
                        color: '#ffffff',
                        width: 2 * vm.getStyleProperty(f,'size',1,tool) 
                      })
                   })
                ]
              } else if (selectMode === 'all') {
                return [
                  new ol.style.Style({
                    fill: new ol.style.Fill({
                      color: vm.getStyleProperty(f,'selectedFillColour','rgba(255, 255, 255, 0.2)',tool)
                    }),
                    stroke: new ol.style.Stroke({
                      color: vm.getStyleProperty(f,'selectedColour','#2199e8',tool),
                      width: 2 * vm.getStyleProperty(f,'size',1,tool) + 2
                    })
                  }),
                  new ol.style.Style({
                    stroke: new ol.style.Stroke({
                      color: '#ffffff',
                      width: 2 * vm.getStyleProperty(f,'size',1,tool) 
                    })
                  }),
               ]
              } else {
                return new ol.style.Style({
                  fill: new ol.style.Fill({
                    color: vm.getStyleProperty(f,'fillColour','rgba(255, 255, 255, 0.2)',tool)
                  }),
                  stroke: new ol.style.Stroke({
                    color: vm.getStyleProperty(f,'colour','rgba(0,0,0,1.0)',tool),
                    width: 2 * vm.getStyleProperty(f,'size',1,tool) 
                  })
                })
              }
            },f,['size','colour'],selectMode)
    
            //get type icon style
            var typeIconStyle = null
            if (!vm.getStyleProperty(f,'typeIcon',false,tool)) {
                return baseStyle
            }
            //draw typeSymbol along the line.
            //does not support geometry select mode
            if (f['typeIconStyle']) {
                var diffs = vm.map.getScale() / f.get('typeIconMetadata')['points']['scale']
                var typeIconTint = f['typeIconTint'] || f.get('typeIconTint') || tool['typeIconTint'] || 'default'
                if (diffs >= 0.5 && diffs <= 1.5) {
                    if (typeIconTint === f.get('typeIconMetadata')['points']['tint']) {
                        typeIconStyle = f['typeIconStyle']
                    } else {
                        typeIconStyle = f['typeIconStyle']
                        var newStyle = []
                        var src = vm.map.getBlob(f, ['typeIcon', 'typeIconTint', 'typeIconDims'],tints || {})
                        if (!src) { return baseStyle }

                        $.each(typeIconStyle,function(index,item){
                            newStyle.push(new ol.style.Style({
                                geometry:item.getGeometry(),
                                image: new ol.style.Icon({
                                  src: src,
                                  rotation: item.getImage().getRotation(),
                                  rotateWithView: item.getImage().getRotateWithView(),
                                  snapToPixel: item.getImage().getSnapToPixel()
                                })
                            }))
                        })
                        f['typeIconStyle'] = newStyle
                        f.get('typeIconMetadata')['points']['tint'] = typeIconTint
                        typeIconStyle = newStyle
                    }
                } else {
                    f.get('typeIconMetadata')['points'] = false
                }
            } 
            if (!typeIconStyle) {
                var linestring = null
                if (f.getGeometry() instanceof ol.geom.Polygon) {
                    linestring = new ol.geom.LineString(f.getGeometry().getCoordinates()[0])
                } else if (f.getGeometry() instanceof ol.geom.LineString) {
                    linestring = f.getGeometry()
                } else {
                    return baseStyle
                }

                var src = vm.map.getBlob(f, ['typeIcon', 'typeIconTint','typeIconDims'],tints || {})
                if (!src) { return baseStyle }

                typeIconStyle = []
                var segmentIndex = 0 
                var segmentMetadata = null
                var metadata = f.get('typeIconMetadata')
                if (!metadata) {
                    metadata = {}
                    f.set('typeIconMetadata',metadata,true)
                }
                var perimeter = 0
                if (!metadata['segments']) {
                    var segmentsMetadata=[]
                    linestring.forEachSegment(function(start,end){
                        var angle = Math.atan2(end[1] - start[1],end[0] - start[0])
                        segmentMetadata = {
                            length:vm.measure.getLength([start,end]),
                            rotation: -1 * Math.atan2(end[1] - start[1],end[0] - start[0]) + Math.PI * 1/4
                        }
                        segmentsMetadata.push(segmentMetadata)
                        perimeter += segmentMetadata['length']
                    })
                    metadata['perimeter'] = perimeter
                    metadata['closed'] = (linestring.getFirstCoordinate()[0] === linestring.getLastCoordinate()[0]) && (linestring.getFirstCoordinate()[1] === linestring.getLastCoordinate()[1])
                    //get the position of each segment's end point in overall linestring
                    var len = 0
                    $.each(segmentsMetadata,function(index,segmentMetadata){
                        len += segmentMetadata['length']
                        segmentMetadata['position'] = len / perimeter
                    })
                    metadata['segments'] = segmentsMetadata
                }
                if (!metadata['points']) {
                    var pointsMetadata = {}
                    var iconSize = tool['typeIconDims']?tool['typeIconDims'][0]:48
                    pointsMetadata['scale'] = vm.map.getScale()
                    var perimeterInPixes = parseInt((metadata['perimeter'] / (pointsMetadata['scale'] * 1000)) * 1000 * vm.dpmm)
                    if (perimeterInPixes < iconSize) {
                        pointsMetadata['symbolSize'] = 1
                        pointsMetadata['symbolPercentage'] = 0.5
                    } else if (perimeterInPixes < iconSize * 2) {
                        pointsMetadata['symbolSize'] = 2
                        pointsMetadata['symbolPercentage'] = metadata['closed']?0.5:1
                    } else {
                        pointsMetadata['symbolSize'] = parseInt(perimeterInPixes / ( iconSize * 2)) //each symbol occupy 2 times symbol size
                        pointsMetadata['symbolPercentage'] = 1 / pointsMetadata['symbolSize']
                        if (!metadata['closed']) {
                            //geomoetry is not closed, drop a symbol at the end
                            pointsMetadata['symbolSize'] = pointsMetadata['symbolSize'] + 1
                        }

                    }
                    pointsMetadata['tint'] = f['typeIconTint'] || f.get('typeIconTint') || tool['typeIconTint'] || 'default'
                    metadata['points'] = pointsMetadata
                }
                var symbolSize = metadata['points']['symbolSize']
                var symbolPercentage = metadata['points']['symbolPercentage']
                
                if (symbolSize == 1) {
                    var segmentIndex = metadata['segments'].findIndex(function(segment){return segment.position >= symbolPercentage})

                    typeIconStyle.push(new ol.style.Style({
                        geometry:new ol.geom.Point(linestring.getCoordinateAt(symbolPercentage)),
                        image: new ol.style.Icon({
                          src: src,
                          rotation: metadata['segments'][segmentIndex]['rotation'],
                          rotateWithView: true,
                          snapToPixel: true
                        })
                    }))
                } else {
                    var segmentIndex = 0
                    var segmentMetadata = metadata['segments'][segmentIndex]
                    var symbolPoints = []
                    var symbolStyle = null
                    var fromStartLength = segmentMetadata.length
                    var fraction = null
                    for (var i = 0;i <= symbolSize ;i++) {
                        if (i == symbolSize || segmentMetadata['position'] < i * symbolPercentage) {
                            typeIconStyle.push(new ol.style.Style({
                                geometry:new ol.geom.MultiPoint(symbolPoints),
                                image: new ol.style.Icon({
                                  src: src,
                                  rotation: segmentMetadata['rotation'],
                                  rotateWithView: true,
                                  snapToPixel: true
                                })
                            }))
                            if (i == symbolSize) {
                                break;
                            }
                            segmentIndex += 1
                            segmentMetadata = metadata['segments'][segmentIndex]
                            fromStartLength += segmentMetadata.length
                            symbolPoints = []
                        }
                        fraction = Math.min( Math.max( i * symbolPercentage, 0 ), 1 )
                        symbolPoints.push(linestring.getCoordinateAt(fraction))
                    }
                }
                f['typeIconStyle'] = typeIconStyle
            }
            return baseStyle.concat(typeIconStyle)
        }
      },
      initFeature:function(feature) {
        var tool = feature.get('toolName')?this.getTool(feature.get('toolName')):false
        if (tool) {
            feature.setStyle(tool.style)
        }
      }
    },
    ready: function () {
      var vm = this
      vm._currentTool = {}
      vm.shape = vm.pointShapes[0]
      var annotationStatus = this.loading.register("annotation","Annotation Component", "Initialize")
      var map = this.map
      // collection to store all annotation features
      this.features.on('add', function (ev) {
        tool = vm.getTool(ev.element.get('toolName'))
        if (tool.onAdd) {
          tool.onAdd(ev.element)
        }
      })
      var savedFeatures = this.$root.geojson.readFeatures(this.$root.store.annotations)
      this.$on('gk-init', function () {
        if (savedFeatures) {
          //set feature style
          $.each(savedFeatures,function(index,feature){
            if (!feature.get('id')) {
                vm.drawingSequence += 1
                feature.set('id',vm.drawingSequence)
            }
            vm.initFeature(feature)
          })
          this.features.extend(savedFeatures)
        }
      })
      // add/remove selected property
      this.selectedFeatures.on('add', function (ev) {
        vm.tintSelectedFeature(ev.element)
      })
      this.selectedFeatures.on('remove', function (ev) {
        vm.tintUnselectedFeature(ev.element)
      })
      // layer/source for modifying annotation features
      this.featureOverlay = new ol.layer.Vector({
        source: new ol.source.Vector({
          features: this.features
        })
      })
      this.featureOverlay.set('id', 'annotations')
      this.featureOverlay.set('name', 'My Drawing')
      // collection for tracking selected features

      // the following interacts are bundled into the Select and Edit tools.
      // main difference is that Select allows movement of whole features around the map,
      // whereas Edit is for movement of individual nodes

      this.ui.translateInter = this.translateInterFactory()()
      this.ui.dragSelectInter = this.dragSelectInterFactory()()
      this.ui.selectInter = this.selectInterFactory()()
      this.ui.keyboardInter = this.keyboardInterFactory()()
      this.ui.modifyInter = this.modifyInterFactory()()

      // load default tools
      this.ui.defaultPan = {
        name: 'Pan',
        icon: 'fa-hand-paper-o',
        cursor:['-webkit-grab','-moz-grab'],
        scope:["annotation","bfrs","resourcetracking"],
        interactions: [
          map.dragPanInter,
          map.doubleClickZoomInter,
          map.keyboardPanInter,
          map.keyboardZoomInter
        ]
      }
      this.ui.editStyle = {
        name: 'Edit Style',
        icon: 'fa-pencil-square-o',
        scope:["annotation"],
        interactions: [
          this.ui.dragSelectInter,
          this.ui.selectInter,
        ],
        onSet: function() {
            vm.ui.dragSelectInter.setMulti(false)
            vm.ui.selectInter.setMulti(false)
        }
      }
      this.ui.defaultSelect = {
        name: 'Select',
        icon: 'fa-mouse-pointer',
        scope:["annotation","resourcetracking"],
        interactions: [
          this.ui.keyboardInter,
          this.ui.dragSelectInter,
          this.ui.selectInter,
          this.ui.translateInter
        ],
        onSet: function() {
            vm.ui.dragSelectInter.setMulti(true)
            vm.ui.selectInter.setMulti(true)
        }
      }
      this.ui.defaultEdit = {
        name: 'Edit Geometry',
        icon: 'fa-pencil',
        scope:["annotation"],
        interactions: [
          this.ui.keyboardInter,
          this.ui.selectInter,
          this.ui.dragSelectInter,
          this.ui.modifyInter
        ],
        onSet: function() {
            vm.ui.dragSelectInter.setMulti(false)
            vm.ui.selectInter.setMulti(false)
        }
      }
      this.tools = [
        this.ui.defaultPan,
        this.ui.defaultSelect,
        this.ui.defaultEdit,
        this.ui.editStyle
      ]

      var noteStyleCache = {}
      var noteStyle = function (res) {
        var f = this
        var url = ''
        if (f) {
          url = vm.getNoteUrl(f.get('note'))
        } else {
          return null
        }
        var tint = f['tint'] || f.get('tint') || "notselected"
        if (!noteStyleCache[url]) {
            noteStyleCache[url] = []
        }
        if (!noteStyleCache[url][tint]) {
          var color = (tint == "selected")?'#70BDF0':undefined
          noteStyleCache[url][tint] = new ol.style.Style({
            image: new ol.style.Icon({
              anchorOrigin: 'bottom-left',
              anchor: [0, 0],
              color: color,
              src: url
            })
          })
        }
        return noteStyleCache[url][tint]
      }
      this.ui.defaultText = {
        name: 'Text Note',
        icon: 'fa-comment',
        style: noteStyle,
        interactions: [vm.pointDrawFactory()],
        showName: true,
        scope:["annotation"],
        onAdd: function (f) {
          f.getGeometry().defaultGetExtent = f.getGeometry().defaultGetExtent || f.getGeometry().getExtent
          f.getGeometry().getExtent = function() {
              if (vm.selecting) {
                  return vm.getNoteExtent(f)
              } else {
                  return this.defaultGetExtent()
              }
          }
          if (f.get('note')) { return }
          f.set('note', $.extend({}, vm.note))
        },
      }

      var customAdd = function (f) {
        if (!f.get('size')) { 
          f.set('size', vm.size)
        }
        if (!f.get('colour')) { 
          f.set('colour', vm.colour)
        }
      }

      var customPointAdd = function (f) {
        if (!f.get('shape')) {
            f.set('shape',vm.shape)
        }
        if (!f.get('colour')) {
            f.set('colour',vm.colour)
        }
        
      }

      this.ui.defaultPoint = {
        name: 'Custom Point',
        icon: function(feature){
            if (feature) {
                return feature.get('shape')[0]
            } else {
                return 'dist/static/symbols/fire/custom_point.svg'
            }
        },
        interactions: [this.pointDrawFactory()],
        showName: true,
        scope:["annotation"],
        onAdd: customPointAdd,
        style: vm.getIconStyleFunction(vm.tints),
        sketchStyle: function (res) {
            var feat = this
            feat.set('shape',vm.shape,true)
            feat.set('colour',vm.colour,true)
            var style = vm.map.cacheStyle(function (feat) {
              var src = vm.map.getBlob(feat, ['icon', 'tint'],vm.tints || {})
              if (!src) { return false }
              var rot = feat.get('rotation') || 0.0
              return new ol.style.Style({
                image: new ol.style.Icon({
                  src: src,
                  scale: 0.5,
                  rotation: rot,
                  rotateWithView: true,
                  snapToPixel: true
                })
              })
            }, feat, ['icon', 'tint', 'rotation'])
            return style
          },
          tint: function(feature) {
            var shape = feature.get('shape')
            var colour = feature.get('colour')
            if (shape) {
                return vm.getCustomPointTint(shape,[null,colour])
            } else {
                return "default"
            }
          },
          selectedTint: function(feature) {
            var shape = feature.get('shape')
            if (shape) {
                return vm.getCustomPointTint(shape,['#2199e8','#2199e8'])
            } else {
                return "selected"
            }
          }
      }

      this.ui.defaultLine = {
        name: 'Custom Line',
        icon: 'dist/static/images/iD-sprite.svg#icon-line',
        interactions: [this.linestringDrawFactory()],
        showName: true,
        scope:["annotation"],
        onAdd: customAdd,
        style: vm.getVectorStyleFunc(this.tints),
        comments:[
          {name:"Tips",description:["Hold down the 'SHIFT' key during drawing to enable freehand mode. "]}
        ]
      }

      this.ui.defaultPolygon = {
        name: 'Custom Area',
        icon: 'dist/static/images/iD-sprite.svg#icon-area',
        interactions: [this.polygonDrawFactory()],
        showName: true,
        scope:["annotation"],
        onAdd: customAdd,
        style: vm.getVectorStyleFunc(this.tints),
        measureLength:true,
        measureArea:true,
        comments:[
          {name:"Tips",description:["Hold down the 'SHIFT' key during drawing to enable freehand mode. "]}
        ]
      }

      var getFeatureInfo = function(feature) {
        var tool = vm.getTool(feature.get('toolName'))
        var icon = tool.icon
        if (typeof icon === "function") {
            icon = icon(feature)
        }

        if (!icon) {
          return {name:tool.name}
        } else if (icon.startsWith('fa-')) {
          return {name:tool.name, icon:"fa " + icon}
        } else if (icon.search('#') === -1) {
          // plain svg/image
          return {name:tool.name, img:icon}
        } else {
          // svg reference
          return {name:tool.name, svg:icon}
        }
      }

      // add annotations layer to catalogue list
      this.$root.catalogue.catalogue.push({
        type: 'Annotations',
        id: 'annotations',
        name: 'My Drawing',
        getFeatureInfo:getFeatureInfo
      })

      this.measure.register("annotations",this.features)

      annotationStatus.wait(30,"Listen 'gk-init' event")
      this.$on("gk-init",function() {
        annotationStatus.progress(80,"Process 'gk-init' event")
        //initialize tool's interaction
        $.each(vm.tools,function(index, tool){
            $.each(tool.interactions,function(subindex,interact){
                if (typeof interact === 'function') {
                    tool.interactions[subindex] = interact(tool)
                }
            })
            tool.keepSelection = (tool.keepSelection === undefined)?false:tool.keepSelection
            tool.selectMode = (tool.selectMode == undefined)?"feature":tool.selectMode
            if (!tool.label) {
                tool.label = tool.name
            }
        })
        vm.annotationTools = this.tools.filter(function (t) {
          return t.scope && t.scope.indexOf("annotation") >= 0
        })
        vm.setDefaultTool('annotations','Edit')
        annotationStatus.end()
      })
    }

  }
</script>
