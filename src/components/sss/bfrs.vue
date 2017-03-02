<template>
  <div class="tabs-panel" id="menu-tab-bfrs">
    <div class="row collapse">
      <div class="columns">
        <ul class="tabs" id="bfrs-tabs">
          <li class="tabs-title is-active">
            <a class="label" aria-selected="true">Bush Fire Report
              <small v-if="active.layerRefreshStatus(bfrsMapLayer)" style="white-space:pre-wrap"><br>Updated: {{ active.layerRefreshStatus(bfrsMapLayer) }}</small>
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
                    <a class="expanded secondary button" v-bind:class="{'selected': t.name == annotations.tool.name}" @click="annotations.setTool(t)"
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
                <input class="switch-input" id="toggleBushfireLabels" type="checkbox" v-bind:checked="bushfireLabels" @change="toggleBushfireLabels" />
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

            <div class="row collapse">
              <div class="small-6 columns">
                <select name="select" v-model="region" @change="updateCQLFilter('region')">
                  <option value="" selected>All regions</option> 
                  <option v-for="r in regions"  value="{{r.region_id}}" track-by="region_id">
                    {{r.region}}
                  </option>
                </select>
              </div>
              <div class="small-6 columns">
                <select name="select" v-model="district" @change="updateCQLFilter('district')">
                  <option value="" selected>All districts</option> 
                  <option v-for="d in districts"  value="{{d.id}}" track-by="id">
                    {{d.district}}
                  </option>
                </select>
              </div>
            </div>

            <div class="row collapse">
              <div class="small-6 columns">
                <select name="select" v-model="statusFilter" @change="updateCQLFilter('bushfireStatus')">
                  <option value="" selected>All bushfires</option> 
                  <option value="init_authorised_by_id is null">Initial Bushfires</option>
                  <option value="init_authorised_by_id is not null AND authorised_by_id is null">Final Bushfires</option>
                  <option value="authorised_by_id is not null">Final Authroized Bushfires</option>
                </select>
              </div>
              <div class="small-6 columns">
                <input type="search" v-model="search" placeholder="Find a bushfire" @keyup="updateFeatureFilter">
              </div>
            </div>

            <div class="row">
              <div class="small-6">
                <div class="columns">
                  <div class="row">
                    <div class="switch tiny">
                      <input class="switch-input" id="selectedBushfiresOnly" type="checkbox" v-model="selectedOnly" @change="updateCQLFilter('selectedBushfire')" />
                      <label class="switch-paddle" for="selectedBushfiresOnly">
                        <span class="show-for-sr">Show selected only</span>
                     </label>
                    </div>
                    <label for="selectedBushfiresOnly" style="margin-left:3px" class="side-label">Show selected only</label>
                  </div>
                </div>
              </div>
              <div class="small-6">
                <a title="Zoom to selected" class="button" @click="map.zoomToSelected()" ><i class="fa fa-search"></i></a>
                <a v-if="isCreatable()" title="Create bushfire" class="button" @click="newFeature()" ><i class="fa fa-plus"></i></a>
                <a title="Download list as geoJSON" class="button" @click="downloadList()" ><i class="fa fa-download"></i></a>
                <label class="button" style="line-height:1;font-size:0.9rem;" for="uploadBushfires" title="Support GeoJSON(.geojson .json), GPS data(.gpx)"><i class="fa fa-upload"></i></label><input type="file" id="uploadBushfires" class="show-for-sr" name="bushfiresfile" accept=".json,.geojson,.gpx" v-model="bushfiresfile" v-el:bushfiresfile @change="importList()"/>
                <!--a title="Download all or selected as CSV" class="button" href="{{bfrsService}}/bushfire.csv?{{downloadSelectedCSV()}}" target="_blank" ><i class="fa fa-table"></i></a-->
              </div>
            </div>
            </div>


            <div id="bfrs-list" class="layers-flexibleframe scroller" style="margin-left:-15px; margin-right:-15px;">
              <div v-for="f in features" class="row feature-row" v-bind:class="{'feature-selected': selected(f) }"
                @click="toggleSelect(f)" track-by="get('id')">
                <div class="columns">
                  <a v-if="canReset(f)"  @click.stop.prevent="resetFeature(f)" title="Reset" class="button tiny secondary float-right acion" style="margin-left:2px"><i class="fa fa-undo actionicon"></i></a>
                  <a v-if="canDelete(f)" @click.stop.prevent="deleteFeature(f)" title="Delete" class="button tiny secondary float-right action" style="margin-left:2px"><i class="fa fa-trash actionicon"></i></a>
                  <a v-if="canCreate(f)" @click.stop.prevent="createFeature(f)" title="Create" class="button tiny secondary float-right action" style="margin-left:2px"><i class="fa fa-save actionicon"></i></a>
                  <a v-if="canEdit(f) " @click.stop.prevent="map.editResource($event)" title="Edit" href="{{editUrl(f)}}" target="_blank" class="button tiny secondary float-right action" style="margin-left:2px"><i class="fa fa-pencil actionicon"></i></a>
                  <a v-if="canSave(f)" @click.stop.prevent="saveFeature(f)" title="Save" class="button tiny secondary float-right action" style="margin-left:2px"><i class="fa fa-save actionicon"></i></a>
                  <div class="feature-title"><img class="feature-icon" id="bushfire-icon-{{f.get('id')}}" v-bind:src="featureIconSrc(f)" /> {{ f.get('label') }} <i><small></small></i></div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<style>
