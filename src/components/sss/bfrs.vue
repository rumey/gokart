<template>
  <div class="tabs-panel" id="menu-tab-bfrs">
    <div class="row collapse">
      <div class="columns">
        <ul class="tabs" id="bfrs-tabs">
          <li class="tabs-title is-active">
            <a class="label" aria-selected="true">Bush Fire Report
              <small v-if="active.layerRefreshStatus(bushfireMapLayer)" style="white-space:pre-wrap"><br>Updated: {{ active.layerRefreshStatus(bushfireMapLayer) }}</small>
            </a>
          </li>
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
                        <a class="expanded button" v-bind:class="{'selected': t.name == annotations.tool.name}" @click="annotations.setTool(t)"
                          v-bind:title="t.label">{{{ annotations.icon(t) }}} {{ t.label }}</a>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="row">
                  <div class="switch tiny">
                    <input class="switch-input" id="bushfiresInViewport" type="checkbox" v-bind:checked="viewportOnly" @change="toggleViewportOnly" />
                    <label class="switch-paddle" for="bushfiresInViewport">
                      <span class="show-for-sr">Viewport bushfires only</span>
                    </label>
                  </div>
                  <label for="bushfiresInViewport" class="side-label">Restrict to viewport ({{ stats }})</label>
                </div>
                <div class="row">
                  <div class="switch tiny">
                    <input class="switch-input" id="toggleBushfireLabels" type="checkbox" v-bind:checked="bushfireLabels" @change="toggleBushfireLabels" v-bind:disabled="bushfireLabelsDisabled" />
                    <label class="switch-paddle" for="toggleBushfireLabels">
                      <span class="show-for-sr">Display bushfire labels</span>
                    </label>
                  </div>
                  <label for="toggleBushfireLabels" class="side-label">Display bushfire labels</label>
                </div>
                <div class="row">
                  <div class="switch tiny">
                    <input class="switch-input" id="toggleReportInfo" type="checkbox" v-bind:disabled="!setting.hoverInfoSwitchable" v-bind:checked="setting.hoverInfo" @change="setting.toggleHoverInfo" />
                    <label class="switch-paddle" for="toggleReportInfo">
                      <span class="show-for-sr">Display hovering bushfire info</span>
                    </label>
                  </div>
                  <label for="toggleReportInfo" class="side-label">Display hovering bushfire info</label>
                </div>
                <div class="row">
                  <div class="small-12">
                    <div class="columns">
                      <div class="row">
                        <div class="switch tiny">
                          <input class="switch-input" id="selectedBushfiresOnly" type="checkbox" v-bind:disabled="selectedOnlyDisabled" v-model="selectedOnly" @change="updateCQLFilter('selectedBushfire',500)" />
                          <label class="switch-paddle" for="selectedBushfiresOnly">
                            <span class="show-for-sr">Show selected only</span>
                         </label>
                        </div>
                        <label for="selectedBushfiresOnly" style="margin-left:3px" class="side-label">Show selected only</label>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="row collapse">
                  <div class="small-6 columns">
                    <select name="select" v-model="region" @change="updateCQLFilter('region',2000)">
                      <option value="" selected>All regions</option> 
                      <option v-for="r in regions"  value="{{r.region_id}}" track-by="region_id">
                        {{r.region}}
                      </option>
                    </select>
                  </div>
                  <div class="small-6 columns">
                    <select name="select" v-model="district" @change="updateCQLFilter('district',500)">
                      <option value="" selected>All districts</option> 
                      <option v-for="d in districts"  value="{{d.id}}" track-by="id">
                        {{d.district}}
                      </option>
                    </select>
                  </div>
                </div>
    
                <div class="row collapse">
                  <div class="small-6 columns">
                    <select name="select" v-model="statusFilter" @change="updateCQLFilter('bushfireStatus',500)">
                      <option value="" selected>All bushfires</option> 
                      <option value="report_status = 1">Initial Bushfires</option>
                      <option value="report_status = 2">Initial Authorised Bushfires</option>
                      <option value="report_status >= 3">Final Authorised Bushfires</option>
                    </select>
                  </div>
                  <div class="small-6 columns">
                    <input type="search" v-model="search" placeholder="Find a bushfire" @keyup="updateFeatureFilter">
                  </div>
                </div>
    
                <div class="tool-slice row collapse">
                  <div class="small-12 expanded button-group">
                    <a title="Zoom to selected" class="button bfrsbutton" @click="zoomToSelected()" ><img style="width:14px;height:14px"src="dist/static/images/zoom-to-selected.svg"/><br>Zoom To<br>Selected</a>
                    <a title="Refresh bushfire list" class="button bfrsbutton" @click="updateCQLFilter('refresh',200)" ><i class="fa fa-refresh" aria-hidden="true"></i><br>Refresh<br>Bushfires </a>
                    <div v-show="canBatchUpload()">
                        <label class="button bfrsbutton" for="uploadBushfires" title="Support GeoJSON(.geojson .json), GPS data(.gpx), GeoPackage(.gpkg), 7zip(.7z), TarFile(.tar.gz,tar.bz,tar.xz),ZipFile(.zip)" style="line-height:1;">
                            <i class="fa fa-upload"></i><br>Batch<br>Upload
                        </label>
                        <input type="file" id="uploadBushfires" class="show-for-sr" name="bushfiresfile" accept=".json,.geojson,.gpx,.gpkg,.7z,.tar,.tar.gz,.tar.bz,.tar.xz,.zip" v-el:bushfiresfile @change="importList()"/>
                    </div>
                    <a class="button bfrsbutton" @click="downloadList('geojson')" title="Export Bushfire as GeoJSON"><i class="fa fa-download" aria-hidden="true"></i><br>Download<br>(geojson) </a>
                    <a class="button bfrsbutton" @click="downloadList('gpkg')" title="Export Bushfire as GeoPackage"><i class="fa fa-download" aria-hidden="true"></i><br>Download<br>(gpkg)</a>
                  </div>
                </div>
    
            </div>

            <div id="bfrs-list" class="layers-flexibleframe scroller" style="margin-left:-15px; margin-right:-15px;">
              <div v-for="f in features" class="row feature-row" v-bind:class="{'feature-selected': selected(f) }"
                @click="toggleSelect(f)" track-by="get('id')">
                <div class="small-12 columns">
                  <a v-if="canReset(f)"  @click.stop.prevent="resetFeature(f)" title="Reset" class="button tiny secondary float-right acion" style="margin-left:2px"><i class="fa fa-undo actionicon"></i></a>
                  <a v-if="canDelete(f)" @click.stop.prevent="deleteFeature(f)" title="Delete" class="button tiny secondary float-right action" style="margin-left:2px"><i class="fa fa-trash actionicon"></i></a>
                  <a v-if="canUpload(f)"  @click.stop.prevent="uploadBushfire(f)" title="Upload" class="button tiny secondary float-right acion" style="margin-left:2px"><i class="fa fa-upload actionicon"></i></a>
                  <a v-if="canModify(f)" @click.stop.prevent="startEditFeature(f)" title="Edit Bushfire" class="button tiny secondary float-right action">
                    <svg class="editicon"><use xlink:href="dist/static/images/iD-sprite.svg#icon-area"></use></svg>
                  </a>
                  <a v-if="canCreate(f)" @click.stop.prevent="createFeature(f)" title="Create" class="button tiny secondary float-right action" style="margin-left:2px;background-color:red"><i class="fa fa-save actionicon"></i></a>
                  <a v-if="canEdit(f) " @click.stop.prevent="utils.editResource($event)" title="Open bushfire form" href="{{editUrl(f)}}" target="_blank" class="button tiny secondary float-right action" style="margin-left:2px"><i class="fa fa-pencil-square-o actionicon"></i></a>
                  <a v-if="canSave(f)" @click.stop.prevent="saveFeature(f)" title="Save" class="button tiny secondary float-right action" style="margin-left:2px;background-color:red">
                    <i class="fa fa-save actionicon"></i>
                  </a>
                  <div class="feature-title"><img class="feature-icon" id="bushfire-icon-{{f.get('id')}}" v-bind:src="featureIconSrc(f)" /> {{ f.get('label') }} <i><small></small></i></div>
                </div>
                <template v-for="task in featureTasks(f)" track-by="$index">
                  <div class="small-12 columns">
                      <a class="task_status float-right" title="{{revision && task.statusText}}"> <i class="fa {{revision && task.icon}}"></i></a>
                      <a class="task_name">{{task.description}}</a>
                  </div>
                  <div v-if="revision && task.message" class="small-12 columns">
                      <a class="task_message">{{revision && task.message}}</a>
                  </div>

                </template>
              </div>
            </div>

            <div v-show="$root.isShowHints('bfrs')" class="tool-slice row collapse" id="bfrs-hints">
              <hr class="small-12"/>
              <template v-for="hint in hints">
                  <div class="small-12">{{hint.name}}:</div>
                  <div class="small-12">
                    <ul>
                    <template v-for="description in hint.description">
                        <li>{{description}}</li>
                    </template>
                    </ul>
                  </div>
              </template>
            </div>


          </div>

        </div>
      </div>
    </div>

    <form id="bushfire_create" name="bushfire_create" action="{{createUrl()}}" method="post" target="{{utils.getAddressTarget("_blank")}}">
        <input type="hidden" name="sss_create" id="sss_create">
    </form>
  </div>
