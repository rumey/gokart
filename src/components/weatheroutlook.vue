<template>
  <div class="tabs-panel" id="weatheroutlook" v-cloak>
    <div class="row">
      <div class="columns">
        <div class="tabs-content vertical" data-tabs-content="setting-tabs">
          <div id="weatheroutlook-settings">

            <div class="tool-slice row collapse">
                <div class="small-4">
                    <label class="tool-label">Outlook Days:</label>
                </div>
                <div class="small-8">
                    <select name="weatheroutlookOutlookDays" v-model="outlookDays" @change="systemsetting.saveState(10000)">
                        <option value="1">Today</option>      
                        <option value="2">2 Days</option>      
                        <option value="3">3 Days</option>      
                        <option value="4">4 Days</option>      
                        <option value="6">6 Days</option>      
                        <option value="7">7 Days</option>      
                    </select>
                </div>
            </div>

            <div class="tool-slice row collapse">
                <div class="small-4">
                    <label class="tool-label">Outlook Times:</label>
                </div>
                <div class="small-8">
                    <select name="weatheroutlookReportType" v-model="reportType" @change="systemsetting.saveState(10000)">
                        <option value="1">Hourly</option>      
                        <option value="2">2 Hourly</option>      
                        <option value="3">3 Hourly</option>      
                        <option value="4">4 Hourly</option>      
                        <option value="6">6 Hourly</option>      
                        <option value="0">Others</option>      
                    </select>
                    <div v-show="reportType == 0">
                      <input type="text" v-model="editingReportHours" placeholder="hours(0-23) separated by ','" @blur="formatReportHours" @keyup="formatReportHours">
                    </div>
                </div>
            </div>

            <div class="tool-slice row collapse">
                <hr class="small-12"/>
            </div>
          </div>

          <div class="tool-slice row collapse" id="weatheroutlook-data-config">
            <div class="columns">
                <ul class="accordion" data-accordion>
                    <li class="accordion-item" data-accordion-item>
                        <!-- Accordion tab title -->
                        <a href="#" class="accordion-title">Daily Title</a>
                        <!-- Accordion tab content: it would start in the open state due to using the `is-active` state class. -->
                        <div class="accordion-content scroller" data-tab-content id="weatheroutlook-header">
                            <textarea type="text" rows="4" style="width:100%;resize:vertical" id="daily-title" v-model="editingDailyTitle" placeholder="{date}" @blur="formatDailyTitle" @keyup="formatDailyTitle"> </textarea>
                            <div class="row feature-row status-row">
                                <div class="small-4">
                                    <div class="outlook-datasources">date</div>
                                </div>
                                <div class="small-8">
                                    <div class="outlook-datasources">outlook date</div>
                                </div>
                            </div>
                            <div v-for="ds in dailyDatasources" track-by="id" class="row feature-row status-row" >
                                <div class="small-4">
                                    <div class="outlook-datasources">{{ ds.var}} </div>
                                </div>
                                <div class="small-8">
                                    <div class="outlook-datasources">{{ ds.name}}</div>
                                </div>
                            </div>
                        </div>
                    </li>
                    <li class="accordion-item is-active" data-accordion-item>
                        <!-- Accordion tab title -->
                        <a href="#" class="accordion-title">Chosen Columns</a>
                        <!-- Accordion tab content: it would start in the open state due to using the `is-active` state class. -->
                        <div class="accordion-content" data-tab-content>
                            <div class="scroller" id="weatheroutlook-columns" style="margin-left:-16px;margin-right:-16px">
                            <div style="margin-left:16px;margin-right:16px">
                                <template v-for="(index,column) in (revision && outlookColumns)" track-by="$index" >
                                    <template v-if="column.group">
                                    <div class='row feature-row {{column===selectedColumn?"feature-selected":""}}' @click="selectColumn(index,-1,column)" id="active-column-{{index}}">
                                        <div class="small-12">
                                            {{ column.group}}
                                            <div class="text-right float-right">
                                                <a @click.stop.prevent="removeColumn(index,-1,column)" v-show="!column.required" class="button tiny secondary alert" title="Remove"><i class="fa fa-close"></i></a>
                                                <a v-bind:disabled="index <= 0" @click.stop.prevent="moveUp(index,-1,column)" title="Move Up" class="button tiny secondary">
                                                    <i class="fa fa-arrow-up"></i>
                                                </a>
                                                <a v-bind:disabled="index >= outlookColumns.length - 1" @click.stop.prevent="moveDown(index,-1,column)" title="Move Down" class="button tiny secondary">
                                                    <i class="fa fa-arrow-down"></i>
                                                </a>
                                            </div>
                                        </div>
                                    </div>
                                    <div v-for="(subindex,subcolumn) in revision && column.datasources" track-by="id" class='row feature-row {{subcolumn===selectedColumn?"feature-selected":""}}'
                                        @click.stop.prevent="selectColumn(index,subindex,subcolumn)" id=active-column-{{index}}-{{subindex}} style="margin-left:0px;">
                                        <div class="small-12">
                                            {{ subcolumn.name}}
                                            <div class="text-right float-right">
                                                <a @click.stop.prevent="removeColumn(index,subindex,subcolumn)" v-show="!subcolumn.required" class="button tiny secondary alert" title="Remove"><i class="fa fa-close"></i></a>
                                                <a v-bind:disabled="subindex <= 0" @click.stop.prevent="moveUp(index,subindex,subcolumn)" title="Move Up" class="button tiny secondary">
                                                    <i class="fa fa-arrow-up"></i>
                                                </a>
                                                <a v-bind:disabled="subindex >= column.datasources.length - 1" 
                                                    @click.stop.prevent="moveDown(index,subindex,subcolumn)" title="Move Down" class="button tiny secondary">
                                                    <i class="fa fa-arrow-down"></i>
                                                </a>
                                            </div>
                                        </div>
                                    </div>
                                    </template>
                                    <template v-if="column.id">
                                    <div class='row feature-row {{column===selectedColumn?"feature-selected":""}}' @click="selectColumn(index,-1,column)" id="active-column-{{index}}">
                                        <div class="small-12">
                                            {{ column.name}}
                                            <div class="text-right float-right">
                                                <a @click.stop.prevent="removeColumn(index,-1,column)" class="button tiny secondary alert" v-show="!column.required" title="Remove"><i class="fa fa-close"></i></a>
                                                <a v-bind:disabled="index <= 0" @click.stop.prevent="moveUp(index,-1,column)" title="Move Up" class="button tiny secondary">
                                                    <i class="fa fa-arrow-up"></i>
                                                </a>
                                                <a v-bind:disabled="index >= outlookColumns.length - 1" @click.stop.prevent="moveDown(index,-1,column)" title="Move Down" class="button tiny secondary">
                                                    <i class="fa fa-arrow-down"></i>
                                                </a>
                                            </div>
                                        </div>
                                    </div>
                                    </template>
                                </template>
                            </div>
                            </div>

                            <div class="row" id="weatheroutlook-column-editor" style="margin-left:-10px;margin-right:-10px" >
                                <div class="small-4">
                                    <label class="tool-label">Title:</label>
                                </div>
                                <div class="small-8">
                                    <input type="text" v-model="editingColumnTitle" @blur="changeColumnTitle()" @keyup="changeColumnTitle" v-bind:disabled="!selectedColumn || selectedColumn.group">
                                </div>
                                <div class="small-4">
                                    <label class="tool-label">Group:</label>
                                </div>
                                <div class="small-8">
                                    <input type="text" v-model="editingColumnGroup" list="column-groups"  @blur="changeColumnGroup()" @keyup="changeColumnGroup"  v-bind:disabled="!selectedColumn">
                                    <datalist id="column-groups">
                                        <option v-for="group in columnGroups" track-by="$index" value="{{group}}">
                                    </datalist>
                                </div>
                            </div>
                        </div>
                    </li>
                    <li class="accordion-item" data-accordion-item>
                        <!-- Accordion tab title -->
                        <a href="#" class="accordion-title">Available Columns</a>
                        <!-- Accordion tab content: it would start in the open state due to using the `is-active` state class. -->
                        <div class="accordion-content scroller" data-tab-content id="weatheroutlook-datasources">

                            <div class="row">
                              <div class="switch tiny">
                                <input class="switch-input" id="toggleDailyDatasources" type="checkbox" v-bind:checked="showDailyDatasources" @change="showDailyDatasources=!showDailyDatasources" />
                                <label class="switch-paddle" for="toggleDailyDatasources">
                                  <span class="show-for-sr">Show daily datasources</span>
                                </label>
                              </div>
                              <label for="toggleDailyDatasources" class="side-label" >Show daily datasources</label>
                              <a @click.stop.prevent="refreshDatasources(true)"  title="Refresh" style="margin-left:120px" ><i class="fa fa-refresh"></i></a>
                            </div>

                            <template v-for="ds in datasources" track-by="id">
                              <div v-if="isShow(ds)" class="row feature-row status-row" >
                                <div class="small-12">
                                    {{ ds.name}}
                                    <div class="text-right float-right">
                                       <div class="switch tiny" @click.stop >
                                           <input class="switch-input ctlgsw" id="outlook_ds_{{ $index }}" v-bind:disabled="ds.required"  type="checkbox" @change="toggleDatasource(ds)" v-bind:checked="isDatasourceSelected(ds)"/>
                                           <label class="switch-paddle" for="outlook_ds_{{ $index }}">
                                               <span class="show-for-sr">Toggle</span>
                                           </label>
                                        </div>
                                    </div>
                                </div>
                                <div class="small-6 datasource-desc">
                                    <div class="outlook-datasources">Type: {{ ds.metadata.type }}</div>
                                </div>
                                <div class="small-6 datasource-desc">
                                    <div class="outlook-datasources" v-if="isDegreeUnit(ds)">Unit: &deg;
                                    </div>
                                    <div class="outlook-datasources" v-if="ds.metadata.unit && !isDegreeUnit(ds)">Unit: {{ ds.metadata.unit}}
                                    </div>
                                </div>
                                <div class="small-12 datasource-desc">
                                    <div class="outlook-datasources">Title: {{ ds.options.title }}</div>
                                </div>
                                <div class="small-12 datasource-desc">
                                    <div class="outlook-datasources">Updated: {{ ds.metadata.refresh_time?ds.metadata.refresh_time.toLocaleString():"" }}</div>
                                </div>
                              </div>
                            </template>
                        </div>
                    </li>
                </ul>
            </div>
          </div>

        </div>
      </div>
    </div>

    <div style="display:none">
    <div id="weatheroutlook_control" class="ol-selectable ol-control" v-bind:style="topPositionStyle">
        <button type="button" title="{{outlookSetting.title}}" @click="toggleTool()" v-bind:class="{'selected':isControlSelected}" style="width:48px;height:36px;border-bottom-left-radius:0px;border-bottom-right-radius:0px">
            <img v-bind:src="outlookSetting.icon" width="36" height="36">
        </button>
        <button type="button" style="height:16px;border-top-left-radius:0px;border-top-right-radius:0px"  @click="showSettings=!showSettings" >
            <i class="fa fa-angle-double-down" aria-hidden="true"></i>
        </button>
        <div v-show="showSettings" style="position:absolute;width:300px;right:0px">
            <button type="button" v-for="s in outlookSettings" title="{{s.title}}"  style="margin:1px;float:right" track-by="$index" @click.stop.prevent="selectSetting(s)">
                <img v-bind:src="s.icon" width="36" height="36">
            </button>
        </div>
    </div>
    </div>

    <form id="get_weatheroutlook" name="weatheroutlook" action="{{env.gokartService + '/weatheroutlook/html'}}" method="post" target="weatheroutlook">
        <input type="hidden" name="data" id="weatheroutlook_data">
    </form>
  </div>