.actionicon {
    width:9px;
}
</style>
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
        statusFilter: '',
        region:'',
        district:'',
        tools: [],
        fields: ['id', 'name'],
        drawings:new ol.Collection(),
        allFeatures: new ol.Collection(),
        editableFeatures:new ol.Collection(),
        extentFeatures: [],
        selectedBushfires: [],
        bushfiresfile:'',
        revision:1,
        profileRevision:1,
        tints: {
          'new':[["#b43232","#1c6928"]],
          'new.text':"#1c6928",
          'new.fillColour':[0, 0, 0, 0.25],
          'new.colour':"#1c6928",
          'unknown': [['#b43232','#f90c25']],
          'unknown.text': '#f90c25',
          'unknown.fillColour':[0, 0, 0, 0.25],
          'unknown.colour': '#f90c25',
          'initial': [['#b43232','#b08c9d']],
          'initial.text': '#b08c9d',
          'initial.fillColour':[0, 0, 0, 0.25],
          'initial.colour': '#b08c9d',
          'submitted': [['#b43232','#3f1919']],
          'submitted.text': '#3f1919',
          'submitted.fillColour':[0, 0, 0, 0.25],
          'submitted.colour': '#3f1919',
          'draft_final': [['#b43232', '#b7d28d']],
          'draft_final.text': '#b7d28d',
          'draft_final.fillColour':[0, 0, 0, 0.25],
          'draft_final.colour': '#b7d28d',
          'final': [['#b43232', '#7ecca3']],
          'final.text': '#7ecca3',
          'final_authorised.fillColour':[0, 0, 0, 0.25],
          'final_authorised.colour': '#7ecca3',
          'draft_review': [['#b43232', '#7ecca3']],
          'draft_review.text': '#7ecca3',
          'draft_review.fillColour':[0, 0, 0, 0.25],
          'draft_review.colour': '#7ecca3',
          'reviewed': [['#b43232', '#7ecca3']],
          'reviewed.text': '#7ecca3',
          'reviewed_authorised.fillColour':[0, 0, 0, 0.25],
          'reviewed_authorised.colour': '#7ecca3',
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
      annotations: function () { return this.$root.$refs.app.$refs.annotations },
      active: function () { return this.$root.active},
      measure: function () { return this.$root.measure },
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
        return this.annotations.selectedFeatures
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
                    if (res < 0.003 && geometries.length > 0 && feat.get('label') && vm.bushfireLabels && !vm.$root.active.isHidden(vm.map.getMapLayer("bfrs:bushfire_dev"))) {
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
      isModifiable:function(bushfire) {
        return this.whoami["bushfire"]["permission"][bushfire.get('status') + ".modify"]
      },
      isEditable:function(bushfire) {
        return this.whoami["bushfire"]["permission"][bushfire.get('status') + ".edit"]
      },
      isViewable:function(bushfire) {
        return this.whoami["bushfire"]["permission"][bushfire.get('status') + ".view"]
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
      isAuthorizable:function(bushfire){
        return this.whoami["bushfire"]["permission"][bushfire.get('status') + ".authorise"] 
      },
      canEdit:function(bushfire) {
        return this.revision && bushfire.get('status') !== "new" && this.isEditable(bushfire) && bushfire.get('tint') !== "modified"
      },
      canReset:function(bushfire) {
        return this.revision && bushfire.get('status') !== "new" // && this.isEditable(bushfire) && bushfire.get('tint') === "modified"
      },
      canSave:function(bushfire) {
        return this.revision && bushfire.get('status') !== "new" && this.isModifiable(bushfire) && bushfire.get('tint') === "modified"
      },
      canCreate:function(bushfire) {
        return this.revision && bushfire.get('status') === "new"
      },
      canDelete:function(bushfire) {
        return this.revision && this.isDeletable(bushfire)
      },
      canAuthorise:function(bushfire) {
        return this.revision && this.isAuthorizable(bushfire) && bushfire.get('tint') !== "modified"
      },
      createUrl:function() {
        return this.bfrsService + "/create/" 
      },
      editUrl:function(feat) {
        var status = feat.get('report_status')
        if ([1,2].indexOf(status) >= 0) {
            return this.bfrsService + "/bfrs/initial/" + feat.get('id') + "/"
        } else if ([3,4].indexOf(status) >= 0) {
            return this.bfrsService + "/bfrs/final/" + feat.get('id') + "/"
        } else if ([5,6].indexOf(status) >= 0) {
            return this.bfrsService + "/bfrs/review/" + feat.get('id') + "/"
        } else {
            return null
        }
      },
      saveUrl:function(feat) {
        return this.bfrsService + "/api/v1/bushfire/" + feat.get('id') + "/?format=json" 
      },
      deleteUrl:function(feat) {
        return this.bfrsService + "/delete/" + feat.get('id')
      },
      authoriseUrl:function(feat) {
        return this.bfrsService + "/authorise/" + feat.get('id')
      },
      getSpatialData:function(feat) {
        var geometries = feat.getGeometry().getGeometriesArray()
        var originPoint = (geometries.length > 0 && geometries[0] instanceof ol.geom.Point)?geometries[0].getCoordinates():null
        var fireBoundary = (geometries.length > 1)?geometries[1]:((geometries.length ===  1 && geometries[0] instanceof ol.geom.MultiPolygon)?geometries[0]:null)
        var area = fireBoundary?this.measure.getTotalArea(fireBoundary):null
        //var length = fireBoundary?this.measure.getTotalLength(fireBoundary):null

        feat.set("area",area,true)

        fireBoundary = fireBoundary?fireBoundary.getCoordinates():null

        var requestData = {origin_point:originPoint, fire_boundary: fireBoundary,area:area}

        console.log( JSON.stringify(requestData ) )
        return requestData
      },
      saveFeature:function(feat) {
        if (this.canSave(feat)) {
            var vm = this
            $.ajax({
                url: vm.saveUrl(feat),
                method:"POST",
                data:JSON.stringify(vm.getSpatialData(feat)),
                contentType:"application/json",
                success: function (response, stat, xhr) {
                    feat.set('tint',feat.get('originalTint'),true)
                    feat.set('fillColour',vm.tints[feat.get('tint') + ".fillColour"])
                    feat.set('colour',vm.tints[feat.get('tint') + ".colour"])
                    vm.revision += 1
                },
                error: function (xhr,status,message) {
                    alert(status + " : " + message)
                },
                xhrFields: {
                  withCredentials: true
                }
            })
        }
      },
      newFeature:function(feat) {
        var vm = this
        var autoSelect = true
        this._bushfireSequence = (this._bushfireSequence || 0) 
        var featId = 0
        if (feat && feat.get('id')) {
            if (Math.abs(feat.get('id')) > this._bushfireSequence) {
                this._bushfireSequence = Math.abs(feat.get('id'))
            }
            autoSelect = false
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

        this.bfrsMapLayer.getSource().addFeature(feat)
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
        if (autoSelect) {
            this.selectedFeatures.clear()
            this.selectedFeatures.push(feat)
            this.annotations.setTool(this.ui.originPointTool)
        }
      },
      createFeature:function(feat) {
        if (this.canCreate(feat)) {
            var target = "_blank"
            if (env.appType == "cordova") {
                target = "_system"       
            }
            var data = this.getSpatialData(feat)
            
            var url = this.createUrl() + "?origin_point=" + JSON.stringify(data.origin_point) + "&fire_boundary=" + JSON.stringify(data.fire_boundary) + "&sss_id=" + feat.get('sss_id')
            //console.log(url)
            window.open(url,target.target);
        }
      },
      authoriseFeature:function(feat) {
        if (this.canAuthorise(feat)) {
            var vm = this
            $.ajax({
                url: vm.authoriseUrl(feat),
                method:"GET",
                success: function (response, stat, xhr) {
                    vm.resetFeature(feat)
                },
                error: function (xhr,status,message) {
                    alert(status + " : " + message)
                },
                xhrFields: {
                  withCredentials: true
                }
            })
        }
      },
      deleteFeature:function(feat) {
         var vm = this
         if (this.canDelete(feat)) {
            vm._deleteFeature = vm._deleteFeature || function(feat) {
                //console.log("Delete feature " + feat.get('label'))
                vm.bfrsMapLayer.getSource().removeFeature(feat)
                vm.allFeatures.remove(feat)
                if (vm.editableFeatures) {
                    vm.editableFeatures.remove(feat)
                }
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
                        alert(status + " : " + message)
                    },
                    xhrFields: {
                      withCredentials: true
                    }
                })
            }
        }
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

            index = vm.selectedFeatures.getArray().findIndex(function(f){return f.get('id') === feat.get('id')})
            if (index >= 0) {
                vm.selectedFeatures.setAt(index,features[0])
            }
              
          }
        })
      },  
      adjustHeight:function() {
        if (this.activeMenu === "bfrs") {
            $("#bfrs-list").height(this.screenHeight - this.leftPanelHeadHeight - $("#bfrs-list-controller-container").height())
        }
      },
      postModified:function(bushfires) {
        var vm = this
        var sortRequired = false
        this._bushfirePostModified = this._bushfirePostModified || function(bushfire) {
            if (bushfire.get('tint') !== "modified" && bushfire.get('tint') !== "new") {
                bushfire.set('tint',"modified",true)
                bushfire.set('fillColour',vm.tints[bushfire.get('tint') + ".fillColour"])
                bushfire.set('colour',vm.tints[bushfire.get('tint') + ".colour"])
            }
            var index = (vm.extentFeatures)?vm.extentFeatures.findIndex(function(f) { return f === bushfire}):-1
            if (index >= 0) {
                if (bushfire.getGeometry().getGeometriesArray().length === 0) {
                    //all geometries are deleted
                    vm.extentFeatures.splice(index,1)
                }
            } else {
                if (bushfire.getGeometry().getGeometriesArray().length > 0) {
                    vm.extentFeatures.push(bushfire)
                    sortRequired = true
                }
            }
        }
        if (Array.isArray(bushfires)) {
            $.each(bushfires,function(index,bushfire){
                vm._bushfirePostModified(bushfire)
            })
        } else {
            vm._bushfirePostModified(bushfires)
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
        var geometries = feature.getGeometry()?[feature.getGeometry()]:[]
        if (feature.get("fire_boundary") && feature.get("fire_boundary").coordinates) {
            geometries.push(new ol.geom.MultiPolygon(feature.get("fire_boundary").coordinates))
            feature.unset("fire_boundary",true)
        }
        feature.setGeometry(new ol.geom.GeometryCollection(geometries),true)
        var now = moment()
        var timestamp = moment(feature.get('created'))

        feature.set('status',this._reportStatus[feature.get('report_status') || 99999],true)

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
            $("#bushfire-icon-" + f.get('id')).attr("src", vm.featureIconSrc(f))
        })
      },
      selected: function (f) {
        return f.get('id') && (this.selectedBushfires.indexOf(f.get('id')) > -1)
      },
      downloadList: function () {
        this.$root.export.exportVector(this.features.filter(this.featureFilter).sort(this.featureOrder), 'bfrs')
      },
      importList: function () {
        if (this.$els.bushfiresfile.files.length === 0) {
            return
        }
        var vm = this
        this.export.importVector(this.$els.bushfiresfile.files[0],function(features,fileFormat){
            var ignoredFeatures = []
            var f = null
            if ((fileFormat === ".geojson") || (fileFormat === ".json")) {
                //geo json file
                for(var i = features.length - 1;i >= 0;i--) {
                    feature = features[i]
                    if (feature.get("toolName") !== "Bfrs Origin Point" ) {
                        //external feature.
                        if (feature.getGeometry() instanceof ol.geom.Point) {
                            vm.map.clearFeatureProperties(feature)
                            feature.setGeometry(new ol.geom.GeometryCollction([feature.getGeometry()]))
                        } else if (feature.getGeometry() instanceof ol.geom.Polygon) {
                            vm.map.clearFeatureProperties(feature)
                            feature.setGeometry(new ol.geom.GeometryCollction([new ol.geom.MultiPloygon([feature.getGeometry().getCoordinates()])]))
                        } else if (feature.getGeometry() instanceof ol.geom.MultiPolygon) {
                            //A multi polygon will be imported as a bushfire report
                            vm.map.clearFeatureProperties(feature)
                            feature.setGeometry(new ol.geom.GeometryCollction([feature.getGeometry()]))
                        } else if (feature.getGeometry() instanceof ol.geom.GeometryCollection) {
                            //A geometry collection will be imported as a bushfire report
                            vm.map.clearFeatureProperties(feature)
                            var geometries = feature.getGeometry().getGeometriesArray().find(function(g,i){return g instanceof ol.geom.Point})
                            geometries = geometries?[geometries]:[]
                            var fireBoundary = null
                            $.each(feature.getGeometry().getGeometriesArra().filter(function(g,i) {return g instanceof ol.geom.MultiPolygon}),function(index,mp){
                                if (fireBoundary) {
                                    $.each(mp.getPolygons(),function(index,p){fireBoundary.appendPolygon(p)})
                                } else {
                                    fireBoundary = mp
                                }
                            })
                            $.each(feature.getGeometry().getGeometriesArra().filter(function(g,i) {return g instanceof ol.geom.Polygon}),function(index,p){
                                fireBoundary = fireBoundary || new ol.geom.MultiPolygon()
                                fireBoundary.appendPolygon(p)
                            })
                            if (fireBoundary) {
                                geometries.push(fireBoundary)
                            }
                            feature.setGeometry(new ol.geom.GeometryCollction(geometries))
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
                        feature.setGeometry(new ol.geom.GeometryCollection([new ol.geom.MultiPolygon([[coordinates]])]))
                    } else if(feature.getGeometry() instanceof ol.geom.MultiLineString) {
                        var geom = feature.getGeometry()
                        var coordinates = null
                        var mp = null
                        $.each(geom.getLineStrings(),function(index,linestring) {
                            coordinates = linestring.getCoordinates()
                            coordinates.push(coordinates[0])
                            mp = mp || new ol.geom.MultiPolygon()
                            mp.appendPolygon(new ol.geom.Polygon([coordinates]))
                        })
                        feature.setGeometry(new ol.geom.GeometryCollection(mp?[mp]:[]))
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
                var notFoundBushfires = null
                $.each(features,function(index,feature){
                    if (feature.get('id') !== undefined) {
                        //existed bushfire report
                        var feat = vm.allFeatures.getArray().find(function(f) {return f.get('id') === feature.get('id')})
                        if (feat) {
                            if (!vm.map.isGeometryEqual(feat.getGeometry(),feature.getGeometry())) {
                                //console.log("====================")
                                //console.log(JSON.stringify(vm.getSpatialData(feat)))
                                //console.log(JSON.stringify(vm.getSpatialData(feature)))
                                feat.setGeometry(feature.getGeometry())  
                                vm.postModified(feat)
                            }
                        } else if(feature.get('id') < 0) {
                            //new feature,
                            vm.newFeature(feature)
                        } else {
                            notFoundBushfires = notFoundBushfires || []
                            notFoundBushfires.push(feature)
                        }
                    }
                }) 
                $.each(features,function(index,feature){
                    if (feature.get('id') === undefined) {
                        //non existed bushfire report
                        vm.newFeature(feature)
                    }
                }) 
                if (notFoundBushfires) {
                    alert("Some bushfires are not found." + JSON.stringify(notFoundBushfires.map(function(o) {return {id:o.get('id'),name:o.get('name')}})))
                }
            }
        })
      },
      downloadSelectedCSV: function () {
          var bushfireFilter = ''
          if (this.selectedBushfires.length > 0) {
              bushfireFilter = 'id__in=' + this.selectedBushfires.join(',')
          }
          return bushfireFilter
      },
      updateCQLFilter: function (updateType,runNow) {
        var vm = this
        if (updateType === "region") {
            this.district = ""
        }
        if (!vm._updateCQLFilterFunc) {
            vm._updateCQLFilterFunc = function(updateType){
                var bushfireFilter = ''
                // filter by specific bushfires if "Show selected only" is enabled
                if ((vm.selectedBushfires.length > 0) && (vm.selectedOnly)) {
                  bushfireFilter = 'id in (' + vm.selectedBushfires.join(',') + ')'
                }
                // CQL statement assembling logic
                var filters = [vm.statusFilter, bushfireFilter, vm.regionFilter, vm.districtFilter].filter(function(f){return (f || false) && true})
                if (filters.length === 0) {
                  vm.bfrsLayer.cql_filter = ''
                } else if (filters.length === 1) {
                  vm.bfrsLayer.cql_filter = filters[0]
                } else {
                  vm.bfrsLayer.cql_filter = "(" + filters.join(") and (") + ")"
                }
                if (!bushfireFilter && vm.selectedOnly) {
                    vm.selectedOnly = false
                }
                if (updateType === "selectedBushfire" && bushfireFilter) {
                    //chosed some bushfires
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
                    //clear bushfire filter or change other filter
                    vm.bfrsMapLayer.getSource().loadSource("query")
                }
            }
        }

        if (!vm._updateCQLFilter) {
            vm._updateCQLFilter = debounce(function(updateType){
                vm._updateCQLFilterFunc(updateType)
            },2000)
        }
        if (runNow) {
            vm._updateCQLFilterFunc(updateType)
        } else {
            vm._updateCQLFilter(updateType)
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
            //
            vm.editableFeatures.clear()
            vm.editableFeatures.extend(allFeatures)
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
        $.ajax({
            url: vm.bfrsService + "/api/v1/profile/?format=json",
            method:"GET",
            dataType:"json",
            success: function (response, stat, xhr) {
                vm.whoami["bushfire"]["profile"] = response
                vm.profileRevision += 1
                if (vm.whoami["bushfire"]["regions"]) {
                    vm.region = vm.whoami["bushfire"]["profile"]["region_id"] || ""
                    vm.district = vm.whoami["bushfire"]["profile"]["district_id"] || ""
                    vm.updateCQLFilter('district',true)
                }
            },
            error: function (xhr,status,message) {
                alert(status + " : " + message)
            },
            xhrFields: {
              withCredentials: true
            }
        })
      },
      loadRegions:function() {
        var vm = this
        $.ajax({
            url: vm.bfrsService + "/api/v1/region/?format=json",
            method:"GET",
            dataType:"json",
            success: function (response, stat, xhr) {
                vm.whoami["bushfire"]["regions"] = response
                vm.profileRevision += 1
                if (vm.whoami["bushfire"]["profile"]) {
                    vm.region = vm.whoami["bushfire"]["profile"]["region_id"] || ""
                    vm.district = vm.whoami["bushfire"]["profile"]["district_id"] || ""
                    vm.updateCQLFilter('district',true)
                }
            },
            error: function (xhr,status,message) {
                alert(status + " : " + message)
            },
            xhrFields: {
              withCredentials: true
            }
        })
      },

      setup: function() {
        var vm = this
        // enable resource bfrs layer, if disabled
        var catalogue = this.$root.catalogue
        if (!this.bfrsMapLayer) {
          catalogue.onLayerChange(this.bfrsLayer, true)
        }

        this.$root.annotations.selectable = [this.bfrsMapLayer]
        this.annotations.setTool()

        //add feature to place an point based on coordinate
        this.$root.search.setSearchPointFunc(function(searchMethod,coords,name){
            var feat = vm.selectedFeatures.getLength() === 1?vm.selectedFeatures.item(0):null
            if (!feat) {return false}

            var hasPoint = feat.getGeometry().getGeometriesArray().length > 0 && feat.getGeometry().getGeometriesArray()[0] instanceof ol.geom.Point
            if (vm.annotations.tool && 
                ["DMS","MGA"].indexOf(searchMethod) >= 0 && 
                (vm.annotations.tool.name === "Bfrs Edit Geometry" || (vm.annotations.tool.name === "Bfrs Origin Point" && !hasPoint) )
            ) {
                if (hasPoint) {
                    feat.getGeometry().getGeometriesArray()[0] = new ol.geom.Point(coords)
                } else {
                    feat.getGeometry().getGeometriesArray().splice(0,0,new ol.geom.Point(coords))
                }
                feat.getGeometry().setGeometriesArray(feat.getGeometry().getGeometriesArray())
                vm.postModified(feat)
                feat.getGeometry().changed()

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
      var bfrsStatus = this.loading.register("bfrs","Bush Fire Report Component","Initialize")
      var map = this.$root.map

      vm._reportStatus = {
       99999: "unknown",
        1: "initial",
        2: "submitted",
        3: "draft_final",
        4: "final_authorised",
        5: "draft_review",
        6: "reviewed"
      }
      
      vm.whoami["bushfire"] = vm.whoami["bushfire"] || {}
      vm.whoami["bushfire"]["permission"] = vm.whoami["bushfire"]["permission"] || {
          "create":null,
          "new.edit":false,
          "new.modify":true,
          "new.delete":true,
          "new.authorise":false,
          "unknown.edit":false,
          "unknown.delete":false,
          "unknown.authorise":false,
          "initial.edit":true,
          "initial.modify":true,
          "initial.delete":false,
          "initial.authorise":null,
          "submitted.edit":true,
          "submitted.modify":false,
          "submitted.delete":false,
          "submitted.authorise":false,
          "draft_final.edit":true,
          "draft_final.modify":true,
          "draft_final.delete":false,
          "draft_final.authorise":null,
          "final_authorised.edit":true,
          "final_authorised.modify":false,
          "final_authorised.delete":false,
          "final_authorised.authorise":false,
          "draft_review.edit":true,
          "draft_review.modify":null,
          "draft_review.delete":false,
          "draft_review.authorise":null,
          "reviewed.edit":true,
          "reviewed.modify":false,
          "reviewed.delete":false,
          "reviewed.authorise":false,
      }

      vm.loadRegions()

      vm.ui = {}
      var toolConfig = {features:vm.allFeatures,mapLayers:function(layer){return layer.get("id") === "bfrs:bushfire_dev" }}
      vm.ui.translateInter = vm.annotations.translateInterFactory()(toolConfig)
      vm.ui.translateInter.on("translateend",function(ev){
          vm.postModified(ev.features.getArray())
      })
      vm.ui.dragSelectInter = vm.annotations.dragSelectInterFactory()(toolConfig)
      vm.ui.selectInter = vm.annotations.selectInterFactory()(toolConfig)
      vm.ui.geometrySelectInter = vm.annotations.selectInterFactory()($.extend({selectMode:"geometry"},toolConfig))

      vm.ui.modifyInter = vm.annotations.modifyInterFactory()({features:vm.editableFeatures,mapLayers:function(layer){return layer.get("id") === "bfrs:bushfire_dev" }})
      vm.ui.modifyInter.on("featuresmodified",function(ev){
          vm.postModified(ev.features.getArray())
      })    

      vm.ui.originPointDraw = vm.annotations.pointDrawFactory({
        events: {
            addfeaturegeometry:true
        },
        drawOptions:{
            condition:function(ev) {
                var feat = (vm.selectedFeatures.getLength() == 1)?vm.selectedFeatures.item(0):null
                if (feat) {
                    var featGeometry = feat.getGeometry()
                    if (vm.isModifiable(feat) && (feat.getGeometry().getGeometriesArray().length == 0 || !(feat.getGeometry().getGeometriesArray()[0] instanceof ol.geom.Point))) {
                        return ol.events.condition.noModifierKeys(ev)
                    } else {
                        return false
                    }
                } else {
                    return false
                }
            }
        }
      })({
        features:vm.drawings
      })

      vm.ui.fireboundaryDraw = vm.annotations.polygonDrawFactory({
        events: {
            addfeaturegeometry:true
        },
        drawOptions:{
            condition:function(ev) {
                var feat = (vm.selectedFeatures.getLength() == 1)?vm.selectedFeatures.item(0):null
                if (feat) {
                    var featGeometry = feat.getGeometry()
                    if (vm.isModifiable(feat)) {
                        return ol.events.condition.noModifierKeys(ev)
                    } else {
                        return false
                    }
                } else {
                    return false
                }
            }
        }
      })({
        features:vm.drawings
      })
      vm.drawings.on("add",function(ev){
        if (vm.selectedFeatures.getLength() === 1){
            var f = vm.selectedFeatures.item(0)
            if (vm.annotations.tool.name === "Bfrs Fire Boundary") {
                var indexes = null
                var index = f.getGeometry().getGeometriesArray().findIndex(function(g){return g instanceof ol.geom.MultiPolygon})
                if (index >= 0) {
                    indexes = [index,f.getGeometry().getGeometriesArray()[index].getPolygons().length]
                    f.getGeometry().getGeometriesArray()[index].appendPolygon(new ol.geom.Polygon(ev.element.getGeometry().getCoordinates()))
                } else {
                    indexes = [f.getGeometry().getGeometriesArray().length,0]
                    f.getGeometry().getGeometriesArray().push(new ol.geom.MultiPolygon([ev.element.getGeometry().getCoordinates()]))
                }
                vm.ui.fireboundaryDraw.dispatchEvent(vm.annotations.createEvent(vm.ui.fireboundaryDraw,"addfeaturegeometry",{feature:f,indexes:indexes}))
            } else if (f.getGeometry().getGeometriesArray().length > 0 && f.getGeometry().getGeometriesArray()[0] instanceof ol.geom.Point){
                f.getGeometry().getGeometriesArray()[0] = ev.element.getGeometry()
                vm.ui.originPointDraw.dispatchEvent(vm.annotations.createEvent(vm.ui.originPointDraw,"addfeaturegeometry",{feature:f,indexes:[0]}))
            } else {
                f.getGeometry().getGeometriesArray().splice(0,0,ev.element.getGeometry())
                vm.ui.originPointDraw.dispatchEvent(vm.annotations.createEvent(vm.ui.originPointDraw,"addfeaturegeometry",{feature:f,indexes:[0]}))
            }
            f.getGeometry().setGeometriesArray(f.getGeometry().getGeometriesArray())
            vm.postModified(f)
            f.getGeometry().changed()
            vm.drawings.clear()
        }
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
                  vm.ui.translateInter,
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
                            } else if (vm.isModifiable(feature)) {
                                feature.getGeometry().getGeometriesArray().length = 0
                                this.dispatchEvent(vm.annotations.createEvent(this,"deletefeatureallgeometries",{feature:feature}))
                                if (feature["selectedIndex"] !== undefined) {
                                    delete feature["selectedIndex"]
                                }
                                vm.postModified(feature)
                                feature.changed()
                            }
                        }
                    }
                  }),
              ],
              keepSelection:true,
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
                  vm.ui.geometrySelectInter,
                  vm.annotations.keyboardInterFactory({
                    selectEnabled:false,
                    events:{ 
                        deletefeaturegeometry:true
                    },
                    deleteSelected:function(features,selectedFeatures) {
                        selectedFeatures.forEach(function (feature) {
                            if (vm.isModifiable(feature) && feature["selectedIndex"] !== undefined) {
                                vm.annotations.deleteSelectedGeometry(feature,this)
                                vm.selectDefaultGeometry(feature)
                                vm.postModified(feature)
                            }
                        },this)
                    }
                  }),
                  vm.ui.modifyInter
              ],
              selectMode:"geometry",
              keepSelection:true,
              onSet: function() {
                  vm.ui.dragSelectInter.setMulti(false)
                  vm.ui.geometrySelectInter.setMulti(false)
                  if (vm.selectedFeatures.getLength() > 1) {
                      vm.selectedFeatures.clear()
                  } else if (vm.selectedFeatures.getLength() == 1) {
                    var selectedFeature = vm.selectedFeatures.item(0)
                    if (selectedFeature["selectedIndex"] === undefined ) {
                        vm.selectDefaultGeometry(selectedFeature)
                    } 
                 }
              }
          }, {
              name: 'Bfrs Origin Point',
              label: 'Origin Point',
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
              scope:["bfrs"],
              measureLength:true,
              measureArea:true,
              keepSelection:true,
              showName: true,
              onSet: function() {
                  if (vm.selectedFeatures.getLength() > 1) {
                      vm.selectedFeatures.clear()
                  }
              }
          },{
              name: 'Bfrs Fire Boundary',
              label: 'Fire Boundary',
              icon: 'dist/static/images/iD-sprite.svg#icon-area',
              style: vm.annotations.getVectorStyleFunc(vm.tints),
              selectedFillColour:[0, 0, 0, 0.25],
              fillColour:[0, 0, 0, 0.25],
              size:2,
              interactions: [
                  this.ui.fireboundaryDraw
              ],
              scope:["bfrs"],
              showName: true,
              keepSelection:true,
              onSet: function() {
                  if (vm.selectedFeatures.getLength() > 1) {
                      vm.selectedFeatures.clear()
                  }
              }
          }
      ]

      tools.forEach(function (tool) {
        vm.annotations.tools.push(tool)
      })

      vm.ui.modifyTool = vm.annotations.tools.find(function(tool){return tool.name === "Bfrs Edit Geometry"})
      vm.ui.originPointTool = vm.annotations.tools.find(function(tool){return tool.name === "Bfrs Origin Point"})

      this.$root.fixedLayers.push({
        type: 'WFSLayer',
        name: 'Bush Fire Report',
        id: 'bfrs:bushfire_dev',
        getFeatureInfo:function (f) {
            return {name:f.get("name"), img:map.getBlob(f, ['icon', 'tint']), comments:"TBD"}
        },
        initialLoad:false,
        //refresh: 60,
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
        onload: function(loadType,vectorSource,features,defaultOnload) {
            //combine the two spatial columns into one
            $.each(features,function(index,feature){
                vm.initBushfire(feature)
            })
            function processResources() {
                //merge the current changes with the new features
                $.each(vm.allFeatures.getArray().filter(function(f) {return ['new','modified'].indexOf(f.get('tint')) >= 0 }),function(index,f){
                    if (f.get('tint') === 'new') {
                        //new features always are the begining and sorted.
                        features.splice(index,0,f)
                    } else {
                        newFeature = features.find(function(f2){return f.get('id') === f2.get('id')})
                        if (newFeature) {
                            //replace the newFeature's geometry with the modified version
                            newFeature.setGeometry(f.getGeometry())
                            newFeature.set('tint','modified',true)
                            newFeature.set('fillColour',vm.tints[newFeature.get('tint') + ".fillColour"])
                            newFeature.set('colour',vm.tints[newFeature.get('tint') + ".colour"])
                        } 
                    }
                })
                defaultOnload(loadType,vectorSource,features)
                if (vm.selectedBushfires.length > 0) {
                    var bushfireIds = vm.selectedBushfires.slice()
                    vm.selectedFeatures.clear()
                    features.filter(function(el, index, arr) {
                      var id = el.get('id')
                      if (!id) return false
                      if (bushfireIds.indexOf(id) < 0) return false
                      return true
                    }).forEach(function (el) {
                      vm.selectedFeatures.push(el)
                    })
                }
                vm.updateFeatureFilter(true)

                if (vm.whoami['bushfire']["permission"]["changed"]) {
                    delete vm.whoami['bushfire']["permission"]["changed"]
                    vm.revision += 1
                }
            }
            var permissionConfig = [
                ["create",null,null],
                ["initial.edit",null,function(f){return f.get('status') === "initial"}],
                ["draft_final.edit",null,function(f) {return f.get('status') === "final"}],
                ["final_authorised.edit",null,function(f) {return f.get('status') === "final_authorised"}],
            ]
            var checkPermission = function(index){
                var p = permissionConfig[index]
                var url = null
                if (vm.whoami['bushfire']["permission"][p[0]] === null || vm.whoami['bushfire']["permission"][p[0]] === undefined){
                    if (p[1] === null) {
                        //always have the permission
                        vm.whoami['bushfire']["permission"][p[0]] = true
                        vm.whoami['bushfire']["permission"]["changed"] = true
                    } else {
                        if (typeof p[1] === "string") {
                            //url is a constant string
                            url = p[1]
                        } else {
                            //url is a function with a bushfire argument.
                            var f = features.find(p[2])
                            if (f) {
                                //get the test url
                                url = p[1](f)
                            } else {
                                //can't find a bushfire to test
                                url = null
                                vm.whoami['bushfire']["permission"][p[0]] = null
                                vm.whoami['bushfire']["permission"]["changed"] = true
                            }
                        }
                    }
                }
                if (url) {
                    utils.checkPermission(url,function(allowed){
                        vm.whoami['bushfire']["permission"][p[0]] = allowed
                        vm.whoami['bushfire']["permission"]["changed"] = true
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

      this.measure.register("bfrs:bushfire_dev",this.allFeatures)

      bfrsStatus.wait(40,"Listen 'gk-init' event")
      // post init event hookup
      this.$on('gk-init', function () {
        bfrsStatus.progress(80,"Process 'gk-init' event")
        map.olmap.getView().on('propertychange', vm.updateViewport)

        vm.selectedFeatures.on('add', function (event) {
          if (event.element.get('toolName') === "Bfrs Origin Point") {
            vm.selectedBushfires.push(event.element.get('id'))
            if (vm.annotations.tool.selectMode === "geometry") {
                if (event.element["selectedIndex"] === undefined) {
                    vm.selectDefaultGeometry(event.element)
                }
            }
            if (vm.selectedOnly) {
                vm.updateCQLFilter('selectedBushfire')
            }
          }
        })
        vm.selectedFeatures.on('remove', function (event) {
          if (event.element.get('toolName') === "Bfrs Origin Point") {
            vm.selectedBushfires.$remove(event.element.get('id'))
            if (vm.selectedOnly) {
                vm.updateCQLFilter('selectedBushfire')
            }
          }
          //remove the index of the selected geometry in geometry collection
          //delete event.element['selectedIndex']
        })
        //load user profile
        vm.loadUserProfile()
        // enable resource bfrs layer, if disabled
        //vm.annotations.setDefaultTool('bfrs','Pan')
        vm.tools = vm.annotations.tools.filter(function (t) {
          return t.scope && t.scope.indexOf("bfrs") >= 0
        })
        bfrsStatus.end()
      })
    }
  }
</script>