</template>
<style>
.button-group .bfrsbutton {
    padding-left:10px;
    padding-right:10px;
    font-size:0.8rem;
}
.actionicon {
    width:9px;
    height:9px;
}
.editicon {
    width:16px;
    height:16px;
    margin-top: -3px;
    margin-bottom: -4px;
    margin-left: -2px;
    margin-right: -2px;
}
.task_status {
}
.task_message {
    font-style:italic;
    font-weight:normal;
    color:red;
    font-size:12px;
}
.task_name {
    font-style:normal;
    font-weight:bold;
    font-size:14px;
}
</style>
<script>
  import { ol, moment,hash,turf,utils } from 'src/vendor.js'
  export default {
    store: {
        bushfireLabels:'settings.bfrs.bushfireLabels',
        viewportOnly:'settings.bfrs.viewportOnly',
        screenHeight:'layout.screenHeight',
        hintsHeight:'layout.hintsHeight',
        leftPanelHeadHeight:'layout.leftPanelHeadHeight',
        activeMenu:'activeMenu',
        hints:'hints',
        whoami:'whoami'
    },
    data: function () {
      var fill = '#ff6600'
      var stroke = '#7c3100'
      return {
        selectedOnly: false,
        search: '',
        statusFilter: '',
        region:'',
        district:'',
        bushfireLabelsDisabled:false,
        tools: [],
        fields: ['fire_number', 'name'],
        drawings:new ol.Collection(),
        allFeatures: new ol.Collection(),
        extentFeatures: [],
        selectedBushfires: [],
        revision:1,
        profileRevision:1,
        tints: {
          'new':[["#b43232","#c8c032e6"]],
          'new.text':"#c8c032e6",
          'new.fillColour':[0, 0, 0, 0.25],
          'new.colour':"#c8c032e6",
          'unknown': [['#b43232','#f90c25']],
          'unknown.text': '#f90c25',
          'unknown.fillColour':[0, 0, 0, 0.25],
          'unknown.colour': '#f90c25',
          'initial': [['#b43232','#808080']],
          'initial.text': '#808080',
          'initial.fillColour':[0, 0, 0, 0.25],
          'initial.colour': '#808080',
          'draft_final': [['#b43232', '#ff0000']],
          'draft_final.text': '#ff0000',
          'draft_final.fillColour':[0, 0, 0, 0.25],
          'draft_final.colour': '#ff0000',
          'final_authorised': [['#b43232', '#008000']],
          'final_authorised.text': '#008000',
          'final_authorised.fillColour':[0, 0, 0, 0.25],
          'final_authorised.colour': '#008000',
          'reviewed': [['#b43232', '#008000']],
          'reviewed.text': '#008000',
          'reviewed.fillColour':[0, 0, 0, 0.25],
          'reviewed.colour': '#008000',
          'modified':[["#b43232","#f57900"]],
          'modified.text':"#f57900",
          'modified_authorised.fillColour':[0, 0, 0, 0.25],
          'modified.colour':"#f57900",
          'selected': [['#b43232', '#2199e8']],
          'selected.text': '#2199e8',
        }
      }
    },
    computed: {
      map: function () { return this.$root.$refs.app.$refs.map },
      env: function () { return this.$root.env },
      annotations: function () { return this.$root.$refs.app.$refs.annotations },
      dialog: function () { return this.$root.dialog },
      active: function () { return this.$root.active},
      measure: function () { return this.$root.measure },
      info: function () { return this.$root.info },
      setting: function () { return this.$root.setting },
      catalogue: function () { return this.$root.catalogue },
      export: function () { return this.$root.export },
      loading: function () { return this.$root.loading },
      utils: function () { return this.$root.utils },
      features: function () {
        if (this.viewportOnly) {
          return this.revision && this.extentFeatures
        } else {
          return this.revision && this.allFeatures.getArray()
        }
      },
      moduleStatus: function(){
        return this._bfrsStatus || {}
      },
      isReportMapLayerHidden:function() {
        return this.$root.active.isHidden(this.bushfireMapLayer)
      },
      selectedOnlyDisabled:function() {
        try {
            return (this.annotations.tool !== this.ui.panTool && this.annotations.tool !== this.ui.selectTool) || (this.selectedBushfires.length === 0 && !this.selectedOnly)
        } catch (ex) {
            return true
        }
      },
      selectedFeatures: function () {
        return this.annotations.selectedFeatures
      },
      stats: function () {
        return this.extentFeatures.length + '/' + this.allFeatures.getLength()
      },
      bushfireLayer: function() {
        //console.log(this.env.bushfireLayer)
        return this.$root.catalogue.getLayer(this.env.bushfireLayer)
      },
      bushfireMapLayer: function() {
        return this.$root.map?this.$root.map.getMapLayer(this.bushfireLayer):undefined
      },
      finalFireBoundaryLayer: function() {
        return this.$root.map?this.$root.map.getMapLayer(this.env.finalFireBoundaryLayer):undefined
      },
      selectedFinalFireBoundaryMapLayer: function() {
        return this.bushfireMapLayer?this.bushfireLayer.dependentLayers[1].mapLayer:null
      },
      regionFilter:function() {
        return this.region?("region_id=" + this.region) : null
      },
      districtFilter:function() {
        return this.district?("district_id=" + this.district) : null
      },
      regions:function() {
        try{
            return this.profileRevision && this.whoami["bushfire"]["regions"]
        }catch(ex) {
            return []
        }
      },
      districts:function() {
        var vm = this
        var r = null
        if (this.region) {
            r = this.regions.find(function(o) { return o.region_id === parseInt(vm.region)})
        }
        return r?r.districts:[]
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
                    var geometries = feat.getGeometry().getGeometriesArray()
                    var pointStyle = (geometries.length > 0 || geometries[0] instanceof ol.geom.Point)?pointStyleFunc.call(feat,res):null
                    var boundaryStyle = (geometries.length > 1 || geometries[0] instanceof ol.geom.MultiPolygon)?boundaryStyleFunc.call(feat,res):null

                    var labelStyle = null
                    if (res < 0.003 && geometries.length > 0 && feat.get('label') && vm.bushfireLabels && !vm.$root.active.isHidden(vm.map.getMapLayer(vm.env.bushfireLayer))) {
                      labelStyle = labelStyleFunc.call(feat,res)
                      labelStyle.setGeometry(geometries[0])
                    }   

                    var style = null
                    if ((pointStyle && 1) + (boundaryStyle && 1) + (labelStyle && 1) === 1) {
                        return pointStyle || boundaryStyle || labelStyle
                    } else {
                        if (!vm._bushfireStyle) {
                            vm._bushfireStyle = []
                        } else {
                            vm._bushfireStyle.length = 0
                        }
                        if (pointStyle) {vm._bushfireStyle.push.apply(vm._bushfireStyle,pointStyle)}
                        if (boundaryStyle) {vm._bushfireStyle.push.apply(vm._bushfireStyle,boundaryStyle)}
                        if (labelStyle) {vm._bushfireStyle.push(labelStyle)}
                        return vm._bushfireStyle
                    }
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
            this.bushfireMapLayer.changed() 
        }
      },
      bushfireLabels:function(newValue,oldValue) {
        this.showBushfireLabels()
      },
      tools:function(newValue,oldValue) {
        this.adjustHeight()
      }
    },
    methods: {
      featureTasks:function(feat) {
        return this.revision && ((this._taskManager)?this._taskManager.getTasks(feat):null)
      },
      refreshWMSLayer: function(wait) {
        var vm = this
        wait = wait || 1000
        this._refreshWMSLayer = this._refreshWMSLayer || debounce(function(){
            if (vm.finalFireBoundaryLayer) {
                vm.finalFireBoundaryLayer.refresh()   
            }
        },wait)

        this._refreshWMSLayer.call({wait:wait})
      },
      refreshSelectedWMSLayer: function(wait) {
        var vm = this
        wait = wait || 1000
        this._refreshSelectedWMSLayer = this._refreshSelectedWMSLayer || debounce(function(){
          var selectedFinalFireBoundaryMapLayer = vm.bushfireMapLayer?vm.bushfireLayer.dependentLayers[1].mapLayer:null
          if (!selectedFinalFireBoundaryMapLayer) return

          var selectedWMSFeatures = selectedFeatures.getArray().filter(function(f) {return !vm.isFireboundaryDrawable(f)})
          if (selectedWMSFeatures.length === 0) {
            if (selectedFinalFireBoundaryMapLayer.show) {
                vm.map.enableDependentLayer(vm.bushfireMapLayer,vm.env.finalFireBoundaryLayer + "_selected",false)
            }
          } else {
            selectedFinalFireBoundaryMapLayer.setParams({
                cql_filter:"fire_number in ('" + selectedWMSFeatures.map(function(f){return f.get('fire_number')}).join("','") +  "')"
            })
            if (!selectedFinalFireBoundaryMapLayer.show) {
                vm.map.enableDependentLayer(vm.bushfireMapLayer,vm.env.finalFireBoundaryLayer + "_selected",true)
            }
          }
        },wait)

        this._refreshSelectedWMSLayer.call({wait:wait})
      },
      zoomToSelected:function(wait) {
        var vm = this
        wait = wait || 0
        vm._zoomToSelected = vm._zoomToSelectedFunc || debounce(function() {
            vm.map.zoomToSelected(125,function(f){
                if (f.get('fire_boundary')) {
                    if (f.getGeometry()) {
                        return ol.extent.extend(f.get('fire_boundary'),f.getGeometry().getExtent())
                    } else {
                        return f.get('fire_boundary')
                    }
                } else {
                    return f.getGeometry().getExtent()
                }
            })
        },wait)
        if (wait === 0) {
            vm._zoomToSelected.call({wait:1})
        } else {
            vm._zoomToSelected.call({wait:wait})
        }
      },
      open:function(options) {
        //active bfrs module
        if (this.activeMenu !== "bfrs") {
            $("#menu-tab-bfrs-label").trigger("click")
        } else if(!$('#offCanvasLeft').hasClass('reveal-responsive')){
            $('#offCanvasLeft').toggleClass('reveal-responsive')
            self.map.olmap.updateSize()
        }

        var vm = this
        var updateType = null
        var action = options["action"] || "select"
        if (!options) {return}
        if ("region" in options && options["region"] !== this.region) {
            this.region = options["region"] || ""
            updateType = "region"
        }
        if ("district" in options && options["district"] != this.district) {
            this.district = options["district"] || ""
            updateType = "district"
        }
        this.selectedFeatures.clear()

        updateType = updateType || ((action === "create")?"query":null)
        if (!updateType && options["bushfireid"] !== null && options["bushfireid"] !== undefined){
            var bushfire = this.allFeatures.getArray().find(function(f) {return f.get('fire_number') === options["bushfireid"]})
            if (bushfire) {
                this.selectedFeatures.push(bushfire)
                if (options["refresh"] || action === "update") {
                    this.resetFeature(bushfire,function() {
                        vm.zoomToSelected()
                    })
                } else {
                    this.zoomToSelected()
                }
                return
            } else {
                updateType = "query"
            }
        }

        if (updateType || options["refresh"]) {
            this.updateCQLFilter(updateType,(updateType === "query")?0:1,function(){
                if (options["bushfireid"] !== null && options["bushfireid"] !== undefined){
                    var feat = vm.allFeatures.getArray().find(function(o) {return o.get('fire_number') == options["bushfireid"]})
                    if (feat) {
                        vm.selectedFeatures.push(feat)
                        vm.zoomToSelected()
                    }
                }

            })
        }

      },
      isModifiable:function(bushfire) {
        try{
            return this.whoami["bushfire"]["permission"][bushfire.get('status') + ".modify"]
        } catch(ex){
            return false
        }
      },
      isFireboundaryDrawable:function(bushfire) {
        return bushfire.get('status') === "new" || (bushfire.get('report_status') === 1)
      },
      isEditable:function(bushfire) {
        try{
            return this.whoami["bushfire"]["permission"][bushfire.get('status') + ".edit"]
        } catch(ex){
            return false
        }
      },
      isDeletable:function(bushfire) {
        return bushfire.get('status') === "new"
      },
      isCreatable:function() {
        try {
            return this.revision && this.whoami["bushfire"]["permission"]["create"] 
        } catch(ex) {
            return false
        }
      },
      canBatchUpload:function() {
        try{
            return this.revision && this.whoami["bushfire"]["permission"]["final_authorised.modify"]
        } catch(ex) {
            return false
        }
      },
      canEdit:function(bushfire) {
        return this.revision && bushfire.get('status') !== "new" && this.isEditable(bushfire) && bushfire.get('tint') !== "modified"
      },
      canUpload:function(bushfire) {
        return this.revision && this.isModifiable(bushfire)
      },
      canModify:function(bushfire) {
        return this.revision && this.isModifiable(bushfire)
      },
      canReset:function(bushfire) {
        return this.revision && bushfire.get('status') !== "new" // && this.isEditable(bushfire) && bushfire.get('tint') === "modified"
      },
      canSave:function(bushfire) {
        return this.revision && bushfire.get('status') !== "new" && this.isModifiable(bushfire) && bushfire.get('tint') === "modified"
      },
      canCreate:function(bushfire) {
        return this.revision && bushfire.get('status') === "new" && bushfire.getGeometry().getGeometriesArray().find(function(g) {return g instanceof ol.geom.Point})
      },
      canDelete:function(bushfire) {
        return this.revision && this.isDeletable(bushfire)
      },
      createUrl:function() {
        return this.env.bfrsService + "/bfrs/create/" 
      },
      editUrl:function(feat) {
        var status = feat.get('report_status')
        if (status === 1) {
            return this.env.bfrsService + "/bfrs/initial/" + feat.get('id') + "/"
        } else {
            return this.env.bfrsService + "/bfrs/final/" + feat.get('id') + "/"
        }
      },
      saveUrl:function(feat) {
        return this.env.bfrsService + "/api/v1/bushfire/" + feat.get('id') + "/?format=json" 
      },
      deleteUrl:function(feat) {
        return this.env.bfrsService + "/delete/" + feat.get('id')
      },
      startEditFeature:function(feat) {
        if (this.annotations.tool !== this.ui.modifyTool) {
            this.annotations.setTool(this.ui.modifyTool)
        }
        if (this.selectedFeatures.getLength() === 1 || this.selectedFeatures.item(0) !== feat) {
            if (this.selectedFeatures.getLength() > 0) this.selectedFeatures.clear()
            this.selectedFeatures.push(feat)
        }
      },
      validateBushfire:function(feat,validateType,callback) {
        var indexes = null
        this._validateBushfireCallback = this._validateBushfireCallback || function(error,callback) {
            if (callback) {
                callback(error)
            } else if (error) {
                alert(error)
            }
        }
        var vm = this
        try {
            var geometries = feat.getGeometry().getGeometries()
            var originPoint = geometries.find(function(g) {return g instanceof ol.geom.Point}) || null
    
            if (!originPoint) {
                throw "No origin point placed"
            }
            if (!this.isFireboundaryDrawable(feat)) {
                if ((feat.get('modifyType') & 2) !== 2) {
                    if (feat.get('fire_boundary')) {
                        //only move  the original point
                        originPoint = originPoint.getCoordinates()
                        if (validateType === "getSpatialData") {
                            //during saving, check agaist the fire boundary
                            $.ajax({
                                url:vm.env.wfsService + "/wfs?service=wfs&version=2.0&request=GetPropertyValue&valueReference=fire_number&typeNames=" + vm.env.finalFireBoundaryLayer + "&cql_filter=(fire_number='" + feat.get('fire_number') + "')and (CONTAINS(fire_boundary,POINT(" + originPoint[1]  + " " + originPoint[0] + ")))",
                                dataType:"xml",
                                success: function (response, stat, xhr) {
                                    if (response.firstChild && response.firstChild.children && response.firstChild.children.length > 0) {
                                        vm._validateBushfireCallback(null,callback)
                                    } else if (callback) {
                                        vm._validateBushfireCallback("Original point should be inside a fire boundary.",callback)
                                    }
                                },
                                error: function (xhr,status,message) {
                                    vm._validateBushfireCallback(xhr.responseText || message,callback)
                                },
                                xhrFields: {
                                    withCredentials: true
                                }
                            })
                        } else {
                            //during modifing,check agaist the bbox of fire boundary
                            if (ol.extent.containsCoordinate(feat.get('fire_boundary'),originPoint)) {
                                vm._validateBushfireCallback(null,callback)
                            } else {
                                vm._validateBushfireCallback("Original point should be inside a fire boundary.",callback)
                            }
                        }
                    } else {
                        vm._validateBushfireCallback(null,callback)
                    }
                } else {
                    vm._validateBushfireCallback(null,callback)
                }
                return
            }
    
            var fireboundary = null
            indexes = geometries.findIndex(function(g) {return g instanceof ol.geom.MultiPolygon})
            if (indexes >= 0) {
                fireboundary = geometries[indexes]
                indexes = [indexes]
            } else {
                fireboundary = null
                indexes = null
            }
    
            var polygon = null
            var polygonIndex = -1
            var convertedToTurf = true
            var checkResult = false
            //check self-intersect and polygon intersect.
            //during checking, polygons are converted into turf polygon and cached in the local variable
            if (fireboundary && fireboundary.getPolygons().length === 1) {
                fireboundary = fireboundary.getCoordinates()
                fireboundary[0] = turf.polygon(fireboundary[0])
                if (turf.kinks(fireboundary[0]).features.length > 0) {
                    if (indexes) indexes.push(0)
                    throw "The polygon is self intersection, please fix it."
                }
            } else if (fireboundary && fireboundary.getPolygons().length > 1) {
                fireboundary = fireboundary.getCoordinates()
                //validate whether any existed polygons are intersect
                for(index = 0;index < fireboundary.length;index++) {
                    if (index === 0) {fireboundary[index] = turf.polygon(fireboundary[index])}
                    for(index2 = index + 1;index2 < fireboundary.length;index2++) {
                        if (index === 0) {fireboundary[index2] = turf.polygon(fireboundary[index2])}
                        try {
                            checkResult = turf.intersect(fireboundary[index],fireboundary[index2]) 
                        } catch(ex) {
                            if (index === 0 && index2 === 1 && turf.kinks(fireboundary[index]).features.length > 0) {
                                if (indexes) indexes.push(index)
                                throw "Some fire boundary are self intersection, please fix it."
                            } else if (index === 0 && turf.kinks(fireboundary[index2]).features.length > 0) {
                                if (indexes) indexes.push(index2)
                                throw "Some fire boundary are self intersection, please fix it."
                            } else {
                                if (indexes) indexes.push(index)
                                throw "Some fire boundary are invalid, please fix it."
                            }
                        }
                        if (checkResult) {
                            if (indexes) indexes.push(index)
                            throw "Some fire boundaries are intersect, please fix it."
                        }
                    }
                }
            }
    
            if (originPoint) {
                inFireBoundary = null
                originPoint = turf.point(originPoint.getCoordinates())
                //checking whether origin point is in a existing fireboundary
                if (fireboundary && fireboundary.length > 0) {
                    inFireBoundary = false
                    for(index = 0;index < fireboundary.length;index++) {
                        if (!convertedToTurf) {
                            fireboundary[index] = turf.polygon(fireboundary[index])
                        }
                        if (turf.inside(originPoint,fireboundary[index])) {
                            inFireBoundary = true
                            break;
                        }
                    }
                }
                //checking whether origin point is in new fireboundary
                if (inFireBoundary !== true && polygon && validateType !== "deleteFireBoundary" && polygonIndex === -1) {
                    inFireBoundary = false
                    if (turf.inside(originPoint,polygon)) {
                        inFireBoundary = true
                    }
                }
    
                if (inFireBoundary === false) {
                    indexes = [0]
                    throw "Original point should be inside a fire boundary."
                }
                convertedToTurf = true
            }
            vm._validateBushfireCallback(null,callback)
        }catch(ex) {
            if (!feat.get('external_feature')) {
                if (indexes) {feat['selectedIndex'] = indexes}
                if (this.annotations.tool !== this.ui.modifyTool) {
                    this.annotations.setTool(this.ui.modifyTool)
                }
                if (this.annotations.selectedFeatures.length !== 1 || this.annotations.selectedFeatures.item(0) !== feat) {
                    this.annotations.selectedFeatures.clear()
                    this.annotations.selectedFeatures.push(feat)
                }
            }

            vm._validateBushfireCallback(ex.message || ex,callback)
        }
      },
      getSpatialData:function(feat,callback,failedCallback) {
        var vm = this
        vm._getSpatialDataCallback = vm._getSpatialDataCallback || function(feat,callback,failedCallback,spatialData) {
            if (vm._taskManager.allTasksSucceed(feat,"getSpatialData")) {
                if ("region" in spatialData && "district" in spatialData) {
                    var region = null
                    var district = null
                    spatialData["region_id"] = null
                    spatialData["district_id"] = null

                    var name = spatialData["region"]
                    delete spatialData["region"]
                    if (name) {
                        name = name.toLowerCase()
                        region = vm.whoami.bushfire.regions.find(function(o) {return o.region.toLowerCase() === name})
                        if (region) {
                            spatialData["region_id"] = region.region_id
                        } else {
                            if (failedCallback) {
                                failedCallback("Region '" + name + "' is not found")
                            } else {
                                alert("Region '" + name + "' is not found")
                            }
                            return
                        }
                    }

                    name = spatialData["district"]
                    delete spatialData["district"]
                    if (name && region) {
                        name = name.toLowerCase()
                        district = region.districts.find(function(o) {return o.district.toLowerCase() === name})
                        if (district) {
                            spatialData["district_id"] = district.id
                        } else {
                            if (failedCallback) {
                                failedCallback("District '" + name + "' is not found in region '" + region.region + "'.")
                            } else {
                                alert("District '" + name + "' is not found in region '" + region.region + "'.")
                            }
                            return
                        }
                    }
                }

                console.log( JSON.stringify(spatialData ) )
                callback(spatialData)
            } else if (vm._taskManager.allTasksFinished(feat,"getSpatialData")) {
                if (failedCallback) failedCallback("")
            }
        }

        vm._getSpatialData = vm._getSpatialData || function(feat,callback,failedCallback) {
            try{
                var spatialData = {}
                var modifyType = (feat.get('status') === 'new')?3:(feat.get('modifyType') || 3)
        
                var geometries = feat.getGeometry().getGeometriesArray()
                var originPoint = geometries.find(function(g){return g instanceof ol.geom.Point}) || null
                originPoint = originPoint?originPoint.getCoordinates():null
        
                var fireboundary = null
                var bbox = null
                var area = 0
        
                if ((modifyType & 1) === 1) {
                    spatialData["origin_point"] = originPoint
                    spatialData["tenure_ignition_point"]  = null
                    spatialData["fire_position"]  = null
                }
        
                if ((modifyType & 2) === 2) {
                    fireboundary = geometries.find(function(g) {return g instanceof ol.geom.MultiPolygon}) || null
                    bbox = (fireboundary && fireboundary.getPolygons().length > 0)?fireboundary.getExtent():null
                    fireboundary = (fireboundary && fireboundary.getPolygons().length > 0)?fireboundary.getCoordinates():null
        
                    spatialData["fire_boundary"] = fireboundary
                }
        
                var tenure_area_task = null
                if (fireboundary && (modifyType & 2) === 2) {
                    tenure_area_task = vm._taskManager.addTask(feat,"getSpatialData","tenure_area","Calculate fire boundary areas",utils.WAITING)
                }
                var tenure_origin_point_task = null
                var fire_position_task = null
                var region_task = null
                var district_task = null
                if (originPoint && (modifyType & 1) === 1) {
                    tenure_origin_point_task = vm._taskManager.addTask(feat,"getSpatialData","tenure_origin_point","Locate bushfire's dpaw tenure",utils.WAITING)
                    fire_position_task = vm._taskManager.addTask(feat,"getSpatialData","fire_position","Get the fire position",utils.WAITING)
                    if (["new","initial"].indexOf(feat.get('status')) >= 0) {
                        region_task = vm._taskManager.addTask(feat,"getSpatialData","region","Locate bushfire's region",utils.WAITING)
                        district_task = vm._taskManager.addTask(feat,"getSpatialData","district","Locate bushfire's district",utils.WAITING)
                    }
                }
                //need to call the callback first because the callback will not be called if no tasks are required.
                vm._getSpatialDataCallback(feat,callback,failedCallback,spatialData)
                if (tenure_area_task) {
                    tenure_area_task.setStatus(utils.RUNNING)
                    $.ajax({
                        url:vm.env.gokartService + "/spatial",
                        dataType:"json",
        
                        data:{
                                features:vm.$root.geojson.writeFeatures([feat]),
                                options:JSON.stringify({
                                    area: {
                                        name:"area",
                                        layer_overlap:false,
                                        unit:"ha",
                                        layers:[
                                            {
                                                id:"tenure_area",
                                                url:vm.env.wfsService + "/wfs?service=wfs&version=2.0&request=GetFeature&typeNames=cddp:dpaw_tenure",
                                                properties:{
                                                    id:"ogc_fid",
                                                    name:"name",
                                                    category:"category"
                                                }
                                            }
                                        ],
                                    }
                                })
                        },
                        method:"POST",
                        success: function (response, stat, xhr) {
                            if (response["total_features"] > 0) {
                                $.extend(spatialData,response["features"][0])
                                tenure_area_task.setStatus(utils.SUCCEED)
                            } else {
                                tenure_area_task.setStatus(utils.FAILED,"Calculate area failed.")
                                alert(tenure_area_task.message)
                            }
                            vm._getSpatialDataCallback(feat,callback,failedCallback,spatialData)
                        },
                        error: function (xhr,status,message) {
                            tenure_area_task.setStatus(utils.FAILED,status + " : " + (xhr.responseText || message))
                            alert(tenure_area_task.message)
                            vm._getSpatialDataCallback(feat,callback,failedCallback,spatialData)
                        },
                        xhrFields: {
                            withCredentials: true
                        }
                    })
                }
        
                if (tenure_origin_point_task) {
                    tenure_origin_point_task.setStatus(utils.RUNNING)
                    $.ajax({
                        url:vm.env.wfsService + "/wfs?service=wfs&version=2.0&request=GetFeature&typeNames=cddp:dpaw_tenure&outputFormat=json&cql_filter=CONTAINS(wkb_geometry,POINT(" + originPoint[1]  + " " + originPoint[0] + "))",
                        dataType:"json",
                        success: function (response, stat, xhr) {
                            if (response.totalFeatures === 0) {
                                spatialData["tenure_ignition_point"] = null
                            } else {
                                spatialData["tenure_ignition_point"] = {
                                    id: response.features[0].properties["ogc_fid"],
                                    name: response.features[0].properties["name"],
                                    category: response.features[0].properties["category"]
                                }
                            }
                            tenure_origin_point_task.setStatus(utils.SUCCEED)
                            vm._getSpatialDataCallback(feat,callback,failedCallback,spatialData)
                        },
                        error: function (xhr,status,message) {
                            tenure_origin_point_task.setStatus(utils.FAILED,status + " : " + (xhr.responseText || message))
                            alert(tenure_origin_point_task.message)
                            vm._getSpatialDataCallback(feat,callback,failedCallback,spatialData)
                        },
                        xhrFields: {
                            withCredentials: true
                        }
                    })
                }
        
                if (fire_position_task) {
                    fire_position_task.setStatus(utils.RUNNING)
                    var buffers = [50,100,150,200,300,400,1000,2000,100000]
                    var getFirePosition = function(index) {
                        var buffered = turf.bbox(turf.buffer(turf.point(originPoint),buffers[index],"kilometers"))
                        $.ajax({
                            url:vm.env.wfsService + "/wfs?service=wfs&version=2.0&request=GetFeature&typeNames=cddp:townsite_points&outputFormat=json&bbox=" + buffered[1] + "," + buffered[0] + "," + buffered[3] + "," + buffered[2],
                            dataType:"json",
                            success: function (response, stat, xhr) {
                                if (response.totalFeatures === 0) {
                                    getFirePosition(index + 1)
                                } else {
                                    var nearestTown = null
                                    var nearestDistance = null
                                    var distance = null
                                    $.each(response.features,function(index,feature){
                                        if (nearestTown === null) {
                                            nearestTown = feature
                                            nearestDistance = vm.measure.getLength([feature.geometry.coordinates,originPoint])
                                        } else {
                                            distance = vm.measure.getLength([feature.geometry.coordinates,originPoint])
                                            if (distance < nearestDistance) {
                                                nearestTown = feature
                                                nearestDistance = distance
                                            }
                                        }
                                    })
                                    nearestDistance = vm.measure.formatLength(nearestDistance,"km")
                                    var bearing = null
                                    if (nearestDistance === 0) {
                                        spatialData["fire_position"] = "0m of " + nearestTown.properties["name"]
                                    } else {
                                        bearing = vm.measure.getBearing(nearestTown.geometry.coordinates,originPoint)
                                        spatialData["fire_position"] = nearestDistance + " " + vm.measure.getDirection(bearing,16) + " of " + nearestTown.properties["name"]
                                    }
            
                                    fire_position_task.setStatus(utils.SUCCEED)
                                    vm._getSpatialDataCallback(feat,callback,failedCallback,spatialData)
            
                                }
                            },
                            error: function (xhr,status,message) {
                                fire_position_task.setStatus(utils.FAILED,status + " : " + (xhr.responseText || message))
                                alert(fire_position_task.message)
                                vm._getSpatialDataCallback(feat,callback,failedCallback,spatialData)
                            },
                            xhrFields: {
                                withCredentials: true
                            }
                        })
                    }
                    getFirePosition(0)
                }
        
                if (region_task) {
                    region_task.setStatus(utils.RUNNING)
                    $.ajax({
                        url:vm.env.wfsService + "/wfs?service=wfs&version=2.0&request=GetFeature&typeNames=cddp:dpaw_regions&outputFormat=json&cql_filter=CONTAINS(wkb_geometry,POINT(" + originPoint[1]  + " " + originPoint[0] + "))",
                        dataType:"json",
                        success: function (response, stat, xhr) {
                            if (response.totalFeatures === 0) {
                                spatialData["region"] = null
                            } else {
                                spatialData["region"] = response.features[0].properties["region"]
                            }
                            region_task.setStatus(utils.SUCCEED)
                            vm._getSpatialDataCallback(feat,callback,failedCallback,spatialData)
                        },
                        error: function (xhr,status,message) {
                            region_task.setStatus(utils.FAILED,status + " : " + (xhr.responseText || message))
                            alert(region_task.message)
                            vm._getSpatialDataCallback(feat,callback,failedCallback,spatialData)
                        },
                        xhrFields: {
                            withCredentials: true
                        }
                    })
                }
        
                if (district_task) {
                    district_task.setStatus(utils.RUNNING)
                    $.ajax({
                        url:vm.env.wfsService + "/wfs?service=wfs&version=2.0&request=GetFeature&typeNames=dpaw:pw_districts_fssvers&outputFormat=json&cql_filter=CONTAINS(wkb_geometry,POINT(" + originPoint[1]  + " " + originPoint[0] + "))",
                        dataType:"json",
                        success: function (response, stat, xhr) {
                            if (response.totalFeatures === 0) {
                                spatialData["district"] = null
                            } else {
                                spatialData["district"] = response.features[0].properties["district"]
                            }
                            district_task.setStatus(utils.SUCCEED)
                            vm._getSpatialDataCallback(feat,callback,failedCallback,spatialData)
                        },
                        error: function (xhr,status,message) {
                            district_task.setStatus(utils.FAILED,status + " : " + (xhr.responseText || message))
                            alert(district_task.message)
                            vm._getSpatialDataCallback(feat,callback,failedCallback,spatialData)
                        },
                        xhrFields: {
                            withCredentials: true
                        }
                    })
                }
            } catch(ex) {
                vm._getSpatialDataCallback(feat,callback,failedCallback,spatialData)
            }
        }

        try {
            var validate_task = vm._taskManager.addTask(feat,"getSpatialData","validate","Validate bushfire",utils.RUNNING)
            this.validateBushfire(feat,"getSpatialData",function(error) {
                if (error) {
                    validate_task.setStatus(utils.FAILED,error)
                    alert(error)
                    vm._getSpatialDataCallback(feat,callback,failedCallback,{})
                } else {
                    validate_task.setStatus(utils.SUCCEED)
                    vm._getSpatialData(feat,callback,failedCallback)
                }
            })
        } catch(ex) {
            vm._getSpatialDataCallback(feat,callback,failedCallback,{})
        }
      },
      saveFeature:function(feat,callback,failedCallback) {
        if (this.canSave(feat)) {
            var vm = this
            if (!callback && !vm._taskManager.initTasks(feat)) {
                return
            }
            var task = vm._taskManager.addTask(feat,"save","save","Save spatial data",utils.RUNNING)
            vm.getSpatialData(feat,function(spatialData,job){
                $.ajax({
                    url: vm.saveUrl(feat),
                    method:"PATCH",
                    data:JSON.stringify(spatialData),
                    contentType:"application/json",
                    success: function (response, stat, xhr) {
                        task.setStatus(utils.SUCCEED)

                        if (!vm.isFireboundaryDrawable(feat)) {
                            if ((feat.get('modifyType') & 2) === 2) {
                                var originPoint = feat.getGeometry().getGeometries().find(function(g) {return g instanceof ol.geom.Point}) || null
                                if (originPoint) {
                                    originPoint = originPoint.getCoordinates()
                                    $.ajax({
                                        url:vm.env.wfsService + "/wfs?service=wfs&version=2.0&request=GetPropertyValue&valueReference=fire_number&typeNames=" + vm.env.finalFireBoundaryLayer + "&cql_filter=(fire_number='" + feat.get('fire_number') + "')and (CONTAINS(fire_boundary,POINT(" + originPoint[1]  + " " + originPoint[0] + ")))",
                                        dataType:"xml",
                                        success: function (response, stat, xhr) {
                                            if (!response.firstChild || !response.firstChild.children || response.firstChild.children.length === 0) {
                                                alert("Original point is not in fire boundary, please fix it.")
                                            }
                                        },
                                        error: function (xhr,status,message) {
                                            alert(xhr.responseText || message)
                                        },
                                        xhrFields: {
                                            withCredentials: true
                                        }
                                    })
                                }
                            }
                        }

                        if (callback) {
                            callback(feat)
                        } else {
                            vm._taskManager.clearTasks(feat)
                            vm.resetFeature(feat)
                            /*
                            feat.set('tint',feat.get('originalTint'),true)
                            feat.set('fillColour',vm.tints[feat.get('tint') + ".fillColour"])
                            feat.set('colour',vm.tints[feat.get('tint') + ".colour"])
                            vm.revision += 1
                            */
                        }
                    },
                    error: function (xhr,status,message) {
                        task.setStatus(utils.FAILED,status + " : " + (xhr.responseText || message))
                        alert(task.message)
                        if (failedCallback) failedCallback(task.message)
                    },
                    xhrFields: {
                        withCredentials: true
                    }
                })
            },
            function(ex) {
                task.setStatus(utils.FAILED,ex.message || ex)
                if (failedCallback) failedCallback(task.message)
            })
        }
      },
      newFeature:function(feat) {
        var vm = this
        this._bushfireSequence = (this._bushfireSequence || 0) 
        var featId = 0
        if (feat && feat.get('id')) {
            if (Math.abs(feat.get('id')) > this._bushfireSequence) {
                this._bushfireSequence = Math.abs(feat.get('id'))
            }
            featId = Math.abs(feat.get('id'))
        } else {
            this._bushfireSequence += 1
            featId = this._bushfireSequence 
        }
        var label = "New bushfire " + ((featId < 10)?"00":(featId < 100?"0":"")) + featId
        if (feat) {
            feat.set('status','new',true)
            feat.set('tint','new',true)
            feat.set('id',featId * -1,true) 
            feat.set('originalTint','new',true)
            feat.set('label',label,true)
            feat.set('name',"",true)
            feat.set('toolName','Bfrs Origin Point',true)
            feat.set('fillColour',this.tints["new.fillColour"],true)
            feat.set('colour',this.tints["new.colour"],true)
        } else {
            feat = new ol.Feature({
                geometry:new ol.geom.GeometryCollection([]),
                status:'new',
                tint:'new',
                id:this._bushfireSequence * -1, 
                originalTint:'new',
                label: label,
                name:"",
                toolName:'Bfrs Origin Point',
                fillColour:this.tints["new.fillColour"],
                colour:this.tints["new.colour"],
            })
        }
        feat.setStyle(this.bushfireStyleFunc)
        feat.set('modifyType',3,true)
        feat.set('fire_number',feat.get('id').toString(),true)

        this.bushfireMapLayer.getSource().addFeature(feat)
        var insertIndex = null
        $.each(this.allFeatures.getArray(),function(index,f){
            if (f.get('status') === 'new') {
                if (featId < Math.abs(f.get('id'))) {
                    insertIndex = index
                    return false
                }
            } else {
                insertIndex = index
                return false
            }
        })
        if (insertIndex != null) {
            this.allFeatures.insertAt(insertIndex,feat)
        } else {
            this.allFeatures.push(feat)
        }

        this.revision += 1
        return feat
      },
      createFeature:function(feat) {
        if (this.canCreate(feat)) {
            var vm = this
            if (!vm._taskManager.initTasks(feat)) {
                return
            }
            var task = vm._taskManager.addTask(feat,"create","create","Open bushfire report form",utils.RUNNING)
            this.getSpatialData(feat,function(spatialData,job) {
                feat.set("saved",true,true)
                feat.set("modifyType",0,true)
                feat.set("sss_id",feat.getGeometry().getGeometriesArray()[0].getCoordinates(),true)
                $("#sss_create").val(JSON.stringify(spatialData))
                $("#bushfire_create").submit()
                task.setStatus(utils.SUCCEED)
                vm._taskManager.clearTasks(feat)
            },
            function(ex){
                task.setStatus(utils.FAILED,ex.message || ex)
            })
        }
      },
      deleteFeature:function(feat) {
         var vm = this
         if (this.canDelete(feat)) {
            vm._deleteFeature = vm._deleteFeature || function(feat) {
                //console.log("Delete feature " + feat.get('label'))
                vm.bushfireMapLayer.getSource().removeFeature(feat)
                vm.allFeatures.remove(feat)
                vm.selectedFeatures.remove(feat)
                var index = vm.extentFeatures.findIndex(function(f){ return f == feat})
                if (index >= 0) {
                    vm.extentFeatures.splice(index,1)
                }
                vm.revision += 1
            }
            if (feat.get('status') === 'new') {
                vm._deleteFeature(feat)
            } else if (window.confirm('The bushfire (' + feat.get('label') + ' will be deleted. Are you sure?')) {
                $.ajax({
                    url: vm.deleteUrl(feat),
                    success: function (response, stat, xhr) {
                        vm._deleteFeature(feat)
                    },
                    error: function (xhr,status,message) {
                        alert(status + " : " + (xhr.responseText || message))
                    },
                    xhrFields: {
                      withCredentials: true
                    }
                })
            }
        }
      },
      resetFeature:function(feat,callback) {
        var vm = this
        var filter = 'fire_number=\'' + feat.get('fire_number') + '\''
        this.bushfireMapLayer.getSource().retrieveFeatures(filter,function(features){
          if (features && features.length) {
            vm.initBushfire(features[0])
            var f = vm.bushfireMapLayer.getSource().getFeatures().find(function(f) {return f.get('fire_number') === feat.get('fire_number')})
            if (f) {
                vm.bushfireMapLayer.getSource().removeFeature(f)
            }
            if (feat.selectedIndex !== undefined) {
                if (vm.annotations.getSelectedGeometry(features[0],feat.selectedIndex)) {
                    features[0].selectedIndex = f.selectedIndex
                } else {
                    vm.selectDefaultGeometry(features[0])
                }
            }

            vm.bushfireMapLayer.getSource().addFeature(features[0])

            var index = vm.allFeatures.getArray().findIndex(function(f){return f.get('fire_number') === feat.get('fire_number')})
            if (index >= 0) {
                vm.allFeatures.setAt(index,features[0])
                vm.revision += 1
            }

            if (vm.extentFeatures) {
                index = vm.extentFeatures.findIndex(function(f){return f.get('fire_number') === feat.get('fire_number')})
                if (index >= 0) {
                    vm.extentFeatures[index] = features[0]
                }
            }

            index = vm.selectedFeatures.getArray().findIndex(function(f){return f.get('fire_number') === feat.get('fire_number')})
            if (index >= 0) {
                vm.selectedFeatures.setAt(index,features[0])
            }
              
            if (callback) {
                callback(features[0])
            }
            vm._checkPermission(features)
          } else {
            //feature does not exist or is invalid, remove it from bushfire list
            vm.bushfireMapLayer.getSource().removeFeature(feat)
            vm.allFeatures.remove(feat)

            vm.selectedFeatures.remove(feat)
            var index = vm.extentFeatures.findIndex(function(f){ return f == feat})
            if (index >= 0) {
                vm.extentFeatures.splice(index,1)
            }
            vm.revision += 1
            if (callback) {
                callback(null)
            }
          }
          vm.refreshWMSLayer()
        })
      },  
      adjustHeight:function() {
        if (this.activeMenu === "bfrs") {
            //$("#bfrs-list").height(this.screenHeight - this.leftPanelHeadHeight - 16 - 16 - 16 - 2 - $("#bfrs-list-controller-container").height() - this.hintsHeight)
            $("#bfrs-list").height(this.screenHeight - this.leftPanelHeadHeight - 50 - $("#bfrs-list-controller-container").height() - this.hintsHeight)
        }
      },
      //modifyType(bit value): 
      //    first bit:  origin point modified; 
      //    second bit: fire boundary modified.
      //    -1: feature is drawed ,can't figure out which part of spatial data was modified  
      postModified:function(bushfires,modifyType) {
        var vm = this
        var sortRequired = false
        this._bushfirePostModified = this._bushfirePostModified || function(bushfire,modifyType) {
            if (bushfire.get('tint') !== "modified" && (bushfire.get('status') !== "new" || bushfire.get("saved"))) {
                bushfire.set('tint',"modified",true)
                bushfire.set('fillColour',vm.tints[bushfire.get('tint') + ".fillColour"])
                bushfire.set('colour',vm.tints[bushfire.get('tint') + ".colour"])
            }
            if (modifyType === -1) {
                if (vm.isFireboundaryDrawable(bushfire)) {
                    //both fireboundary and point can be changed, don't which part of spatial data was changed,
                    modifyType = 3
                } else {
                    //only point can be changed.
                    modifyType = 1
                }
            }
            bushfire.set('modifyType',(bushfire.get('modifyType') || 0) | modifyType,true)
            var index = (vm.extentFeatures)?vm.extentFeatures.findIndex(function(f) { return f === bushfire}):-1
            if (index >= 0) {
                if (bushfire.getGeometry().getGeometriesArray().length === 0 && 
                    (!bushfire.get('fire_boundary'))
                ) {
                    //all geometries are deleted
                    vm.extentFeatures.splice(index,1)
                }
            } else {
                if (bushfire.getGeometry().getGeometriesArray().length > 0 || 
                    (bushfire.get('fire_boundary'))
                ) {
                    vm.extentFeatures.push(bushfire)
                    sortRequired = true
                }
            }
        }
        if (Array.isArray(bushfires)) {
            $.each(bushfires,function(index,bushfire){
                vm._bushfirePostModified(bushfire,modifyType)
            })
        } else {
            vm._bushfirePostModified(bushfires,modifyType)
        }
        if (sortRequired) {
            vm.extentFeatures.sort(vm.featureOrder)
        }
        vm.revision += 1
      },
      isModified:function(feat){
        return feat.get('tint') === 'modified'
      },
      toggleSelect: function (f) {
        if (this.selected(f)) {
          this.selectedFeatures.remove(f)
        } else {
          if (["Bfrs Origin Point","Bfrs Edit Geometry","Bfrs Fire Boundary"].indexOf(this.annotations.tool.name) >= 0) {
              //Only one bush fire can be choosed in edit mode
              this.selectedFeatures.clear()
          }
          this.selectedFeatures.push(f)
        }
        //this.zoomToSelected(200)
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
      initBushfire:function(feature) {
        feature.set('status',this._reportStatus[feature.get('report_status') || 99999],true)

        var geometries = feature.getGeometry()?[feature.getGeometry()]:[]
        if (feature.get("fire_boundary")) {
            var fire_boundary = JSON.parse(feature.get("fire_boundary"))
            if (fire_boundary.coordinates) {
                if (!this.isFireboundaryDrawable(feature)) {
                    feature.set("fire_boundary",new ol.geom.Polygon(fire_boundary.coordinates).getExtent(),true)
                } else {
                    geometries.push(new ol.geom.MultiPolygon(fire_boundary.coordinates))
                    feature.unset("fire_boundary",true)
                }
            } else {
                feature.unset("fire_boundary",true)
            }
        } else {
            feature.unset("fire_boundary",true)
        }
        feature.setGeometry(new ol.geom.GeometryCollection(geometries),true)
        var now = moment()
        var timestamp = moment(feature.get('created'))

        feature.set('status',this._reportStatus[feature.get('report_status') || 99999],true)

        feature.set('label',feature.get('fire_number'),true)

        feature.set('toolName','Bfrs Origin Point',true)
        feature.set('tint',feature.get('status'),true)
        feature.set('originalTint', feature.get('tint'),true)
        feature.set('fillColour',this.tints[feature.get('tint') + ".fillColour"])
        feature.set('colour',this.tints[feature.get('tint') + ".colour"])
        feature.setStyle(this.bushfireStyleFunc)
      },
      showBushfireLabels:function() {
        if (this.bushfireMapLayer && !this.$root.active.isHidden(this.bushfireMapLayer)) {
            this.bushfireMapLayer.changed()
        }
      },
      featureIconSrc:function(f) {
        var vm = this
        //trigger dynamic binding
        return this.map.getBlob(f, ['icon', 'originalTint'],this.tints,function(){
            $("#bushfire-icon-" + f.get('id')).attr("src", vm.featureIconSrc(f))
        })
      },
      selected: function (f) {
        return f.get('fire_number') && (this.selectedBushfires.indexOf(f.get('fire_number')) > -1)
      },
      downloadList: function (fmt) {
        var downloadFeatures = []
        var vm = this
        var feature = null
        var geometries = null
        var id = 0
        var newBushfiresPoint = []
        var newBushfiresBoundary = []
        $.each(this.features,function(index,f){
            if (f.get('status') == 'new') {
                geometries = f.getGeometry().getGeometriesArray()

                feature = vm.map.cloneFeature(f,false,['toolName','tint','originalTint','fillColour','colour','status','label','measurement','fire_boundary','modifyType'])
                feature.setGeometry( geometries.find(function(g) {return g instanceof ol.geom.Point}) || null)
                feature.setId(++id)
                newBushfiresPoint.push(feature)

                feature = vm.map.cloneFeature(feature,false)
                feature.setGeometry(geometries.find(function(g){ return g instanceof ol.geom.MultiPolygon}) || new ol.geom.MultiPolygon())
                feature.setId(++id)
                newBushfiresBoundary.push(feature)
            }
        })
        cql_filter = (vm.bushfireLayer.cql_filter)?("&cql_filter=" + vm.bushfireLayer.cql_filter):""
        var options = {
            filename:"bushfires",
            srs:"EPSG:4326",
            layers:[{
                layer:"initial_bushfire_originpoint",
                sourcelayers:{
                    url:vm.env.wfsService + "/wfs?service=wfs&version=2.0&request=GetFeature&typeNames=" + vm.env.bushfireLayer + cql_filter ,
                    where:"report_status=1",
                }
            },{
                layer:"final_bushfire_originpoint",
                sourcelayers:{
                    url:vm.env.wfsService + "/wfs?service=wfs&version=2.0&request=GetFeature&typeNames=" + vm.env.bushfireLayer + cql_filter,
                    where:"report_status>1",
                }
            },{
                layer:"initial_bushfire_fireboundary",
                sourcelayers:{
                    url:vm.env.wfsService + "/wfs?service=wfs&version=2.0&request=GetFeature&typeNames=" + vm.env.fireBoundaryLayer + cql_filter,
                    where:"report_status=1",
                }
            },{
                layer:"final_bushfire_fireboundary",
                sourcelayers:{
                    url:vm.env.wfsService + "/wfs?service=wfs&version=2.0&request=GetFeature&typeNames=" + vm.env.fireBoundaryLayer + cql_filter,
                    where:"report_status>1",
                }
            }]
        }
        if (newBushfiresPoint.length > 0 ) {
            options["newBushfiresOriginPoint"] = this.$root.geojson.writeFeatures(newBushfiresPoint)
            options["layers"].push({
                layer:"new_bushfire_point",
                sourcelayers:{
                    parameter:"newBushfiresOriginPoint",
                    srs:"EPSG:4326"
                }
            })
        }
        if (newBushfiresBoundary.length > 0 ) {
            options["newBushfiresFireBoundary"] = this.$root.geojson.writeFeatures(newBushfiresBoundary)
            options["layers"].push({
                layer:"new_bushfire_fireboundary",
                sourcelayers:{
                    parameter:"newBushfiresFireBoundary",
                    srs:"EPSG:4326"
                }
            })
        }
        this.$root.export.downloadVector(fmt,options)
      },
      uploadBushfire:function(targetFeature) {
        this._uploadTargetFeature = targetFeature
        this._uploadType = "fireboundary"
        this._uploadTargetOnly = true
        $("#uploadBushfires").click()
      },
      importList: function () {
        var files = this.$els.bushfiresfile.files
        if (files.length === 0) {
            return
        }
        var targetFeature = this._uploadTargetFeature
        delete this._uploadTargetFeature

        var uploadType = this._uploadType
        delete this._uploadType

        var targetOnly = (targetFeature && this._uploadTargetOnly)?true:false
        delete this._uploadTargetOnly

        var import_task = null
        if (targetFeature) {
            if (!this._taskManager.initTasks(targetFeature)) {
                return
            }
            import_task = this._taskManager.addTask(targetFeature,"import","import","Import bushfire fire boundary",utils.RUNNING)
        }
        var vm = this
        this.export.importVector(files[0],function(features,fileFormat){
          try{
            var ignoredFeatures = []
            var f = null
            //initialize the loaded features
            if (fileFormat === "gpx") {
                //gpx file
                if (uploadType === "originpoint") {
                    features.length = 0
                }
                for(var i = features.length - 1;i >= 0;i--) {
                    feature = features[i]
                    if (targetFeature) {
                        feature.set('fire_number',targetFeature.get('fire_number'),true)
                        feature.set('id',targetFeature.get('id'),true)
                    }
                    if (uploadType === "originpoint") {
                        features.splice(i,1)
                        continue
                    }
                    if (feature.getGeometry() instanceof ol.geom.Point) {
                        //feature.set('toolName','Spot Fire')
                        ignoredFeatures.push(feature)
                        features.splice(i,1)
                    } else if(feature.getGeometry() instanceof ol.geom.LineString) {
                        var coordinates = feature.getGeometry().getCoordinates()
                        coordinates.push(coordinates[0])
                        feature.setGeometry(new ol.geom.Polygon([coordinates]))
                    } else if(feature.getGeometry() instanceof ol.geom.MultiLineString) {
                        var geom = feature.getGeometry()
                        var coordinates = null
                        var mp = new ol.geom.MultiPolygon()
                        $.each(geom.getLineStrings(),function(index,linestring) {
                            coordinates = linestring.getCoordinates()
                            coordinates.push(coordinates[0])
                            mp.appendPolygon(new ol.geom.Polygon([coordinates]))
                        })
                        feature.setGeometry(mp)
                    } else {
                        ignoredFeatures.push(feature)
                        features.splice(i,1)
                    }
                }
            } else {
                //geo json file
                //try to figure out the property name of 'fire_number' in imported files
                var fire_number_property = null
                for(var i = "fire_number".length;i >= 8;i--) {
                    var name = "fire_number".substring(0,i)
                    for (var j = 0;j < features.length;j++) {
                        if (features[j].get(name) !== undefined) {
                            fire_number_property = name
                            break
                        }
                    }
                    if (fire_number_property) {
                        break
                    }
                }
                fire_number_property = fire_number_property || "fire_number"
                if (fire_number_property !== "fire_number") {
                    //for some reason, the name of fire_number property is not 'fire_number', change the name of fire_number property to 'fire_number'
                    //for example, in shape file, the name of fire_number property is 'fire_numbe' because of the property length limit
                    for (var j = 0;j < features.length;j++) {
                        if (features[j].get(fire_number_property) !== undefined) {
                            features[j].set('fire_number',features[j].get(fire_number_property),true)
                            features[j].unset(fire_number_property)
                        }
                    }
                }

                for(var i = features.length - 1;i >= 0;i--) {
                    feature = features[i]
                    if (targetFeature && (feature.get('fire_number') === undefined || feature.get('fire_number') === null)) {
                        feature.set('fire_number',targetFeature.get('fire_number'),true)
                        feature.set('id',targetFeature.get('id'),true)
                    }
                    if (targetOnly && feature.get('fire_number') !== targetFeature.get('fire_number')) { 
                        //not target feature, ignore
                        features.splice(i,1)
                        continue
                    } 
                    if (feature.getGeometry() instanceof ol.geom.Point) {
                        if (uploadType === "fireboundary") {
                            features.splice(i,1)
                        }
                        continue
                    } else if (feature.getGeometry() instanceof ol.geom.Polygon) {
                        if (uploadType === "originpoint") {
                            features.splice(i,1)
                        }
                        continue
                    } else if (feature.getGeometry() instanceof ol.geom.MultiPolygon) {
                        if (uploadType === "originpoint") {
                            features.splice(i,1)
                        }
                        continue
                    } else if (feature.getGeometry() instanceof ol.geom.GeometryCollection) {
                        //remove the MultiPoint feature
                        features.splice(i,1)
                        //split the gemoetry collection into mutiple features
                        var geometries = null
                        geometries = feature.getGeometry().getGeometries()
                                    
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
            if (ignoredFeatures.length) {
                //console.warn("The following features are ignored.\r\n" + vm.$root.geojson.writeFeatures(features))
            }
            if (features && features.length == 0) {
                if (targetFeature) {
                    import_task.setStatus(utils.SUCCEED,"No features")
                    vm._taskManager.clearTasks(targetFeature)
                }
            } else {
                //Combine multile features of bushfire into one feature.
                features.sort(function(f1,f2){
                    var id1 = f1.get('fire_number')
                    var id2 = f2.get('fire_number')
                    if (id1) {
                        if (id2) {
                            return (id1 === id2)?0:(id1 < id2 ?-1:1)
                        } else {
                            return 1
                        }
                    } else if(id2) {
                        reurn -1
                    } else {
                        return 0
                    }
                })

                var feat = null
                for(var i = features.length - 1;i >= 0;i--) {
                    if (feat &&
                        (
                            feat.get('fire_number') === features[i].get('fire_number') && features[i].get('fire_number') !== undefined && features[i].get('fire_number') !== null
                        )
                    ) {
                        if (features[i].getGeometry() instanceof ol.geom.Point) {
                            if (feat.getGeometry() instanceof ol.geom.MultiPolygon) {
                                feat.setGeometry(new ol.geom.GeometryCollection([features[i].getGeometry(),feat.getGeometry()]))
                                features.splice(i,1)
                            } else {
                                //already have a point, ignore the point
                                features.splice(i,1)
                            }
                        } else if (features[i].getGeometry() instanceof ol.geom.Polygon) {
                            if (feat.getGeometry() instanceof ol.geom.MultiPolygon) {
                                feat.getGeometry().appendPolygon(features[i].getGeometry())
                                features.splice(i,1)
                            } else if (feat.getGeometry() instanceof ol.geom.Point) {
                                feat.setGeometry(new ol.geom.GeometryCollection([feat.getGeometry(),new ol.geom.MultiPolygon([features[i].getGeometry().getCoordinates()])]))
                                features.splice(i,1)
                            } else if (feat.getGeometry() instanceof ol.geom.GeometryCollection) {
                                feat.getGeometry().getGeometriesArray()[1].appendPolygon(features[i].getGeometry())
                                features.splice(i,1)
                            }
                        } else if (features[i].getGeometry() instanceof ol.geom.MultiPolygon) {
                            if (feat.getGeometry() instanceof ol.geom.MultiPolygon) {
                                $.each(features[i].getGeometry().getPolygons(),function(index,p) {
                                    feat.getGeometry().appendPolygon(p)
                                })
                                features.splice(i,1)
                            } else if (feat.getGeometry() instanceof ol.geom.Point) {
                                feat.setGeometry(new ol.geom.GeometryCollection([feat.getGeometry(),features[i].getGeometry()]))
                                features.splice(i,1)
                            } else if (feat.getGeometry() instanceof ol.geom.GeometryCollection) {
                                $.each(features[i].getGeometry().getPolygons(),function(index,p) {
                                    feat.getGeometry().appendPolygon(p)
                                    feat.getGeometry().getGeometriesArray()[1].appendPolygon(p)
                                })
                                features.splice(i,1)
                            }
                        }
                    } else {
                        feat = features[i]
                        if (feat.getGeometry() instanceof ol.geom.Polygon) {
                            feat.setGeometry(new ol.geom.MultiPolygon([feat.getGeometry().getCoordinates()]))
                        }
                    }
                    
                }
                
                //after merged, loaded feature can have geometryCollection,  point or multipolygon
                //update existing bushfires

                var canUpload = function(uploadedFeature,feature) {
                    if (feature && !vm.isFireboundaryDrawable(feature)) {
                        return
                    }
                    var uploadedFireboundary = null
                    if(uploadedFeature.getGeometry() instanceof ol.geom.GeometryCollection) {
                        uploadedFireboundary = uploadedFeature.getGeometry().getGeometriesArray()[1]
                    } else if(uploadedFeature.getGeometry() instanceof ol.geom.MultiPolygon) {
                        uploadedFireboundary = uploadedFeature.getGeometry()
                    } 
                    if (!uploadedFireboundary) {
                        return
                    }
                    uploadedFireboundary = uploadedFireboundary.getCoordinates()
                    var points = 0
                    for (var pIndex = 0;pIndex < uploadedFireboundary.length;pIndex++) {
                        for(var rIndex = 0;rIndex < uploadedFireboundary[pIndex].length;rIndex++) {
                            points += uploadedFireboundary[pIndex][rIndex].length
                        }
                    }
                    if (points > 5000) {
                        if (feature) {
                            throw "The maximum number of vertex points for uploading a initial bushfire's fireboundary is 5000."
                        } else {
                            throw "The maximum number of vertex points for uploading a new bushfire's fireboundary is 5000."
                        }
                    }
                }

                vm.selectedFeatures.clear()
                //var notFoundBushfires = null
                //var noPermissionBushfires = null
                var geometries = null
                $.each(features,function(index,feature){
                    if (feature.get('fire_number') !== undefined) {
                        //existed bushfire report
                        var feat = vm.allFeatures.getArray().find(function(f) {return f.get('fire_number') === feature.get('fire_number')})
                        canUpload(feature,feat)
                        if (feat) {
                            if (!vm.isModifiable(feat)) {
                                return
                            }
                            changed = false
                            geometries = feat.getGeometry().getGeometriesArray()
                            featurePoint = geometries.find(function(g){return g instanceof ol.geom.Point}) || null
                            if (vm.isFireboundaryDrawable(feat)) {
                                featureFireboundary = geometries.find(function(g){return g instanceof ol.geom.MultiPolygon}) || null
                            } else {
                                featureFireboundary = feat.get('fire_boundary')
                            }
                            var uploadedPoint = null
                            var uploadedFireboundary = null
                            if (feature.getGeometry() instanceof ol.geom.Point) {
                                uploadedPoint = feature.getGeometry()
                            } else if(feature.getGeometry() instanceof ol.geom.GeometryCollection) {
                                uploadedPoint = feature.getGeometry().getGeometriesArray()[0]
                                uploadedFireboundary = feature.getGeometry().getGeometriesArray()[1]
                            } else if(feature.getGeometry() instanceof ol.geom.MultiPolygon) {
                                uploadedFireboundary = feature.getGeometry()
                            } 
                            var modifyType = 0
                            if (uploadedPoint && !vm.map.isGeometryEqual(uploadedPoint,featurePoint,0.000000005)) {
                                modifyType = modifyType | 1
                            }
                            if (uploadedFireboundary && (!vm.isFireboundaryDrawable(feat) || !vm.map.isGeometryEqual(uploadedFireboundary,featureFireboundary,0.000000005))) {
                                modifyType = modifyType | 2
                            }

                            if (!vm.isFireboundaryDrawable(feat) && (modifyType & 2) === 2) {
                                //save to the database directly
                                feature.set('id',feat.get('id'),true)
                                feature.set('status',feat.get('status'),true)
                                feature.set('report_status',feat.get('report_status'),true)
                                feature.set('fire_number',feat.get('fire_number'),true)
                                feature.set('modifyType',modifyType | (feat.get('modifyType') || 0),true)
                                feature.set('tint','modified',true)
                                feature.set('fire_boundary',uploadedFireboundary.getExtent(),true)
                                feature.set('external_feature',true)
                                newGeometries = []
                                if ((modifyType & 1) === 1) {
                                    //both fireboundary and origin point are changed
                                    feature.setGeometry(new ol.geom.GeometryCollection([uploadedPoint,uploadedFireboundary]))
                                } else if (featurePoint) {
                                    //only fire boundary is changed, feature already has a valid origin point
                                    feature.setGeometry(new ol.geom.GeometryCollection([featurePoint,uploadedFireboundary]))
                                } else {
                                    //only fire boundary is changed, feature does not have a valid origin point
                                    feature.setGeometry(new ol.geom.GeometryCollection([uploadedFireboundary]))
                                }
                                if (!targetFeature && !vm._taskManager.initTasks(feat)) {
                                    return
                                }
                                feature.tasks = feat.tasks
                                vm.saveFeature(feature,function(f){
                                    vm.resetFeature(feat)
                                    vm.refreshWMSLayer()
                                    if (vm.selectedBushfires.indexOf(f.get('fire_number')) >= 0) { 
                                        vm.refreshSelectedWMSLayer()
                                    }
                                    if (import_task) {
                                        import_task.setStatus(utils.SUCCEED)
                                        vm._taskManager.clearTasks(feat)
                                    }
                                },function(){
                                    if (import_task) {
                                        import_task.setStatus(utils.FAILED)
                                    }
                                })
                            } else {
                                if ((modifyType & 1) === 1) {
                                    if (featurePoint) {
                                        geometries[0] = uploadedPoint
                                    } else {
                                        geometries.splice(0,0,uploadedPoint)
                                    }
                                }
                                if ((modifyType & 2) === 2) {
                                    if (featureFireboundary){
                                        geometries[1] = uploadedFireboundary
                                    } else {
                                        geometries.push(uploadedFireboundary)
                                    }
                                }
                                if (modifyType > 0) {
                                    feat.getGeometry().setGeometriesArray(geometries)
                                    vm.selectedFeatures.push(feat)
                                    vm.postModified(feat,modifyType)
                                }
                                if (import_task) {
                                    import_task.setStatus(utils.SUCCEED)
                                    vm._taskManager.clearTasks(feat)
                                }
                            }
                        } else if(feature.get('id') < 0 && feature.get('id').toString() === feature.get('fire_number') && vm.isCreatable()) {
                            //new feature,
                            if (feature.getGeometry() instanceof ol.geom.Point || feature.getGeometry() instanceof ol.geom.MultiPolygon) {
                                feature.setGeometry(new ol.geom.GeometryCollection([feature.getGeometry()]))
                            }
                            vm.newFeature(feature)
                            vm.measure.remeasureFeature(feature)
                            vm.selectedFeatures.push(feature)
                        } else {
                            //notFoundBushfires = notFoundBushfires || []
                            //notFoundBushfires.push(feature)
                        }
                    }
                }) 
                //add non existing bushfires
                $.each(features,function(index,feature){
                    if (feature.get('fire_number') === undefined) {
                        if (vm.isCreatable()) {
                            //non existed bushfire report
                            canUpload(feature,null)
                            if (feature.getGeometry() instanceof ol.geom.Point || feature.getGeometry() instanceof ol.geom.MultiPolygon) {
                                feature.setGeometry(new ol.geom.GeometryCollection([feature.getGeometry()]))
                            }
                            vm.newFeature(feature)
                            vm.measure.remeasureFeature(feature)
                            if (vm.selectedFeatures.getLength() < 10) {
                                vm.selectedFeatures.push(feature)
                            }
                        }
                    }
                }) 
                if (vm.selectedFeatures.getLength() > 0) {
                    vm.annotations.setTool("Bfrs Select")
                    //vm.zoomToSelected()
                }

                if (import_task && vm._taskManager.getTasks(targetFeature).length === 1) {
                    import_task.setStatus(utils.SUCCEED)
                    vm._taskManager.clearTasks(feat)
                }
                /*
                if (notFoundBushfires) {
                    alert("Some bushfires are not found." + JSON.stringify(notFoundBushfires.map(function(o) {return {id:o.get('id'),name:o.get('name')}})))
                }
                */
            }
          }catch(ex) {
            if (import_task) {
                import_task.setStatus(utils.FAILED,ex.message || ex)
            }
            if (targetFeature) {
                vm._taskManager.clearTasks(targetFeature)
            }
            alert(ex.message || ex)
          }
        },
        function(ex) {
            if (ex !== "Cancelled") {
                alert(ex)
            }
            if (import_task) {
                import_task.setStatus(utils.FAILED,ex.message || ex)
            }
            if (targetFeature) {
                vm._taskManager.clearTasks(targetFeature)
            }
        })
      },
      updateCQLFilter: function (updateType,wait,callback) {
        var vm = this
        if (updateType === "region") {
            this.district = ""
        }
        if (!vm._updateCQLFilterFunc) {
            vm._updateCQLFilterFunc = function(updateType,callback){
                if (!vm.bushfireMapLayer) {
                    vm._updateCQLFilter.call({wait:100},updateType)
                    return
                }
                if (vm.selectedOnly && !vm.selectedOnlyDisabled && vm.selectedBushfires.length === 0) {
                    vm.selectedOnly = false
                }
                // filter by specific bushfires if "Show selected only" is enabled
                if (vm.selectedOnly && !vm.selectedOnlyDisabled) {
                    vm.bushfireFilter = 'fire_number in (\'' + vm.selectedBushfires.join('\',\'') + '\')'
                } else if (vm.selectedOnly) {
                    vm.bushfireFilter = vm.bushfireFilter || ''
                } else {
                    vm.bushfireFilter = ''
                }
                // CQL statement assembling logic
                var filters = [vm.statusFilter, vm.bushfireFilter, vm.regionFilter, vm.districtFilter].filter(function(f){return (f || false) && true})
                if (filters.length === 0) {
                  vm.bushfireLayer.cql_filter = ''
                } else if (filters.length === 1) {
                  vm.bushfireLayer.cql_filter = filters[0]
                } else {
                  vm.bushfireLayer.cql_filter = "(" + filters.join(") and (") + ")"
                }
                if (updateType === "selectedBushfire" && vm.bushfireFilter) {
                    //chosed some bushfires
                    var filteredFeatures = vm.bushfireMapLayer.getSource().getFeatures().filter(function(f){
                        return f.get('status') === "new" || vm.selectedBushfires.indexOf(f.get('fire_number')) >= 0
                    })
                    vm.bushfireMapLayer.getSource().clear()
                    vm.bushfireMapLayer.getSource().addFeatures(filteredFeatures)
                    $.each(filteredFeatures,function(index,feature){
                        if (vm.selectedBushfires.indexOf(feature.get('fire_number')) >= 0) {
                            vm.annotations.tintSelectedFeature(feature)
                        }
                    })
                    vm.updateFeatureFilter(true)
                    return
                }
                //clear bushfire filter or change other filter
                vm.bushfireMapLayer.getSource().loadSource("query",callback)
                if (updateType === "refresh") {
                    vm.refreshWMSLayer()
                    if (vm.selectedBushfires.length >= 0) { 
                        vm.refreshSelectedWMSLayer()
                    }
                }
            }
        }

        if (!vm._updateCQLFilter) {
            vm._updateCQLFilter = debounce(function(updateType,callback){
                vm._updateCQLFilterFunc(updateType,callback)
            },2000)
        }
        if (wait === 0) {
            vm._updateCQLFilterFunc(updateType,callback)
        } else if (wait === undefined || wait === null) {
            vm._updateCQLFilter(updateType,callback)
        } else {
            vm._updateCQLFilter.call({wait:wait},updateType,callback)
        }
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
        if (a.get('status') === "new") {
            if  (b.get('status') === 'new') {
                return a.get('label') < b.get('label')?-1:1
            } else {
                return -1
            }
        } else if(b.get('status') === 'new') {
            return 1
        } else {
            return a.get('label') < b.get('label')?-1:1
        }
      },
      updateFeatureFilter: function(runNow) {
        var vm = this
        var updateFeatureFilterFunc = function() {
            // syncing of Resource Tracking features between Vue state and OL source
            var mapLayer = vm.bushfireMapLayer
            if (!mapLayer) { return }
            // update vue list for filtered features in the current extent
            vm.extentFeatures = mapLayer.getSource().getFeaturesInExtent(vm.$root.map.extent).filter(vm.featureFilter)
            vm.extentFeatures.sort(vm.featureOrder)
            // update vue list for filtered features
            var allFeatures = mapLayer.getSource().getFeatures().filter(vm.featureFilter)
            allFeatures.sort(vm.featureOrder)
            vm.allFeatures.clear()
            vm.allFeatures.extend(allFeatures)
            //
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
            var mapLayer = vm.bushfireMapLayer
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
      selectDefaultGeometry:function(feature) {
        var geometries = feature.getGeometry().getGeometriesArray()
        if (geometries.length > 1) {
            if (geometries[1].getPolygons().length === 0){
                feature["selectedIndex"] = [0]
            } else {
                feature["selectedIndex"] = [1,0]
            }
        } else if (geometries.length === 0) {
            delete feature["selectedIndex"]
        } else if (geometries[0] instanceof ol.geom.Point){
            feature["selectedIndex"] = [0]
        } else if (geometries[0].getPolygons().length === 0){
            delete feature["selectedIndex"]
        } else {
            feature["selectedIndex"] = [0,0]
        }
      },
      loadUserProfile:function() {
        var vm = this
        vm._bfrsStatus.phaseBegin("load_profile",20,"Load profile")
        $.ajax({
            url: vm.env.bfrsService + "/api/v1/profile/?format=json",
            method:"GET",
            dataType:"json",
            success: function (response, stat, xhr) {
                vm.whoami["bushfire"]["profile"] = response
                vm.profileRevision += 1
                if (vm.whoami["bushfire"]["regions"]) {
                    vm.region = vm.whoami["bushfire"]["profile"]["region_id"] || ""
                    vm.district = vm.whoami["bushfire"]["profile"]["district_id"] || ""
                    vm._bfrsStatus.phaseBegin("load_bushfires",20,"Load bushfires",false,true)
                    vm.updateCQLFilter('district',0)
                    vm.bushfireLayer.initialLoad = true
                }
                vm._bfrsStatus.phaseEnd("load_profile")
            },
            error: function (xhr,status,message) {
                alert(status + " : " + (xhr.responseText || message))
                vm._bfrsStatus.phaseFailed("load_profile","Failed to loading user profile data. status = " + status + " , message = " + (xhr.responseText || message))
            },
            xhrFields: {
              withCredentials: true
            }
        })
      },
      loadRegions:function() {
        var vm = this
        vm._bfrsStatus.phaseBegin("load_regions",20,"Load regions")
        $.ajax({
            url: vm.env.bfrsService + "/api/v1/region/?format=json",
            method:"GET",
            dataType:"json",
            success: function (response, stat, xhr) {
                vm.whoami["bushfire"]["regions"] = response
                vm.profileRevision += 1
                if (vm.whoami["bushfire"]["profile"]) {
                    vm.region = vm.whoami["bushfire"]["profile"]["region_id"] || ""
                    vm.district = vm.whoami["bushfire"]["profile"]["district_id"] || ""
                    vm._bfrsStatus.phaseBegin("load_bushfires",20,"Load bushfires",false,true)
                    vm.updateCQLFilter('district',0)
                    vm.bushfireLayer.initialLoad = true
                }
                vm._bfrsStatus.phaseEnd("load_regions")
            },
            error: function (xhr,status,message) {
                alert(status + " : " + (xhr.responseText || message))
                vm._bfrsStatus.phaseFailed("load_regions","Failed to loading regions data. status = " + status + " , message = " + (xhr.responseText || message))
            },
            xhrFields: {
              withCredentials: true
            }
        })
      },

      setup: function() {
        var vm = this
        //restore the selected features
        this.annotations.restoreSelectedFeatures()

        // enable resource bfrs layer, if disabled
        if (!this.bushfireMapLayer) {
          this.catalogue.onLayerChange(this.bushfireLayer, true)
        } else if (this.active.isHidden(this.bushfireMapLayer)) {
            this.active.toggleHidden(this.bushfireMapLayer)
        }

        this.$root.annotations.selectable = [this.bushfireMapLayer]
        this.annotations.setTool()

        //add feature to place an point based on coordinate
        this.$root.search.setSearchPointFunc(function(searchMethod,coords,name){
            if (["DMS","MGA"].indexOf(searchMethod) < 0) {
                return false
            }
            if (vm.annotations.tool && vm.annotations.tool.name === "Bfrs Edit Geometry") {
                var feat = vm.selectedFeatures.getLength() === 1?vm.selectedFeatures.item(0):null
                if (!feat) {return false}
                if (!vm.isModifiable(feat)) {
                    alert("Can't modify " + feat.get('status') + " report")
                    return true
                }

                var hasPoint = feat.getGeometry().getGeometriesArray().length > 0 && feat.getGeometry().getGeometriesArray()[0] instanceof ol.geom.Point

                if (hasPoint) {
                    feat.getGeometry().getGeometriesArray()[0] = new ol.geom.Point(coords)
                } else {
                    feat.getGeometry().getGeometriesArray().splice(0,0,new ol.geom.Point(coords))
                }
                feat.getGeometry().setGeometriesArray(feat.getGeometry().getGeometriesArray())
                vm.postModified(feat,1)
                
                feat.getGeometry().changed()

                return true
            } else if (vm.annotations.tool && vm.annotations.tool.name === "Bfrs Origin Point") {
                var feat = vm.newFeature()
                feat.getGeometry().getGeometriesArray().splice(0,0,new ol.geom.Point(coords))
                feat.getGeometry().setGeometriesArray(feat.getGeometry().getGeometriesArray())
                feat.getGeometry().changed()
                vm.selectedFeatures.clear()
                vm.selectedFeatures.push(feat)
                vm.annotations.setTool("Bfrs Edit Geometry")
                vm.postModified(feat,1)
                return true
            }
        })

        this.$nextTick(this.adjustHeight)
      },
      tearDown:function() {
        this.selectable = null
      }
    },
    ready: function () {
      var vm = this
      this._taskManager = utils.getFeatureTaskManager(function(){
        vm.revision++
      })
      vm._bfrsStatus = this.loading.register("bfrs","Bush Fire Report Component")
      vm._bfrsStatus.phaseBegin("initialize",10,"Initialize")
      var map = this.$root.map

      vm._reportStatus = {
       99999: "unknown",
        1: "initial",
        2: "draft_final",
        3: "final_authorised",
        4: "reviewed"
      }
      
      vm.whoami["bushfire"] = vm.whoami["bushfire"] || {}
      vm.whoami["bushfire"]["permission"] = vm.whoami["bushfire"]["permission"] || {
          "create":null,
          "new.edit":false,
          "new.modify":true,
          "new.delete":true,
          "unknown.edit":false,
          "unknown.modify":false,
          "unknown.delete":false,
          "initial.edit":null,
          "initial.modify":null,
          "initial.delete":false,
          "draft_final.edit":null,
          "draft_final.modify":null,
          "draft_final.delete":false,
          "final_authorised.edit":null,
          "final_authorised.modify":null,
          "final_authorised.delete":false,
          "reviewed.edit":null,
          "reviewed.modify":null,
          "reviewed.delete":false,
          "_checked_":0
      }

      var permissionConfig = [
          ["create",vm.createUrl(),"GET",null,function(hasPermission){
             if (hasPermission) {
                 if (vm.tools && !vm.tools.find(function(t){return t === vm.ui.originPointTool})) {
                  vm.tools.push(vm.ui.originPointTool)
                 }
             }
          }],
          ["initial.edit",vm.saveUrl,"PATCH",function(f){return f.get('status') === "initial"},null],
          ["initial.modify",vm.saveUrl,"PATCH",function(f){return f.get('status') === "initial"},null],
          ["draft_final.edit",vm.saveUrl,"PATCH",function(f) {return f.get('status') === "draft_final"},null],
          ["draft_final.modify",vm.saveUrl,"PATCH",function(f) {return f.get('status') === "draft_final"},null],
          ["final_authorised.edit",vm.saveUrl,"PATCH",function(f) {return f.get('status') === "final_authorised"},null],
          ["final_authorised.modify",vm.saveUrl,"PATCH",function(f) {return f.get('status') === "final_authorised"},null],
          ["reviewed.edit",vm.saveUrl,"PATCH",function(f) {return f.get('status') === "reviewed"},null],
          ["reviewed.modify",vm.saveUrl,"PATCH",function(f) {return f.get('status') === "reviewed"},null],
      ]
      vm._checkPermission = function(features,callback){
          if (vm.whoami['bushfire']['permission']['_checked_'] === permissionConfig.length) {
              //All permission checks are done
              if (callback) callback()
              return
          }

          var taskCounter = 0

          vm._checkPermissionCallback = vm._checkPermissionCallback || function(callback) {
              if (vm.whoami['bushfire']["permission"]["changed"]) {
                  delete vm.whoami['bushfire']["permission"]["changed"]
                  vm.revision += 1
              }
              if (callback) callback()
          }

          taskCounter += 1
          for (var index = 0;index < permissionConfig.length;index++) {
              var p = permissionConfig[index]
              var url = null
              if (vm.whoami['bushfire']["permission"][p[0]] === null || vm.whoami['bushfire']["permission"][p[0]] === undefined){
                  if (p[1] === null) {
                      //always have the permission
                      vm.whoami['bushfire']["permission"][p[0]] = true
                      vm.whoami['bushfire']["permission"]["changed"] = true
                      vm.whoami['bushfire']['permission']['_checked_'] = vm.whoami['bushfire']['permission']['_checked_'] + 1
                  } else {
                      if (typeof p[1] === "string") {
                          //url is a constant string
                          url = p[1]
                      } else {
                          //url is a function with a bushfire argument.
                          var f = (Array.isArray(features))?features.find(p[3]):(p[3](features)?features:null)
                          if (f) {
                              //get the test url
                              url = p[1](f)
                          } else {
                              //can't find a bushfire to test
                              url = null
                              vm.whoami['bushfire']["permission"][p[0]] = null
                          }
                      }
                  }
              }
              if (url) {
                  taskCounter += 1
                  
                  vm.utils.checkPermission(url,p[2],function(hasPermission,permission){
                      vm.whoami['bushfire']['permission']['_checked_'] = vm.whoami['bushfire']['permission']['_checked_'] + 1
                      vm.whoami['bushfire']["permission"][permission[0]] = hasPermission
                      vm.whoami['bushfire']["permission"]["changed"] = true
                      if (permission[4]) {
                          permission[4](hasPermission)
                      }
                      if (--taskCounter <= 0) vm._checkPermissionCallback(callback)
                  },p)
              }
          }
          if (--taskCounter <= 0) vm._checkPermissionCallback(callback)
      }

      vm.loadRegions()

      vm.ui = {}
      var toolConfig = {features:vm.allFeatures,mapLayers:function(layer){return layer.get("id") === vm.env.bushfireLayer }}
      /*
      vm.ui.translateInter = vm.annotations.translateInterFactory()(toolConfig)
      vm.ui.translateInter.on("translateend",function(ev){
          vm.postModified(ev.features.getArray())
      })
      */
      vm.ui.dragSelectInter = vm.annotations.dragSelectInterFactory()(toolConfig)
      vm.ui.selectInter = vm.annotations.selectInterFactory()(toolConfig)
      vm.ui.geometrySelectInter = vm.annotations.selectInterFactory({
        condition: function(event) {
            var result = ol.events.condition.singleClick(event)
            if (result) {
                if (vm.bushfireMapLayer && vm.selectedFeatures.getLength() === 1) {
                    result = vm.bushfireMapLayer.getSource().getFeaturesAtCoordinate(event.coordinate).findIndex(function(o) {return o === vm.selectedFeatures.item(0)}) >= 0
                } else {
                    result = false
                }
            }
            return result
        }
      })($.extend({selectMode:"geometry"},toolConfig))

      vm.ui.modifyInter = vm.annotations.modifyInterFactory()({features:vm.selectedFeatures,mapLayers:function(layer){return layer.get("id") === vm.env.bushfireLayer }})
      vm.ui.modifyInter.on("featuresmodified",function(ev){
          if (ev.features.getLength() === 1 ) {
            vm.validateBushfire(ev.features.item(0),"modifyBushfire")
          }
          vm.postModified(ev.features.getArray(),-1)
      })    

      vm.ui.originPointDraw = vm.annotations.pointDrawFactory({
        events: {
            addfeaturegeometry:true
        },
        drawOptions:{
        }
      })({
        features:vm.drawings
      })

      var canDrawFireboundary = function(ev) {
        var feat = (vm.selectedFeatures.getLength() == 1)?vm.selectedFeatures.item(0):null
        if (feat) {
            var featGeometry = feat.getGeometry()
            if (vm.isModifiable(feat) && vm.isFireboundaryDrawable(feat)) {
                if (vm.bushfireMapLayer) {
                    return vm.bushfireMapLayer.getSource().getFeaturesAtCoordinate(ev.coordinate).findIndex(function(o) {return o === feat}) < 0
                } else {
                    return false
                }
            } else {
                return false
            }
        } else {
            //alert("Plase choose a bushfire to draw a fire boundary.")
            return false
        }
      }

      vm.ui.fireboundaryDraw = vm.annotations.polygonDrawFactory({
        events: {
            addfeaturegeometry:true
        },
        drawOptions:{
            freehandCondition:function(ev) {
                var result = ol.events.condition.shiftKeyOnly(ev)
                if (result) {
                    return canDrawFireboundary(ev)
                }
                return result
            },
            condition:function(ev) {
                var result = ol.events.condition.noModifierKeys(ev)
                if (result) {
                    return canDrawFireboundary(ev)
                }
                return result
            }
        }
      })({
        features:vm.drawings
      })
      vm.drawings.on("add",function(ev){
        if (vm.annotations.tool.name === "Bfrs Edit Geometry") {
            if (vm.selectedFeatures.getLength() === 1){
                var f = vm.selectedFeatures.item(0)
                var indexes = null

                var index = f.getGeometry().getGeometriesArray().findIndex(function(g){return g instanceof ol.geom.MultiPolygon})
                if (index >= 0) {
                    indexes = [index,f.getGeometry().getGeometriesArray()[index].getPolygons().length]
                    f.getGeometry().getGeometriesArray()[index].appendPolygon(ev.element.getGeometry())
                } else {
                    index = f.getGeometry().getGeometriesArray().length
                    indexes = [index,0]
                    f.getGeometry().getGeometriesArray().push(new ol.geom.MultiPolygon([ev.element.getGeometry().getCoordinates()]))
                }
                f.getGeometry().setGeometriesArray(f.getGeometry().getGeometriesArray())
                f.getGeometry().changed()
                vm.postModified(f,2)
                vm.validateBushfire(f,"addFireBoundary")

                vm.ui.fireboundaryDraw.dispatchEvent(vm.map.createEvent(vm.ui.fireboundaryDraw,"addfeaturegeometry",{feature:f,indexes:indexes}))
            }
        } else {
            f = vm.newFeature()
            f.getGeometry().getGeometriesArray().splice(0,0,ev.element.getGeometry())
            f.getGeometry().setGeometriesArray(f.getGeometry().getGeometriesArray())
            f.getGeometry().changed()
            vm.postModified(f,1)
            vm.selectedFeatures.clear()
            vm.selectedFeatures.push(f)
            vm.annotations.setTool("Bfrs Edit Geometry")
            //vm.validateBushfire(f,"addOriginPoint")

            vm.ui.originPointDraw.dispatchEvent(vm.map.createEvent(vm.ui.originPointDraw,"addfeaturegeometry",{feature:f,indexes:[0]}))
        }
        vm.drawings.clear()
      })

      //add tools
      var tools = [
          {
              name: 'Bfrs Select',
              label: 'Select',
              icon: 'fa-mouse-pointer',
              scope:["bfrs"],
              interactions: [
                  vm.ui.dragSelectInter,
                  vm.ui.selectInter,
                  //vm.ui.translateInter,
                  vm.annotations.keyboardInterFactory({
                    selectEnabled:false,
                    events: {
                        deletefeatureallgeometries:true
                    },
                    deleteSelected:function(features,selectedFeatures) {
                        var feature = null
                        for(i = selectedFeatures.getLength() - 1;i >= 0;i--) {
                            feature = selectedFeatures.item(i)
                            if (vm.isDeletable(feature)) {
                                vm.deleteFeature(feature)
                            } else {
                                alert("Can't delete a existing bushfire.")
                            }
                        }
                    }
                  }),
              ],
              keepSelection:true,
              onSet: function() {
                  vm.ui.dragSelectInter.setMulti(true)
                  vm.ui.selectInter.setMulti(true)
              },
              comments:[
                {
                    name:"Tips",
                    description:[
                        "Select bushfires using keyboard or mouse",
                    ]
                }
              ]
          },{
              name: 'Bfrs Edit Geometry',
              label: 'Edit Geometry',
              icon: 'fa-pencil',
              scope:[],
              interactions: [
                  vm.ui.geometrySelectInter,
                  vm.annotations.keyboardInterFactory({
                    selectEnabled:false,
                    events:{ 
                        deletefeaturegeometry:true
                    },
                    deleteSelected:function(features,selectedFeatures) {
                        selectedFeatures.forEach(function (feature) {
                            if (vm.isModifiable(feature) && feature["selectedIndex"] !== undefined) {
                                var geom = vm.annotations.getSelectedGeometry(feature)
                                if (geom instanceof ol.geom.Point) {
                                    if (feature.get('status') === "new") {
                                        vm.deleteFeature(feature)
                                    } else {
                                        alert("Can't delete existing bushfire's orgin point.")
                                    }
                                    return
                                }
                                vm.annotations.deleteSelectedGeometry(feature,this)
                                vm.selectDefaultGeometry(feature)
                                vm.postModified(feature,2)
                                vm.validateBushfire(feature,"deleteFireBoundary")
                            }
                        },this)
                    }
                  }),
                  vm.ui.modifyInter,
                  this.ui.fireboundaryDraw
              ],
              selectMode:"geometry",
              keepSelection:true,
              onSet: function() {
                  vm.ui.geometrySelectInter.setMulti(false)
                  if (vm.selectedFeatures.getLength() > 1) {
                      vm.selectedFeatures.clear()
                  } else if (vm.selectedFeatures.getLength() == 1) {
                    var selectedFeature = vm.selectedFeatures.item(0)
                    if (selectedFeature["selectedIndex"] === undefined ) {
                        vm.selectDefaultGeometry(selectedFeature)
                    } 
                    var currentScale = vm.map.getScale()
                 }
              },
              comments:[
                {
                    name:"Tips",
                    description:[
                        "Click in a fire boundary of the selected initial bushfire to select a fire boundary.",
                        "Press 'Del' to delete a selected fire boundary of the selected initial bushfire.",
                        "Click outside of the selected initial bushfire's fire boundary to draw a new fire boundary.",
                        "Hold down the 'SHIFT' key during drawing to enable freehand mode."
                    ]
                }
              ]
          },{
              name: 'Bfrs Origin Point',
              label: 'Add Bushfire',
              icon: 'dist/static/symbols/fire/origin.svg',
              tints: vm.tints,
              selectedFillColour:[0, 0, 0, 0.25],
              fillColour:[0, 0, 0, 0.25],
              size:2,
              interactions: [
                  vm.ui.originPointDraw
              ],
              sketchStyle: vm.annotations.getIconStyleFunction(vm.tints),
              features:vm.allFeatures,
              scope:[],
              measureLength:true,
              measureArea:true,
              keepSelection:true,
              showName: true,
              getMeasureGeometry:function() {
                if (vm.isFireboundaryDrawable(this)) {
                    return this.getGeometry()
                } else {
                    return null
                }
              },
              onSet: function() {
                  /*
                  if (vm.selectedFeatures.getLength() > 1) {
                      vm.selectedFeatures.clear()
                  } else {
                      var currentScale = vm.map.getScale()
                  }
                  */
              },
              comments:[
                {
                    name:"Tips",
                    description:[
                        "Click on the map or search a point to create a new bushfire in SSS."
                    ]
                }
              ]
          }
      ]

      tools.forEach(function (tool) {
        vm.annotations.tools.push(tool)
      })

      vm.ui.modifyTool = vm.annotations.tools.find(function(tool){return tool.name === "Bfrs Edit Geometry"})
      vm.ui.originPointTool = vm.annotations.tools.find(function(tool){return tool.name === "Bfrs Origin Point"})
      vm.ui.panTool = vm.annotations.tools.find(function(tool){return tool.name === "Pan"})
      vm.ui.selectTool = vm.annotations.tools.find(function(tool){return tool.name === "Bfrs Select"})

      this.$root.fixedLayers.push({
        type: 'WFSLayer',
        name: 'Bush Fire Report',
        id: vm.env.bushfireLayer,
        getFeatureInfo:function (f) {
            return {name:f.get("fire_number"), img:map.getBlob(f, ['icon', 'tint']), comments:f.get('name') + "(" + f.get('status')  + ")"}
        },
        initialLoad:false,
        refresh: 60,
        dependentLayers:[
            {
                type: 'TileLayer',
                name: 'Fire Boundary of Bush Fire Final Report',
                id: vm.env.finalFireBoundaryLayer,
                refresh: 60
            },
            {
                type: 'ImageLayer',
                name: 'Fire Boundary of Selected Bush Fire Final Report',
                id: vm.env.finalFireBoundaryLayer,
                style: vm.env.finalFireBoundaryLayer + ".selected",
                mapLayerId:vm.env.finalFireBoundaryLayer + "_selected",
                autoAdd:false,
                refresh: 60,
                autoAdd:false
            }
        ],
        /*
        getUpdatedTime:function(features) {
            var updatedTime = null
            $.each(features,function(index,f){
                if (f.get('status') !== 'new') {
                    var featureModifiedDate = moment(new Date(f.get('modified')))
                    if (updatedTime === null) {
                        updatedTime =  featureModifiedDate
                    } else if(updatedTime < featureModifiedDate) {
                        updatedTime =  featureModifiedDate
                    }
                }
            })
            return updatedTime
        },
        */
        onerror:function(status,message) {
            vm._bfrsStatus.phaseFailed("load_bushfires",status + " : " + message)
        },
        onload: function(loadType,vectorSource,features,defaultOnload) {
            //combine the two spatial columns into one
            $.each(features,function(index,feature){
                vm.initBushfire(feature)
            })
            function processResources() {
                //merge the current changes with the new features
                var insertPosition = 0
                var loadedFeature = null
                for(var index = vm.allFeatures.getLength() - 1;index >= 0;index--) {
                    f = vm.allFeatures.item(index)
                    if (f.get('status') === 'new') {
                        //new features always are the begining and sorted.
                        if (f.get('saved')) {
                            //save before
                            loadedFeature = features.find(function(f2){
                                var geometries = f2.getGeometry().getGeometriesArray()
                                var originPoint = (geometries.length > 0 && geometries[0] instanceof ol.geom.Point)?geometries[0]:null
                           
                                return originPoint?vm.map.isGeometryEqual(new ol.geom.Point(f.get('sss_id')),originPoint,0.000000005):false
                            })
                            if (!loadedFeature) {
                                //still not save, keep the current new bushfire
                                features.splice(insertPosition,0,f)
                                insertPosition += 1
                            } else{
                                if (f.get('tint') === 'modified'){
                                    //feature was changed after saving
                                    //replace the loadedFeature's geometry with the modified version
                                    loadedFeature.setGeometry(f.getGeometry())
                                    loadedFeature.set('tint','modified',true)
                                    loadedFeature.set('fillColour',vm.tints[loadedFeature.get('tint') + ".fillColour"],true)
                                    loadedFeature.set('colour',vm.tints[loadedFeature.get('tint') + ".colour"],true)
                                    loadedFeature.set('modifyType',f.get('modifyType'),true)
                                } else {
                                    //already saved into the database, and not change after saving, ignore it
                                }
                                if (f.tasks) {
                                    loadedFeature.tasks = f.tasks
                                }
                                var i = vm.selectedFeatures.getArray().findIndex(function(o) {return o.get('fire_number') === f.get('fire_number')})
                                if (i >= 0) {
                                    vm.selectedFeatures.removeAt(i)
                                    vm.selectedFeatures.push(loadedFeature)
                                }
                            }
                        } else {
                            //not save before
                            features.splice(insertPosition,0,f)
                            insertPosition += 1
                        }
                    } else if (f.get('tint') === 'modified' || f.tasks) {
                        loadedFeature = features.find(function(f2){return f.get('id') === f2.get('id')})
                        if (loadedFeature) {
                            if (f.get('tint') === 'modified') {
                                //replace the loadedFeature's geometry with the modified version
                                loadedFeature.setGeometry(f.getGeometry())
                                loadedFeature.set('tint','modified',true)
                                loadedFeature.set('fillColour',vm.tints[loadedFeature.get('tint') + ".fillColour"],true)
                                loadedFeature.set('colour',vm.tints[loadedFeature.get('tint') + ".colour"],true)
                                loadedFeature.set('modifyType',f.get('modifyType'),true)
                            } 
                            if (f.tasks) {
                                loadedFeature.tasks = f.tasks
                            }
                        }
                    }
                }
                if (vm.annotations.isSelectedFeaturesOfModule("bfrs") && vm.selectedFeatures.getLength() > 0) {
                    for(var index = vm.selectedFeatures.getLength() - 1;index >= 0;index--) {
                        var f = vm.selectedFeatures.item(index)
                        loadedFeature = features.find(function(f1){return f1.get('fire_number') === f.get('fire_number')})
                        if (loadedFeature) {
                            if (f.selectedIndex !== undefined) {
                                if (vm.annotations.getSelectedGeometry(loadedFeature,f.selectedIndex)) {
                                    loadedFeature.selectedIndex = f.selectedIndex
                                } else {
                                    vm.selectDefaultGeometry(loadedFeature)
                                }
                            }
                            vm.selectedFeatures.setAt(index,loadedFeature)
                        } else {
                            vm.selectedFeatures.removeAt(index)
                        }
                    }
                }
                defaultOnload(loadType,vectorSource,features)

                vm.updateFeatureFilter(true)

                if (vm.whoami['bushfire']["permission"]["changed"]) {
                    delete vm.whoami['bushfire']["permission"]["changed"]
                    vm.revision += 1
                }
                vm._bfrsStatus.phaseEnd("load_bushfires")
            }
            vm._checkPermission(features,processResources)
        }
      })

      this.measure.register(vm.env.bushfireLayer,this.allFeatures)
      vm._bfrsStatus.phaseEnd("initialize")

      vm._bfrsStatus.phaseBegin("gk-init",20,"Listen 'gk-init' event",true,true)
      // post init event hookup
      this.$on('gk-init', function () {
        vm._bfrsStatus.phaseEnd("gk-init")

        vm._bfrsStatus.phaseBegin("attach_event",10,"Attach events")
        map.olmap.getView().on('propertychange', vm.updateViewport)

        vm.selectedFeatures.on('add', function (event) {
          if (event.element.get('toolName') === "Bfrs Origin Point") {
            vm.selectedBushfires.push(event.element.get('fire_number'))
            if (vm.annotations.tool.selectMode === "geometry") {
                if (event.element["selectedIndex"] === undefined) {
                    vm.selectDefaultGeometry(event.element)
                }
            }
            vm.refreshSelectedWMSLayer()
            if (vm.selectedOnly && !vm.selectedOnlyDisabled) {  
                vm.updateCQLFilter('selectedBushfire',1000)
            }
            //vm.zoomToSelected(200)
          }
        })
        vm.selectedFeatures.on('remove', function (event) {
          if (event.element.get('toolName') === "Bfrs Origin Point") {
            vm.selectedBushfires.$remove(event.element.get('fire_number'))
            vm.refreshSelectedWMSLayer()
            //vm.zoomToSelected(200)
            if (vm.selectedOnly && !vm.selectedOnlyDisabled) {  
                vm.updateCQLFilter('selectedBushfire',1000)
            }

          }
          //remove the index of the selected geometry in geometry collection
          //delete event.element['selectedIndex']
        })
        // enable resource bfrs layer, if disabled
        //vm.annotations.setDefaultTool('bfrs','Pan')
        $.each(vm.annotations.tools.filter(function (t) {
          return t.scope && t.scope.indexOf("bfrs") >= 0
        }),function(index,t){
            vm.tools.splice(index,0,t)
        })


        vm.map.olmap.on("removeLayer",function(ev){
            if (ev.mapLayer.get('id') === vm.env.bushfireLayer) {
                vm.allFeatures.clear()
                vm.extentFeatures = []
            }
        })

        vm._resolutionChanged = debounce(function(ev){
            vm.bushfireLabelsDisabled = (vm.map.olmap.getView().getResolution() > 0.003)
        },200)

        vm._resolutionChanged()

        vm.map.olmap.getView().on("change:resolution",function(){
            vm._resolutionChanged()
        })

        vm._bfrsStatus.phaseEnd("attach_event")
        //load user profile
        vm.loadUserProfile()

      })
    }
  }
</script>
