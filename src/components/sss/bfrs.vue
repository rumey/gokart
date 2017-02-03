<template>
  <div class="tabs-panel" id="menu-tab-bfrs">
    <div class="row collapse">
      <div class="columns">
        <ul class="tabs" id="bfrs-tabs">
          <li class="tabs-title is-active"><a class="label" aria-selected="true">Bush Fire Report</a></li>
        </ul>
      </div>
    </div>
    <div class="row collapse" id="bfrs-tab-panels">
      <div class="columns">
        <div class="tabs-content vertical" data-tabs-content="bfrs-tabs">
          <div id="bfrs-list-tab" class="tabs-panel is-active" v-cloak>
            <div id="bfrs-list-controller-container">
            <div class="tool-slice row collapse">
              <div class="small-12">
                <div class="expanded button-group">
                  <a v-for="t in tools | filterIf 'showName' undefined" class="button button-tool" v-bind:class="{'selected': t.name == annotations.tool.name}"
                    @click="annotations.setTool(t)" v-bind:title="t.label">{{{ annotations.icon(t) }}}</a>
                </div>
                <div class="row resetmargin">
                  <div v-for="t in tools | filterIf 'showName' true" class="small-6" v-bind:class="{'rightmargin': $index % 2 === 0}" >
                    <a class="expanded secondary button" v-bind:class="{'selected': t.name == annotations.tool.name}" @click="annotations.setTool(t)"
                      v-bind:title="t.label">{{{ annotations.icon(t) }}} {{ t.label }}</a>
                  </div>
                </div>
              </div>
            </div>
            <div class="row">
              <div class="switch tiny">
                <input class="switch-input" id="reportsInViewport" type="checkbox" v-bind:checked="viewportOnly" @change="toggleViewportOnly" />
                <label class="switch-paddle" for="reportsInViewport">
                  <span class="show-for-sr">Viewport reports only</span>
                </label>
              </div>
              <label for="reportsInViewport" class="side-label">Restrict to viewport ({{ stats }})</label>
            </div>
            <div class="row">
              <div class="switch tiny">
                <input class="switch-input" id="toggleBushfireLabels" type="checkbox" v-bind:checked="bushfireLabels" @change="toggleBushfireLabels" />
                <label class="switch-paddle" for="toggleBushfireLabels">
                  <span class="show-for-sr">Display report labels</span>
                </label>
              </div>
              <label for="toggleBushfireLabels" class="side-label">Display bushfire labels</label>
            </div>
            <div class="row">
              <div class="switch tiny">
                <input class="switch-input" id="toggleReportInfo" type="checkbox" v-bind:disabled="!setting.hoverInfoSwitchable" v-bind:checked="setting.hoverInfo" @change="setting.toggleHoverInfo" />
                <label class="switch-paddle" for="toggleReportInfo">
                  <span class="show-for-sr">Display hovering report info</span>
                </label>
              </div>
              <label for="toggleReportInfo" class="side-label">Display hovering bushfire info</label>
            </div>
            <div class="row collapse">
              <div class="small-6 columns">
                <select name="select" v-model="cql" @change="updateCQLFilter">
                  <option value="" selected>All reports</option> 
                </select>
              </div>
              <div class="small-6 columns">
                <input type="search" v-model="search" placeholder="Find a report" @keyup="updateFeatureFilter">
              </div>
            </div>
            <div class="row">
              <div class="small-7">
                <div class="columns">
                  <div class="row">
                    <div class="switch tiny">
                      <input class="switch-input" id="selectedBushfiresOnly" type="checkbox" v-model="selectedOnly" @change="updateCQLFilter('selectedBushfire')" />
                      <label class="switch-paddle" for="selectedBushfiresOnly">
                        <span class="show-for-sr">Show selected only</span>
                     </label>
                    </div>
                    <label for="selectedBushfiresOnly" class="side-label">Show selected only</label>
                  </div>
                </div>
              </div>
              <div class="small-5">
                <a title="Zoom to selected" class="button" @click="zoomToSelected()" ><i class="fa fa-search"></i></a>
                <a title="Download list as geoJSON" class="button" @click="downloadList()" ><i class="fa fa-download"></i></a>
                <!--a title="Download all or selected as CSV" class="button" href="{{bfrsService}}/report.csv?{{downloadSelectedCSV()}}" target="_blank" ><i class="fa fa-table"></i></a-->
              </div>
            </div>
            </div>


            <div id="bfrs-list" class="layers-flexibleframe scroller" style="margin-left:-15px; margin-right:-15px;">
              <div v-for="f in features" class="row feature-row" v-bind:class="{'feature-selected': selected(f) }"
                @click="toggleSelect(f)" track-by="get('id')">
                <div class="columns">
                  <a v-if="isModified(f)" @click.stop.prevent="resetFeature(f)" title="Reset" class="button tiny secondary float-right"><i class="fa fa-undo"></i></a>
                  <div class="feature-title"><img class="feature-icon" id="report-icon-{{f.get('id')}}" v-bind:src="featureIconSrc(f)" /> {{ f.get('label') }} <i><small></small></i></div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
  import { ol, moment,utils } from 'src/vendor.js'
  export default {
    store: {
        bfrsService:'bfrsService',
        bushfireLabels:'settings.bfrs.bushfireLabels',
        viewportOnly:'settings.bfrs.viewportOnly',
        screenHeight:'layout.screenHeight',
        leftPanelHeadHeight:'layout.leftPanelHeadHeight',
        activeMenu:'activeMenu',
        whoami:'whoami'
    },
    data: function () {
      var fill = '#ff6600'
      var stroke = '#7c3100'
      return {
        selectedOnly: false,
        search: '',
        cql: '',
        tools: [],
        fields: ['id', 'name'],
        fireboundary:new ol.Collection(),
        allFeatures: new ol.Collection(),
        extentFeatures: [],
        selectedBushfires: [],
        revision:1,
        tints: {
          'initial': [['#b43232','#b08c9d']],
          'initial.text': '#b08c9d',
          'initial.colour': '#b08c9d',
          'final': [['#b43232', '#b7d28d']],
          'final.text': '#b7d28d',
          'final.colour': '#b7d28d',
          'final_authroized': [['#b43232', '#7ecca3']],
          'final_authroized.text': '#7ecca3',
          'final_authroized.colour': '#7ecca3',
          'modified':[["#b43232","#f57900"]],
          'modified.text':"#f57900",
          'modified.colour':"#f57900",
          'selected': [['#b43232', '#2199e8']],
          'selected.text': '#2199e8',
        }
      }
    },
    computed: {
      map: function () { return this.$root.$refs.app.$refs.map },
      annotations: function () { return this.$root.$refs.app.$refs.annotations },
      info: function () { return this.$root.info },
      setting: function () { return this.$root.setting },
      catalogue: function () { return this.$root.catalogue },
      export: function () { return this.$root.export },
      loading: function () { return this.$root.loading },
      features: function () {
        if (this.viewportOnly) {
          return this.revision && this.extentFeatures
        } else {
          return this.revision && this.allFeatures.getArray()
        }
      },
      isReportMapLayerHidden:function() {
        return this.$root.active.isHidden(this.bfrsMapLayer)
      },
      selectedFeatures: function () {
        return this.features.filter(this.selected)
      },
      stats: function () {
        return this.extentFeatures.length + '/' + this.allFeatures.getLength()
      },
      bfrsLayer: function() {
        return this.$root.catalogue.getLayer('bfrs:bushfire_dev')
      },
      bfrsMapLayer: function() {
        return this.$root.map?this.$root.map.getMapLayer(this.bfrsLayer):undefined
      },
      bushfireStyleFunc:function() {
        if (!this._bushfireStyleFunc) {
            this._bushfireStyleFunc = function () {
                var vm = this
                var pointStyleFunc = vm.annotations.getIconStyleFunction(vm.tints)
                var boundaryStyleFunc = vm.annotations.getVectorStyleFunc(vm.tints)
                var labelStyleFunc = vm.annotations.getLabelStyleFunc(vm.tints)
                return function(res) {
                    var feat = this
                    var pointStyle = pointStyleFunc.call(feat,res)
                    var boundaryStyle = (feat.getGeometry() && (feat.getGeometry() instanceof ol.geom.GeometryCollection ) && feat.getGeometry().getGeometries().length > 1)?boundaryStyleFunc.call(feat,res):null
                    var labelStyle = null
                    if (res < 0.003 && feat.get('label') && vm.bushfireLabels && !vm.$root.active.isHidden(vm.map.getMapLayer("bfrs:bushfire_dev"))) {
                      labelStyle = labelStyleFunc.call(feat,res)
                      labelStyle.setGeometry(feat.getGeometry().getGeometries()[0])
                    }   

                    var style = null
                    if (boundaryStyle || labelStyle) {
                        if (boundaryStyle && labelStyle) {
                            style = [pointStyle,boundaryStyle,labelStyle]
                        } else {
                            style = [pointStyle,boundaryStyle || labelStyle]
                        }
                        for(var i = (labelStyle?(style.length - 2):(style.length - 1));i >= 0;i--) {
                            if (Array.isArray(style[i])) {
                                $.each(style.splice(i,1)[0],function(p,s){style.push(s)})
                            }
                        }
                    } else {
                        style = pointStyle
                    }
                    return style
                }
            }.call(this)
        }
        return this._bushfireStyleFunc
      }
    },
    watch:{
      isReportMapLayerHidden:function(newValue,oldValue) {
        if (newValue === undefined || oldValue === undefined) {
            //layer is turned on or turned off
            return
        } else if (this.map.resolution >= 0.003) {
            //label is turned on, but resolution is not less than 0.003
            return
        } else {
            //label is enabled, hiding/showing bfrs layer requires resetting the style text.
            this.bfrsMapLayer.changed() 
        }
      },
      bushfireLabels:function(newValue,oldValue) {
        this.showBushfireLabels()
      },
      "screenHeight":function(newValue,oldvalue) {
        this.adjustHeight()
      },
      "toggleHistory":function() {
        this.adjustHeight()
      }
    },
    methods: {
      adjustHeight:function() {
        if (this.activeMenu === "bfrs") {
            $("#bfrs-list").height(this.screenHeight - this.leftPanelHeadHeight - $("#bfrs-list-controller-container").height())
        }
      },
      toggleSelect: function (f) {
        if (this.selected(f)) {
          this.$root.annotations.selectedFeatures.remove(f)
        } else {
          if (this.annotations.tool.name === "Bfrs Edit Geometry") {
              //Only one bush fire can be choosed in edit mode
              this.$root.annotations.selectedFeatures.clear()
          }
          this.$root.annotations.selectedFeatures.push(f)
        }
      },
      toggleViewportOnly: function () {
        this.viewportOnly = !this.viewportOnly
        this.export.saveState()
      },
      toggleBushfireLabels: function () {
        var vm = this
        this.bushfireLabels = !this.bushfireLabels
        this.export.saveState()
      },
      isModified:function(feat){
        return feat.get('status') === 'modified'
      },
      resetFeature:function(feat) {
        var vm = this
        var filter = 'id=' + feat.get('id')
        this.bfrsMapLayer.getSource().retrieveFeatures(filter,function(features){
          if (features && features.length) {
            vm.initBushfire(features[0])
            vm.bfrsMapLayer.getSource().removeFeature(feat)
            vm.bfrsMapLayer.getSource().addFeature(features[0])

            var index = vm.allFeatures.getArray().findIndex(function(f){return f.get('id') === feat.get('id')})
            if (index >= 0) {
                vm.allFeatures.setAt(index,features[0])
                vm.revision += 1
            }

            if (vm.extentFeatures) {
                index = vm.extentFeatures.findIndex(function(f){return f.get('id') === feat.get('id')})
                if (index >= 0) {
                    vm.extentFeatures[index] = features[0]
                }
            }

            index = vm.annotations.selectedFeatures.getArray().findIndex(function(f){return f.get('id') === feat.get('id')})
            if (index >= 0) {
                vm.annotations.selectedFeatures.setAt(index,features[0])
            }
              
          }
        })
        
      },
      initBushfire:function(feature) {
        var geometries = feature.getGeometry()?[feature.getGeometry()]:[]
        if (feature.get("fire_boundary") && feature.get("fire_boundary").coordinates) {
            $.each(feature.get("fire_boundary").coordinates,function(index,polygonCoordinates){
                geometries.push(new ol.geom.Polygon(polygonCoordinates))
            })
        }
        feature.setGeometry(new ol.geom.GeometryCollection(geometries),true)
        var now = moment()
        var timestamp = moment(feature.get('created'))
        if (!feature.get('init_authorised_by_id')) {
            feature.set('status','initial',true)
        } else if(feature.get('authorised_by_id')) {
            feature.set('status','final_authorized',true)
        } else {
            feature.set('status','final',true)
        }
        feature.set('label',feature.get('name'),true)

        feature.set('toolName','Bfrs Origin Point',true)
        feature.set('tint',feature.get('status'),true)
        feature.set('originalTint', feature.get('tint'),true)
        feature.set('fillColour',this.tints[feature.get('tint') + ".fillColour"])
        feature.set('colour',this.tints[feature.get('tint') + ".colour"])
        feature.setStyle(this.bushfireStyleFunc)
      },
      showBushfireLabels:function() {
        if (this.bfrsMapLayer && !this.$root.active.isHidden(this.bfrsMapLayer)) {
            this.bfrsMapLayer.changed()
        }
      },
      featureIconSrc:function(f) {
        var vm = this
        //trigger dynamic binding
        var tmp = vm.selectedBushfires
        return this.map.getBlob(f, ['icon', 'originalTint'],this.tints,function(){
            $("#report-icon-" + f.get('id')).attr("src", vm.featureIconSrc(f))
        })
      },
      selected: function (f) {
        return f.get('id') && (this.selectedBushfires.indexOf(f.get('id')) > -1)
      },
      downloadList: function () {
        this.$root.export.exportVector(this.features.filter(this.featureFilter).sort(this.featureOrder), 'bfrsdata')
      },
      downloadSelectedCSV: function () {
          var bushfireFilter = ''
          if (this.selectedBushfires.length > 0) {
              bushfireFilter = 'id__in=' + this.selectedBushfires.join(',')
          }
          return bushfireFilter
      },
      updateCQLFilter: function (updateType) {
        var vm = this
        if (!vm._updateCQLFilter) {
            vm._updateCQLFilter = debounce(function(updateType){
                var groupFilter = vm.cql
                var bushfireFilter = ''
                // filter by specific reports if "Show selected only" is enabled
                if ((vm.selectedBushfires.length > 0) && (vm.selectedOnly)) {
                  bushfireFilter = 'id in (' + vm.selectedBushfires.join(',') + ')'
                }
                // CQL statement assembling logic
                if (groupFilter && bushfireFilter) {
                  vm.bfrsLayer.cql_filter = '(' + groupFilter + ') and (' + bushfireFilter + ')'
                } else if (bushfireFilter) {
                  vm.bfrsLayer.cql_filter = bushfireFilter
                } else {
                  vm.bfrsLayer.cql_filter = groupFilter
                }
                if (!bushfireFilter && vm.selectedOnly) {
                    vm.selectedOnly = false
                }
                if (updateType === "selectedBushfire" && bushfireFilter) {
                    //chosed some reports
                    var filteredFeatures = vm.bfrsMapLayer.getSource().getFeatures().filter(function(f){
                        return vm.selectedBushfires.indexOf(f.get('id')) >= 0
                    })
                    vm.bfrsMapLayer.getSource().clear()
                    vm.bfrsMapLayer.getSource().addFeatures(filteredFeatures)
                    $.each(filteredFeatures,function(index,feature){
                        vm.annotations.tintSelectedFeature(feature)
                    })
                    vm.updateFeatureFilter(true)
                } else {
                    //clear report filter or change other filter
                    vm.bfrsMapLayer.set('updated', moment().toLocaleString())
                    vm.bfrsMapLayer.getSource().loadSource("query")
                }
            },500)
        }
        vm._updateCQLFilter(updateType)
      },
      featureFilter: function (f) {
        var search = ('' + this.search).toLowerCase()
        var found = !search || this.fields.some(function (key) {
          return ('' + f.get(key)).toLowerCase().indexOf(search) > -1
        })
        if (this.selectedOnly && this.selectedFeatures.length) {
          return this.selected(f) && found
        };
        return found
      },
      featureOrder: function (a, b) {
        return 0
      },
      zoomToSelected: function () {
        var extent = ol.extent.createEmpty()
        this.selectedFeatures.forEach(function (f) {
          ol.extent.extend(extent, f.getGeometry().getExtent())
        })
        var map = this.$root.map.olmap
        map.getView().fit(extent, map.getSize())
      },
      updateFeatureFilter: function(runNow) {
        var vm = this
        var updateFeatureFilterFunc = function() {
            // syncing of Resource Tracking features between Vue state and OL source
            var mapLayer = vm.bfrsMapLayer
            if (!mapLayer) { return }
            // update vue list for filtered features in the current extent
            vm.extentFeatures = mapLayer.getSource().getFeaturesInExtent(vm.$root.map.extent).filter(vm.featureFilter)
            vm.extentFeatures.sort(vm.featureOrder)
            // update vue list for filtered features
            var allFeatures = mapLayer.getSource().getFeatures().filter(vm.featureFilter)
            allFeatures.sort(vm.featureOrder)
            vm.allFeatures.clear()
            vm.allFeatures.extend(allFeatures)
        }
        if (runNow) {
            updateFeatureFilterFunc()
        } else {
            if (!vm._updateFeatureFilter) {
                vm._updateFeatureFilter = debounce(function(){
                    updateFeatureFilterFunc()
                },700)
            }
            vm._updateFeatureFilter()
        }
      },
      updateViewport: function(runNow) {
        var vm = this
        var updateViewportFunc = function() {
            // syncing of Resource Tracking features between Vue state and OL source
            var mapLayer = vm.bfrsMapLayer
            if (!mapLayer) { return }
            var feats = mapLayer.getSource().getFeatures()
            // update vue list for filtered features in the current extent
            vm.extentFeatures = mapLayer.getSource().getFeaturesInExtent(vm.$root.map.extent).filter(vm.featureFilter)
            vm.extentFeatures.sort(vm.featureOrder)
        }
        if (runNow) {
            updateViewportFunc()
        } else {
            if (!vm._updateViewport) {
                vm._updateViewport = debounce(function(){
                    updateViewportFunc()
                },100)
            }
            vm._updateViewport()
        }
      },
      setup: function() {
        // enable resource bfrs layer, if disabled
        var catalogue = this.$root.catalogue
        if (!this.bfrsMapLayer) {
          catalogue.onLayerChange(this.bfrsLayer, true)
        }

        this.$root.annotations.selectable = [this.bfrsMapLayer]
        this.annotations.setTool()

        this.$nextTick(this.adjustHeight)
      },
      tearDown:function() {
        this.selectable = null
      }
    },
    ready: function () {
      var vm = this
      var bfrsStatus = this.loading.register("bfrs","Bush Fire Report Component","Initialize")
      var map = this.$root.map
      vm.whoami['bushfire'] = {}

      this.$root.fixedLayers.push({
        type: 'WFSLayer',
        name: 'Bush Fire Report',
        id: 'bfrs:bushfire_dev',
        getFeatureInfo:function (f) {
            return {name:f.get("name"), img:map.getBlob(f, ['icon', 'tint']), comments:"TBD"}
        },
        //refresh: 60,
        onload: function(loadType,vectorSource,features,defaultOnload) {
            //combine the two spatial columns into one
            $.each(features,function(index,feature){
                vm.initBushfire(feature)
            })
            function processResources() {
                defaultOnload(loadType,vectorSource,features)
                if (vm.selectedBushfires.length > 0) {
                    var reportIds = vm.selectedBushfires.slice()
                    vm.$root.annotations.selectedFeatures.clear()
                    features.filter(function(el, index, arr) {
                      var id = el.get('id')
                      if (!id) return false
                      if (reportIds.indexOf(id) < 0) return false
                      return true
                    }).forEach(function (el) {
                      vm.$root.annotations.selectedFeatures.push(el)
                    })
                }
                vm.updateFeatureFilter(true)
            }
            var permissionConfig = [
                ["create",null,null],
                ["initial.edit",null,function(f){return f.get('status') === "initial"}],
                ["initial.authorize",null,function(f) {return f.get('status') === "initial"}],
                ["final.edit",null,function(f) {return f.get('status') === "final"}],
                ["final.authroize",null,function(f) {return f.get('status') === "final"}],
                ["final_authroized.edit",null,function(f) {return f.get('status') === "final_authorized"}],
            ]
            var checkPermission = function(index){
                var p = permissionConfig[index]
                var url = null
                if (vm.whoami[p[0]] === null || vm.whoami[p[0]] === undefined){
                    if (p[1] === null) {
                        //always have the permission
                        vm.whoami['bushfire'][p[0]] = true
                    } else {
                        if (typeof p[1] === "string") {
                            //url is a constant string
                            url = p[1]
                        } else {
                            //url is a function with a report argument.
                            var f = features.find(p[2])
                            if (f) {
                                //get the test url
                                url = p[1](f)
                            } else {
                                //can't find a report to test
                                url = null
                                vm.whoami['bushfire'][p[0]] = null
                            }
                        }
                    }
                }
                if (url) {
                    utils.checkPermission(url,function(allowed){
                        vm.whoami['bushfire'][p[0]] = allowed
                        if (index < permissionConfig.length - 1) {
                            checkPermission(index + 1)
                        } else {
                            processResources()
                        }
                    })
                } else {
                    if (index < permissionConfig.length - 1) {
                        checkPermission(index + 1)
                    } else {
                        processResources()
                    }
                }
            }
            checkPermission(0)
        }
      })

      vm.ui = {}
      var toolConfig = {features:vm.allFeatures,mapLayers:function(layer){return layer.get("id") === "bfrs:bushfire_dev" }}
      vm.ui.translateInter = vm.annotations.translateInterFactory()(toolConfig)
      vm.ui.translateInter.on("translateend",function(ev){
          ev.features.forEach(function(f){
            f.set('status',"modified",true)
            vm.revision += 1
            f.set('tint',"modified",true)
            f.set('fillColour',vm.tints[f.get('tint') + ".fillColour"])
            f.set('colour',vm.tints[f.get('tint') + ".colour"])
          })
      })
      vm.ui.dragSelectInter = vm.annotations.dragSelectInterFactory()(toolConfig)
      vm.ui.selectInter = vm.annotations.selectInterFactory()(toolConfig)
      vm.ui.modifyInter = vm.annotations.modifyInterFactory()(toolConfig)
      vm.ui.modifyInter.on("featuresmodified",function(ev){
          ev.features.forEach(function(f){
            if (f.get('status') !== "modified") {
                f.set('status','modified',true)
                f.set('tint',"modified",true)
                f.set('fillColour',vm.tints[f.get('tint') + ".fillColour"])
                f.set('colour',vm.tints[f.get('tint') + ".colour"])
            }
          })
          vm.revision += 1
      })

      vm.ui.polygonDraw = vm.annotations.polygonDrawFactory()({features:vm.fireboundary})
      vm.fireboundary.on("add",function(ev){
        if (vm.annotations.selectedFeatures.getLength() === 1){
            var f = vm.annotations.selectedFeatures.item(0)
            f.getGeometry().getGeometriesArray().push(ev.element.getGeometry())
            f.getGeometry().changed()
            if (f.get('status') !== "modified") {
                f.set('status','modified',true)
                f.set('tint',"modified",true)
                f.set('fillColour',vm.tints[f.get('tint') + ".fillColour"])
                f.set('colour',vm.tints[f.get('tint') + ".colour"])
                vm.revision += 1
            }
        }
      })

      //add tools
      var tools = [
          {
              name: 'Bfrs Origin Point',
              label: 'Origin Point',
              icon: 'dist/static/symbols/fire/origin.svg',
              tints: vm.tints,
              selectedFillColour:[0, 0, 0, 0.25],
              fillColour:[0, 0, 0, 0.25],
              size:2,
              interactions: [vm.annotations.pointDrawFactory()],
              sketchStyle: vm.annotations.getIconStyleFunction(vm.tints),
              features:vm.allFeatures,
              scope:["bfrs"],
              measureLength:true,
              measureArea:true,
              showName: true,
          },{
              name: 'Bfrs Select',
              label: 'Select',
              icon: 'fa-mouse-pointer',
              scope:["bfrs"],
              interactions: [
                  vm.ui.dragSelectInter,
                  vm.ui.selectInter,
                  vm.ui.translateInter
              ],
              onSet: function() {
                  vm.ui.dragSelectInter.setMulti(true)
                  vm.ui.selectInter.setMulti(true)
              }
          },{
              name: 'Bfrs Edit Geometry',
              label: 'Edit Geometry',
              icon: 'fa-pencil',
              scope:["bfrs"],
              interactions: [
                  this.ui.selectInter,
                  this.ui.dragSelectInter,
                  this.ui.modifyInter
              ],
              onSet: function() {
                  vm.ui.dragSelectInter.setMulti(false)
                  vm.ui.selectInter.setMulti(false)
              }
          }, {
              name: 'Bfrs Fire Boundary',
              label: 'Fire Boundary',
              icon: 'dist/static/images/iD-sprite.svg#icon-area',
              style: vm.annotations.getVectorStyleFunc(vm.tints),
              selectedFillColour:[0, 0, 0, 0.25],
              fillColour:[0, 0, 0, 0.25],
              size:2,
              interactions: [vm.ui.polygonDraw],
              scope:["bfrs"],
              showName: true,
          }
      ]

      tools.forEach(function (tool) {
        vm.annotations.tools.push(tool)
      })


      bfrsStatus.wait(40,"Listen 'gk-init' event")
      // post init event hookup
      this.$on('gk-init', function () {
        bfrsStatus.progress(80,"Process 'gk-init' event")
        map.olmap.getView().on('propertychange', vm.updateViewport)
        this.$root.annotations.selectedFeatures.on('add', function (event) {
          if (event.element.get('id')) {
            vm.selectedBushfires.push(event.element.get('id'))
            if (vm.selectedOnly) {
                vm.updateCQLFilter('selectedBushfire')
            }
          }
        })
        this.$root.annotations.selectedFeatures.on('remove', function (event) {
          if (event.element.get('id')) {
            vm.selectedBushfires.$remove(event.element.get('id'))
            if (vm.selectedOnly) {
                vm.updateCQLFilter('selectedBushfire')
            }
          }
        })
        //vm.annotations.setDefaultTool('bfrs','Pan')
        vm.tools = vm.annotations.tools.filter(function (t) {
          return t.scope && t.scope.indexOf("bfrs") >= 0
        })
        bfrsStatus.end()
      })
    }
  }
</script>