</template>

<style>
#weatheroutlook_control button{
    width: 48px;
    height: 48px;
    margin: 0;
}

.datasource-desc {
    font-style:italic;
    padding-left:24px;
    color:#6dd8ef;
    font-size:14px;
}

#weatheroutlook-data-config .accordion {
    background-color: transparent
}
#weatheroutlook-data-config .accordion-content {
    background-color: transparent
}
#daily-title.alert{
    background-color: rgba(171, 116, 107, 0.7);
}
.outlook-datasources {
    font-size: 100%;
}
#weatheroutlook_control .selected{
    background-color: #2199E8;
}
#weatheroutlook_control {
    position: absolute;
    left: auto;
    right: 16px;
    bottom: auto;
    padding: 0;
}

</style>

<script>
  import { ol,saveAs,$,moment,utils} from 'src/vendor.js'
  export default {
    store: {
        reportType:'settings.weatheroutlook.reportType',
        reportHours:'settings.weatheroutlook.reportHours',
        dailyTitle:'settings.weatheroutlook.dailyTitle',
        outlookDays:'settings.weatheroutlook.outlookDays',
        outlookColumns:'settings.weatheroutlook.outlookColumns',
        screenHeight:'layout.screenHeight',
        leftPanelHeadHeight:'layout.leftPanelHeadHeight',
        activeMenu:'activeMenu',
        activeSubmenu:'activeSubmenu',
    },
    data: function () {
      return {
        format:"html",
        showDailyDatasources:false,
        dailyData:null,
        editingReportHours:"",
        editingDailyTitle:"",
        editingColumnTitle:"",
        editingColumnGroup:"",
        selectedRow:null,
        selectedDatasource:{},
        selectedIndex:-1,
        selectedSubindex:-1,
        selectedColumn:null,
        columnGroups:[],
        reportTimes:[],
        outlookSetting:{},
        outlookSettings:[
            {name:"weather-outlook-default",title:"Default 4 Day Weather Outlook",icon:"/dist/static/images/weather-outlook-default.svg"},
            {name:"weather-outlook-customized",title:"Customized Weather Outlook",icon:"/dist/static/images/weather-outlook-customized.svg"},
            {name:"weather-outlook-amicus",title:"Weather Outlook Amicus Export",icon:"/dist/static/images/weather-outlook-amicus.svg"}
        ],
        showSettings:false,
        revision:1,
      }

    },
    // parts of the template to be computed live
    computed: {
      loading: function () { return this.$root.loading },
      setting: function () { return this.$root.setting },
      map: function () { return this.$root.map },
      env: function () { return this.$root.env },
      systemsetting: function () { return this.$root.systemsetting },
      measure: function () { return this.$root.measure },
      active: function () { return this.$root.active },
      catalogue: function () { return this.$root.catalogue },
      annotations: function () { return this.$root.$refs.app.$refs.annotations },
      dailyDatasources:function() {
        return this.revision && (this._datasources?this._datasources["dailyDatasources"]:[])
      },
      datasources:function() {
        return this.revision && (this._datasources?this._datasources["datasources"]:[])
      },
      mapControl:function() {
        if (!this._controller) {
            this._controller = new ol.control.Control({
                element: $('#weatheroutlook_control').get(0),
        	target: $('#external-controls').get(0)
            })
        }
        return this._controller
      },
      isControlSelected:function() {
        if (this.annotations) {
            return this.annotations.tool === this._weatheroutlookTool
        } else {
            return false
        }
      },
      selectedColumnTitle:{
        get:function(){
            if (this.selectedColumn === null || this.selectedColumn.group) {
                return ""
            }
            return (this.selectedColumn.options && this.selectedColumn.options.title) || this.selectedDatasource.options.title
        },
        set:function(value){
            if (this.selectedColumn === null || this.selectedColumn.group) {
                return 
            }
            value = value.trim()
            if (!value || this.selectedDatasource.options.title === value) {
                if (this.selectedColumn.options && "title" in this.selectedColumn.options) {
                    delete this.selectedColumn.options["title"]
                }
            } else {
                this.selectedColumn.options = this.selectedColumn.options || {}
                this.selectedColumn.options["title"] = value
            }
        }
      },
      height:function() {
        if (!this.$root.toolbox || this.$root.toolbox.inToolbox(this)) {
            return 0
        } else if (!this.showSettings) {
            return 52 + 9
        } else {
            return 52 + Math.ceil(this.outlookSettings.length / 6) * 50 + 9
        }
      },
      topPosition:function() {
        return 180;
      },
      topPositionStyle:function() {
        return "top:" + this.topPosition + "px";
      },
      tools:function() {
        return this.outlookSettings
      },
    },
    watch:{
      isControlSelected:function(newValue,oldValue) {
        if (newValue) {
            this._overlay.setMap(this.map.olmap)
        } else {
            this._overlay.setMap(null)
        }
      },
      reportType:function(newValue,oldValue) {
        this.updateReportTimes()   
      },
      reportHours:function(newValue,oldValue) {
        this.updateReportTimes()   
      },
      outlookDays:function(newValue,oldValue) {
        this.changeOutlookDays()
      }
    },
    // methods callable from inside the template
    methods: {
      adjustHeight:function() {
        if (this.activeMenu === "settings" && this.activeSubmenu === "weatheroutlook") {
            //the 'chosen columns' is selected by default, so the first time when the user entries into the sportoutlook setting panel, the 'column editor' should have valid height value.
            this._columnEditorHeight = this._columnEditorHeight || $("#weatheroutlook-column-editor").height()
            var height = this.screenHeight - this.leftPanelHeadHeight - $("#weatheroutlook-settings").height() - 200
            $("#weatheroutlook-header").height(height)
            $("#weatheroutlook-columns").height(height - this._columnEditorHeight)
            $("#weatheroutlook-datasources").height(height)
        }
      },
      open:function(options) {
        //active this module
        if (this.activeMenu !== "settings") {
            $("#menu-tab-settings-label").trigger("click")
        }
        if (this.activeSubmenu !== "weatheroutlook") {
            $("#weatheroutlook-label").trigger("click")
        }
        if(!$('#offCanvasLeft').hasClass('reveal-responsive')){
            $('#offCanvasLeft').toggleClass('reveal-responsive')
            this.map.olmap.updateSize()
        }

      },
      changeOutlookDays:function() {
        this.outlookSettings[1].title = "Customised " + this.outlookDays + " Day Weather Outlook"
      },
      selectSetting:function(s) {
        this.showSettings = false
        if (this.outlookSetting === s) {
            return
        }
        this.outlookSetting = s
      },
      selectTool:function(tool) {
        if (tool.name === "weather-outlook-customized") {
            this.open()
        }
        if (this.outlookSetting === tool) {
            return
        }
        this.outlookSetting = tool
      },
      toggleTool: function (enable) {
        if (!this._weatheroutlookTool) {
            this.annotations.setTool(this.annotations.currentTool,true)
        } else if (enable === true && this.annotations.tool === this._weatheroutlookTool) {
            //already enabled
            return
        } else if (enable === false && this.annotations.tool !== this._weatheroutlookTool) {
            //already disabled
            return
        } else if (this.annotations.tool === this._weatheroutlookTool) {
            this.annotations.setTool(this.annotations.currentTool,true)
        } else  {
            this.annotations.setTool(this._weatheroutlookTool)
        }
      },
      isToolActivated:function(tool) {
        return this.isControlSelected
      },
      isDegreeUnit:function(ds) {
        return ds.metadata.unit === "C"
      },
      selectColumn:function(index,subindex,column) {
        if (this.selectedRow) {
            this.selectedRow.removeClass("feature-selected")
        }
        this.selectedIndex = index
        this.selectedSubindex = (subindex < 0 || subindex === null || subindex == undefined)?-1:subindex
        this.selectedRow = this.selectedSubindex == -1?$("#active-column-" + this.selectedIndex):$("#active-column-" + this.selectedIndex + "-" + this.selectedSubindex)
        this.selectedColumn = column
        if (column.group) {
            //the selected column is a group
            this.selectedDatasource = null
            this.editingColumnTitle = ""
            this.editingColumnGroup = column.group
        } else {
            //the selected column is a column
            this.selectedDatasource = this._datasources["datasources"].find(function(o){return o.id === column.id})
            this.editingColumnTitle = this.selectedColumnTitle
            this.editingColumnGroup = subindex >= 0 ?this.outlookColumns[index]["group"]:""
        }

        this.selectedRow.addClass("feature-selected")
      },
      changeColumnTitle:function(event) {
        if (event && event.type === "keyup" && event.keyCode !== 13) {  
            return
        }
        if (this.selectedColumnTitle === this.editingColumnTitle) {
            //not changed
            return
        }
        this.selectedColumnTitle = this.editingColumnTitle
        this.systemsetting.saveState(10000)
      },
      changeColumnGroup:function(event) {
        if (event && event.type === "keyup" && event.keyCode !== 13) {  
            return
        }
        this.editingColumnGroup = this.editingColumnGroup.trim()
        var vm = this
        if (this.selectedColumn.group) {
            if (this.editingColumnGroup === this.selectedColumn.group) {
                return
            }
            //remove the old group
            var groupIndex = this.columnGroups.findIndex(function(o){return o === vm.selectedColumn["group"]})
            if (groupIndex >= 0) {
                this.columnGroups.splice(groupIndex,1)
            }

            if (this.editingColumnGroup) {
                //change group name
                groupIndex = this.outlookColumns.findIndex(function(o) {return o.group?o.group === vm.editingColumnGroup:false})
                if (groupIndex >= 0) {
                    //group already exist,move the columns to existing groups
                    this.outlookColumns[groupIndex].datasources.push.apply(this.outlookColumns[groupIndex].datasources,this.selectedColumn.datasources)
                    //remove the old group
                    this.outlookColumns.splice(this.selectedIndex,1)
                    if (this.selectedIndex < groupIndex) {
                        this.selectedIndex = groupIndex - 1
                    } else {
                        this.selectedIndex = groupIndex
                    }
                    this.selectedIndex = groupIndex
                    this.selectedSubindex = -1
                    this.selectedColumn = this.outlookColumns[groupIndex]
                    this.selectedRow = null
                    this.selectedDatasource = null
                    this.editingColumnTitle = ""

                } else {
                    //group does not exist, rename the group
                    this.outlookColumns[vm.selectedIndex]["group"] = this.editingColumnGroup
                    this.columnGroups.push(this.editingColumnGroup)
                    this.columnGroups.sort()
                }
                

            } else {
                //remove group
                this.outlookColumns.splice(this.selectedIndex,1)
                $.each(this.selectedColumn.datasources,function(index,col){
                    vm.outlookColumns.splice(vm.selectedIndex + index,0,col)
                })
                this.selectedIndex = -1
                this.selectedSubindex = -1
                this.selectedColumn = null
                this.selectedRow = null
                this.selectedDatasource = null
                this.editingColumnTitle = ""
                this.editingColumnGroup = ""
            }
        } else {
            if (this.editingColumnGroup) {
                if (this.selectedSubindex >=0  && this.outlookColumns[this.selectedIndex]["group"] === this.editingColumnGroup) {
                    //not changed
                    return
                }
            } else if (this.selectedSubindex < 0) {
                //not changed
                return
            }
            //group changed
            if (this.selectedSubindex >= 0) {
                //already in a group, remove it from old group
                this.outlookColumns[this.selectedIndex]["datasources"].splice(this.selectedSubindex,1)
                if (this.outlookColumns[this.selectedIndex]["datasources"].length === 0) {
                    //group is empty, remove it
                    var groupIndex = this.columnGroups.findIndex(function(o){return o === vm.outlookColumns[vm.selectedIndex]["group"]})
                    if (groupIndex >= 0) {
                        this.columnGroups.splice(groupIndex,1)
                    }
                    this.outlookColumns.splice(this.selectedIndex,1)
                } else {
                    this.selectedIndex += 1
                }
            } else {
                //not in a group, remove it from outlookColumns
                this.outlookColumns.splice(this.selectedIndex,1)
            }
            if (this.editingColumnGroup) {
                var groupIndex = this.outlookColumns.findIndex(function(o) {return o.group?o.group === vm.editingColumnGroup:false})
                if (groupIndex >= 0) {
                    //new  group already exist, add it into the existing group
                    this.outlookColumns[groupIndex]["datasources"].push(this.selectedColumn)
                    this.selectedIndex = groupIndex
                    this.selectedSubindex = this.outlookColumns[groupIndex]["datasources"].length - 1
                } else {
                    //group doesn't exist, add a new group
                    this.outlookColumns.splice(this.selectedIndex,0,{group:this.editingColumnGroup,datasources:[this.selectedColumn]})
                    this.selectedSubindex = 0
                    this.columnGroups.push(this.editingColumnGroup)
                    this.columnGroups.sort()
                }
            } else {
                //not in a group
                this.outlookColumns.splice(this.selectedIndex,0,this.selectedColumn)
                this.selectedSubindex = -1
                
            }
        }
        this.revision += 1

      },
      //toggle datasource
      //ds: the datasource
      //add: add if true else remove
      //index, subindex: used to improve performance during removing
      toggleDatasource:function(ds,add,index,subindex) {
        if (ds) {
            if (add === undefined || add === null) {
                ds["selected"] = !(ds["selected"] || false)
            } else {
                ds["selected"] = add
            }
        }
        var vm = this
        if (ds && ds["selected"]) {
            //add
            if (ds["options"] && ds["options"]["group"]) {
                //has default group
                group = ds["options"] && ds["options"]["group"]
                var groupIndex = this.outlookColumns.findIndex(function(o) {return o.group?o.group === group:false})
                if (groupIndex >= 0) {
                    //group already exist
                    this.outlookColumns[groupIndex]["required"] = this.outlookColumns[groupIndex]["required"] || (ds["required"] || false)
                    this.outlookColumns[groupIndex]["datasources"].push({workspace:ds["workspace"],id:ds["id"],name:ds["name"],required:ds["required"] || false})
                } else {
                    //group does not exist
                    this.outlookColumns.push({
                        group:group,
                        datasources:[{workspace:ds["workspace"],id:ds["id"],name:ds["name"],required:ds["required"] || false}]
                    })
                }
                groupIndex = this.columnGroups.findIndex(function(o) {return o === group})
                if (groupIndex < 0) {
                    this.columnGroups.push(group)
                    this.columnGroups.sort()
                }
            } else {
                //no default group
                this.outlookColumns.push({workspace:ds["workspace"],id:ds["id"],name:ds["name"],required:ds["required"] || false})
            }

        } else {
            //remove
            if (ds["required"]) {
                //required column, can't remove
                return
            }
            if (index === null || index === undefined) {
                $.each(this.outlookColumns,function(i,column){
                    if (column.group) {
                        j = column.datasources.findIndex(function(o){ return o["workspace"] === ds["workspace"] && o["id"] === ds["id"]})
                        if (j >= 0) {
                            index = i
                            subindex = j
                            return false
                        }
                    } else if (column["workspace"] === ds["workspace"] && column["id"] === ds["id"]){
                        index = i
                        subindex = -1
                        return false
                    }
                })
            }
            if (subindex >= 0) {
                this.outlookColumns[index]["datasources"].splice(subindex,1)
                if (this.selectedIndex === index && this.selectedSubindex === subindex) {
                    this.selectedIndex = -1
                    this.selectedSubindex = -1
                    this.selectedColumn = null
                    this.selectedRow = null
                    this.selectedDatasource = null
                    this.editingColumnTitle = ""
                    this.editingColumnGroup = ""
                } else if (this.selectedIndex === index && this.selectedSubindex > subindex) {
                    this.selectedSubindex -= 1
                }
                if (this.outlookColumns[index]["datasources"].length === 0) {
                    var groupIndex = this.columnGroups.findIndex(function(o){return o === vm.outlookColumns[index]["group"]})
                    if (groupIndex >= 0) {
                        this.columnGroups.splice(groupIndex,1)
                    }
                    this.outlookColumns.splice(index,1)
                    if (this.selectedIndex > index) {
                        this.selectedIndex -= 1
                    }
                }
            } else if (index >= 0) {
                this.outlookColumns.splice(index,1)
                if (this.selectedIndex === index) {
                    this.selectedIndex = -1
                    this.selectedSubindex = -1
                    this.selectedColumn = null
                    this.selectedRow = null
                    this.selectedDatasource = null
                    this.editingColumnTitle = ""
                    this.editingColumnGroup = ""
                } else if(this.selectedIndex > index) {
                    this.selectedIndex -= 1
                }
            }
        }
        this.systemsetting.saveState(10000)
        this.revision += 1
      },
      moveDown:function(index,subindex,column) {
        if (subindex >= 0) {
            if (index >= this.outlookColumns.length || index < 0) {
                return
            }
            if (subindex >= this.outlookColumns[index]["datasources"].length - 1 || subindex < 0) {
                return
            }
        } else {
            if (index >= this.outlookColumns.length - 1 || index < 0) {
                return
            }
        }
        if (subindex >= 0) {
            this.outlookColumns[index]["datasources"][subindex] = this.outlookColumns[index]["datasources"][subindex + 1]
            this.outlookColumns[index]["datasources"][subindex + 1] = column
            if (this.selectedSubindex === subindex ) {
                this.selectedSubindex += 1
            } else if (this.selectedSubindex === subindex - 1) {
                this.selectedSubindex -= 1
            }
        } else {
            this.outlookColumns[index] = this.outlookColumns[index + 1]
            this.outlookColumns[index + 1] = column
            if (this.selectedIndex === index ) {
                this.selectedIndex += 1
            } else if (this.selectedIndex === index - 1) {
                this.selectedIndex -= 1
            }
        }
     
        this.systemsetting.saveState(10000)
        this.revision += 1
      },
      moveUp:function(index,subindex,column) {
        if (subindex >= 0) {
            if (index >= this.outlookColumns.length || index < 0) {
                return
            }
            if (subindex >= this.outlookColumns[index]["datasources"].length || subindex <= 0) {
                return
            }
        } else {
            if (index >= this.outlookColumns.length || index <= 0) {
                return
            }
        }
        if (subindex >= 0) {
            this.outlookColumns[index]["datasources"][subindex] = this.outlookColumns[index]["datasources"][subindex - 1]
            this.outlookColumns[index]["datasources"][subindex - 1] = column
            if (this.selectedSubindex === subindex ) {
                this.selectedSubindex -= 1
            } else if (this.selectedSubindex === subindex - 1) {
                this.selectedSubindex += 1
            }
        } else {
            this.outlookColumns[index] = this.outlookColumns[index - 1]
            this.outlookColumns[index - 1] = column
            if (this.selectedIndex === index ) {
                this.selectedIndex -= 1
            } else if (this.selectedIndex === index - 1) {
                this.selectedIndex += 1
            }
        }
        this.systemsetting.saveState(10000)
        this.revision += 1
      },
      removeColumn:function(index,subindex,column) {
        var vm = this
        if (column.required) return
        if (column.group) {
            //remove group
            for(var subindex = column.datasources.length - 1;subindex >= 0;subindex--) {
                var datasource = vm._datasources["datasources"].find(function(o) {return column.datasources[subindex]["workspace"] === o["workspace"] && column.datasources[subindex]["id"] === o["id"]})
                vm.toggleDatasource(datasource,false,index,subindex)
            }
        } else {
            var datasource = this._datasources["datasources"].find(function(o) {return column["workspace"] === o["workspace"] && column["id"] === o["id"]})
            this.toggleDatasource(datasource,false,index,subindex)
        }
      },
      isDatasourceSelected:function(ds) {
        return this.revision && ds["selected"]
      },
      isShow:function(ds) {
        return ds["metadata"]["type"] != "Daily" || this.showDailyDatasources
      },
      formatReportHours(event) {
        if (event && event.type === "keyup" && event.keyCode !== 13) {  
            return
        }
        var hours = ""
        $.each(this.editingReportHours.split(','),function(index,hour) {
            hour = parseInt(hour.trim())
            if (!isNaN(hour) && hour >= 0 && hour < 24) {
                if (hours === "") {
                    hours = hour
                } else {
                    hours += "," + hour
                }
            }
        })
        this.editingReportHours = hours
        if (this.reportHours === hours) {
            return
        }
        this.reportHours = hours
        this.systemsetting.saveState(10000)
      },
      formatDailyTitle(event) {
        if (event && event.type === "keyup" && event.keyCode !== 13) {  
            return
        }
        if (event && this.editingDailyTitle === this.dailyTitle) {
            //not changed
            return
        }
        var result;
        var dailyData = {}
        var ds = null
        $("#daily-title").removeClass('alert')
        var varPattern = null
        var title = this.editingDailyTitle
        var rerun = true
        var unavailableVars = null
        while (rerun) {
            varPattern = /\{([^\}]+)\}/g
            rerun = false
            while(result = varPattern.exec(title || "")) {
                if (result[1] === "date") {
                } else if (!(ds = this._datasources["dailyDatasources"].find(function(ds){return ds["var"] === result[1]}))) {
                    if (unavailableVars === null) {
                        unavailableVars = result[1]
                    } else {
                        unavailableVars += " , " + result[1]
                    }
                    title = title.replace(result[0],"N/A")
                    rerun = true
                    break
                } else {
                    dailyData[result[1]] = {workspace:ds["workspace"],id:ds["id"]}
                }
            }
        }
        if (unavailableVars !== null) {
            $("#daily-title").addClass('alert')
            alert("The variables (" + unavailableVars + ") are unavailable");
        }
        this.dailyData = dailyData
        this.dailyTitle = title
        this.systemsetting.saveState(10000)
      },
      updateReportTimes:function() {
        this.reportTimes = []
        var vm = this
        if (this.reportType > 0) {
            var hour = 0;
            while (hour < 24) {
                if (hour % this.reportType === 0) {
                    if (hour < 10) {
                        this.reportTimes.push("0" + hour + ":00:00")
                    } else {
                        this.reportTimes.push(hour + ":00:00")
                    }
                }
                hour += 1
            }
        } else if (this.reportHours != null){
            var hours = this.reportHours + "";
            if (hours.length > 0) {
                $.each(hours.split(","),function(index,hour){
                    if (hour < 10) {
                        vm.reportTimes.push("0" + hour + ":00:00")
                    } else {
                        vm.reportTimes.push(hour + ":00:00")
                    }
                })
            }
        }
      },
      setOutlookColumns:function(columns) {
        var vm = this
        vm.outlookColumns = columns
        vm.columnGroups.length = 0
        var required = false
        $.each(vm._datasources["datasources"],function(index,ds){ds["selected"] = false})

        for(var index = vm.outlookColumns.length - 1;index >= 0;index--) {
            column = vm.outlookColumns[index]
            if (column.group){
                required = false
                for(var subindex = column.datasources.length - 1;subindex >= 0;subindex--) {
                    subcolumn = column.datasources[subindex]
                    var ds = vm._datasources["datasources"].find(function(o){return o["workspace"] === subcolumn["workspace"] && o["id"] === subcolumn["id"]})
                    if (ds) {
                        ds["selected"] = true
                        subcolumn["name"] = ds["name"]
                        subcolumn["required"] = ds["required"]?true:false
                        required = required || subcolumn["required"]
                    } else {
                        //column is unavailable
                        column.datasources.splice(subindex,1)
                    }
                }
                column["required"] = required
                var groupIndex = vm.columnGroups.findIndex(function(o){return o === column["group"]})
                if (column.datasources.length === 0) {
                    vm.outlookColumns.splice(index,1)
                    if (groupIndex >= 0) {
                        vm.columnGroups.splice(groupIndex,1)
                    }
                } else if(groupIndex < 0) {
                    vm.columnGroups.push(column["group"])
                    
                }
            } else {
                var ds = vm._datasources["datasources"].find(function(o){return o["workspace"] === column["workspace"] && o["id"] === column["id"]})
                if (ds) {
                    ds["selected"] = true
                    column["name"] = ds["name"]
                    column["required"] = ds["required"]?true:false
                } else {
                    //column is unavailable
                    vm.outlookColumns.splice(index,1)
                }

            }
        }
        //add required columns if not added before
        $.each(vm._datasources["datasources"],function(index,ds){
            if (ds["required"] && !ds["selected"]) {
                vm.toggleDatasource(ds,true) 
            }
        })
        this.columnGroups.sort()
        this.editingColumnTitle = ""
        this.editingColumnGroup = ""
        this.selectedRow = null
        this.selectedDatasource = null
        this.selectedIndex = -1
        this.selectedSubindex = -1
        this.selectedColumn = null
        this.revision += 1
      },
      loadDatasources:function() {
        var vm = this
        this._weatheroutlookStatus.phaseBegin("load_datasources",80,"Load datasources")
        this.refreshDatasources(true,function(){
            vm._weatheroutlookStatus.phaseEnd("load_datasources")
        },function(){
            vm._weatheroutlookStatus.phaseFailed("load_datasources","Failed to loading datasources. status = " + xhr.status + " , message = " + (xhr.responseText || message))
        })
      },
      refreshDatasources:function(refresh,callback,failedCallback) {
        var vm = this
        this._datasources = []
        $.ajax({
            url: vm.env.gokartService + "/outlookmetadata" + (refresh?"?refresh=true":""),
            method:"GET",
            dataType:"json",
            success: function (response, stat, xhr) {
                $.each(response["datasources"],function(index,datasource){
                    if (datasource["metadata"] && datasource["metadata"]["refresh_time"]) {
                        datasource["metadata"]["refresh_time"] = moment.tz(datasource["metadata"]["refresh_time"],"YYYY-MM-DD HH:mm:ss","Australia/Perth")
                    }
                })
                vm._datasources = {"datasources":response["datasources"],"dailyDatasources":[]}
                $.each(vm._datasources["datasources"],function(index,ds){
                    if (ds["var"] && ds["metadata"]["type"] === "Daily") {
                        vm._datasources["dailyDatasources"].push(ds)
                    }
                })
                var columns = vm.outlookColumns
                vm.outlookColumns = null
                vm.formatDailyTitle()
                vm.revision += 1
                vm.$nextTick(function(){vm.setOutlookColumns(columns)})
                if (callback) {callback()}
            },
            error: function (xhr,status,message) {
                alert(xhr.status + " : " + (xhr.responseText || message))
                if (failedCallback) {failedCallback()}
            },
            xhrFields: {
              withCredentials: true
            }
        })
      },
      setPosition:function(coordinate) {
        this._features.clear()
        this._features.push(new ol.Feature({geometry:new ol.geom.Point(coordinate)}))
      },
      getWeatherOutlook:function(coordinate) {
        if (this.reportTimes.length === 0) {
            alert("No weather outlook times are configured in settings module")
            return
        }
        if (!this.outlookColumns || this.outlookColumns.length === 0) {
            this.setOutlookColumns(JSON.parse(JSON.stringify(this._defaultOutlookColumns)))
            this.systemsetting.saveState()
        }
        var vm = this
        var _getWeatherOutlook = function(position) {
            var requestData = null;
            var format = vm.format
            if (vm.outlookSetting.name === "weather-outlook-default") {
                requestData = {
                    point:coordinate,
                    options: {
                        title:"4 Day Weather Outlook for " + position + "(" + Math.round(coordinate[0] * 10000) / 10000 + "," + Math.round(coordinate[1] * 10000) / 10000 + ")",
                    },
                    outlooks:[
                        {
                            days:utils.getDatetimes(["00:00:00"],4,1).map(function(dt) {return dt.format("YYYY-MM-DD")}),
                            times:["09:00:00","12:00:00","15:00:00","18:00:00"],
                            options:{
                                daily_title_pattern: "{date} {weather}"
                            },
                            daily_data:{"weather":{"workspace":"bom","id":"IDW71152_WA_DailyWxIcon_SFC_DESC"}},
                            times_data:vm._defaultOutlookColumns,
                        }
                    ]
                }
            } else if (vm.outlookSetting.name === "weather-outlook-amicus") {
                requestData = {
                    point:coordinate,
                    options: {
                        title:"2 Day Weather Outlook for " + position + "(" + Math.round(coordinate[0] * 10000) / 10000 + "," + Math.round(coordinate[1] * 10000) / 10000 + ")",
                        position:position,
                        latitude:Math.round(coordinate[1] * 10000) / 10000,
                        longitude:Math.round(coordinate[0] * 10000) / 10000
                    },
                    outlooks:[
                        {
                            days:utils.getDatetimes(["00:00:00"],2,1).map(function(dt) {return dt.format("YYYY-MM-DD")}),
                            times:["00:00:00","01:00:00","02:00:00","03:00:00","04:00:00","05:00:00","06:00:00","07:00:00","08:00:00","09:00:00","10:00:00","11:00:00","12:00:00","13:00:00","14:00:00","15:00:00","16:00:00","17:00:00","18:00:00","19:00:00","20:00:00","21:00:00","22:00:00","23:00:00"],
                            options:{
                                expired:1 //unit:hour, the exipre time of each outlook in times
                            },
                            times_data:vm._amicusOutlookColumns,
                        }
                    ]
                }
                format = "amicus"
            } else {
                requestData = {
                    point:coordinate,
                    options: {
                        title:vm.outlookDays + " Day Weather Outlook for " + position + "(" + Math.round(coordinate[0] * 10000) / 10000 + "," + Math.round(coordinate[1] * 10000) / 10000 + ")",
                    },
                    outlooks:[
                        {
                            days:utils.getDatetimes(["00:00:00"],parseInt(vm.outlookDays),1).map(function(dt) {return dt.format("YYYY-MM-DD")}),
                            times:vm.reportTimes,
                            options:{
                                daily_title_pattern: vm.dailyTitle || "{date}"
                            },
                            daily_data:vm.dailyData||{},
                            times_data:vm.outlookColumns,
                        }
                    ]
                }
            }
            if (format === "html") {
                $("#weatheroutlook_data").val(JSON.stringify(requestData))
                utils.submitForm("get_weatheroutlook",{width: (screen.width > 1890)?1890:screen.width, height:(screen.height > 1060)?1060:screen.height},true)
            } else {
                try{
                    var req = new window.XMLHttpRequest()
                    req.open('POST', vm.env.gokartService + "/weatheroutlook/" + format)
                    req.responseType = 'blob'
                    req.withCredentials = true
                    req.onload = function (event) {
                        try{
                            if (req.status >= 400) {
                                var reader = new FileReader()
                                reader.addEventListener("loadend",function(e){
                                    alert(e.target.result)
                                })
                                reader.readAsText(req.response)
                            } else {
                                var filename = null
                                if (req.getResponseHeader("Content-Disposition")) {
                                    var matches = vm._filename_re.exec(req.getResponseHeader("Content-Disposition"))
                                    filename = (matches && matches[1])? matches[1]: null
                                }
                                if (!filename) {
                                    filename = "weather_outlook_" + moment().format("YYYYMMDD_HHmm") + "." + format ;
                                }
                                saveAs(req.response, filename)
                            }
                        } catch(ex) {
                            alert(ex.message || ex)
                        }
                    }
                    var formData = new window.FormData()
                    formData.append('data', JSON.stringify(requestData))
                    req.send(formData)
                }catch(ex) {
                    callback(false,ex.message || ex)
                }
            }
        }

        this.map.getPosition(coordinate,_getWeatherOutlook)
        
      },
    },
    ready: function () {
      var vm = this
      this._filename_re = new RegExp("filename=[\'\"](.+)[\'\"]")
      this._weatheroutlookStatus = vm.loading.register("weatheroutlook","BOM Spot Outlook Component")

      this._weatheroutlookStatus.phaseBegin("initialize",20,"Initialize")
      this.outlookSetting = this.outlookSettings[0]
      
      if (!vm.$root.toolbox.inToolbox(vm)) {
          vm.map.mapControls["weatheroutlook"] = {
              enabled:false,
            autoenable:false,
            controls:vm.mapControl
        }
      }

      this.editingReportHours = this.reportHours
      this.editingDailyTitle = this.dailyTitle

      this._defaultOutlookColumns = [
          {
              workspace:"bom",
              id:"IDW71034_WA_WxIcon_SFC_ICON",
          },
          {
              workspace:"bom",
              id:"IDW71000_WA_T_SFC",
          },
          {
              workspace:"bom",
              id:"IDW71001_WA_Td_SFC",
          },
          {
              workspace:"bom",
              id:"IDW71018_WA_RH_SFC",
          },
          {
              group:"10m Wind",
              datasources:[
                  {
                      workspace:"bom",
                      id:"IDW71089_WA_Wind_Dir_SFC",
                  },
                  {
                      workspace:"bom",
                      id:"IDW71071_WA_WindMagKmh_SFC",
                  },
                  {
                      workspace:"bom",
                      id:"IDW71072_WA_WindGustKmh_SFC",
                  }
              ]
          },
          {
              workspace:"bom",
              id:"IDW71127_WA_DF_SFC",
          },
          {
              workspace:"bom",
              id:"IDW71139_WA_Curing_SFC",
          },
          {
              workspace:"bom",
              id:"IDW71117_WA_FFDI_SFC",
          },
          {
              workspace:"bom",
              id:"IDW71122_WA_GFDI_SFC",
          },
      ]

      this._amicusOutlookColumns = [
          {
              workspace:"bom",
              id:"IDW71000_WA_T_SFC",
          },
          {
              workspace:"bom",
              id:"IDW71001_WA_Td_SFC",
          },
          {
              workspace:"bom",
              id:"IDW71018_WA_RH_SFC",
          },
          {
              workspace:"bom",
              id:"IDW71089_WA_Wind_Dir_SFC",
          },
          {
              workspace:"bom",
              id:"IDW71071_WA_WindMagKmh_SFC",
          },
          {
              workspace:"bom",
              id:"IDW71072_WA_WindGustKmh_SFC",
          },
          {
              workspace:"bom",
              id:"IDW71110_WA_WindMagKmh_1500mAMSL",
          },
          {
              workspace:"bom",
              id:"IDW71117_WA_FFDI_SFC",
          },
          {
              workspace:"bom",
              id:"IDW71122_WA_GFDI_SFC",
          },
      ]

      this.outlookColumns = (this.outlookColumns && this.outlookColumns.length > 0)?this.outlookColumns:JSON.parse(JSON.stringify(this._defaultOutlookColumns))

      this.loadDatasources()

      var map = this.$root.map

      this._features = new ol.Collection()
      this._features.on("add",function(event){
        vm.getWeatherOutlook(event.element.getGeometry().getCoordinates())
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
      var weatheroutlookInter = new ol.interaction.Draw({
          source: this._source,
          type: 'Point',
          style: this._style
      });

      weatheroutlookInter.on('drawend',function(){
        vm._features.clear()
      }, this)

      this._weatheroutlookTool = {
        name: 'WeatherOutlook',
        keepSelection:true,
        interactions:[
            weatheroutlookInter
        ]
      }

      this.annotations.tools.push(this._weatheroutlookTool)

      this.updateReportTimes()

      this.adjustHeight()

      this.changeOutlookDays()

      this._weatheroutlookStatus.phaseEnd("initialize")

    }
  }
</script>
