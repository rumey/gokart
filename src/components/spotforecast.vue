<template>
  <div class="tabs-panel" id="spotforecast" v-cloak>
    <div class="row">
      <div class="columns">
        <div class="tabs-content vertical" data-tabs-content="setting-tabs">
          <div id="spotforecast-settings">

            <div class="tool-slice row collapse">
                <div class="small-4">
                    <label class="tool-label">Forecast Days:</label>
                </div>
                <div class="small-8">
                    <select name="spotforecastForecastDays" v-model="forecastDays" @change="systemsetting.saveState(10000)">
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
                    <label class="tool-label">Forecast Times:</label>
                </div>
                <div class="small-8">
                    <select name="spotforecastReportType" v-model="reportType" @change="systemsetting.saveState(10000)">
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

          <div class="tool-slice row collapse" id="spotforecast-data-config">
            <div class="columns">
                <ul class="accordion" data-accordion>
                    <li class="accordion-item" data-accordion-item>
                        <!-- Accordion tab title -->
                        <a href="#" class="accordion-title">Daily Title</a>
                        <!-- Accordion tab content: it would start in the open state due to using the `is-active` state class. -->
                        <div class="accordion-content scroller" data-tab-content id="spotforecast-header">
                            <textarea type="text" rows="4" style="width:100%;resize:vertical" id="daily-title" v-model="editingDailyTitle" placeholder="{date}" @blur="formatDailyTitle" @keyup="formatDailyTitle"> </textarea>
                            <div class="row feature-row status-row">
                                <div class="small-4">
                                    <div class="forecast-datasources">date</div>
                                </div>
                                <div class="small-8">
                                    <div class="forecast-datasources">forecast date</div>
                                </div>
                            </div>
                            <div v-for="ds in dailyDatasources" track-by="id" class="row feature-row status-row" >
                                <div class="small-4">
                                    <div class="forecast-datasources">{{ ds.var}} </div>
                                </div>
                                <div class="small-8">
                                    <div class="forecast-datasources">{{ ds.name}}</div>
                                </div>
                            </div>
                        </div>
                    </li>
                    <li class="accordion-item is-active" data-accordion-item>
                        <!-- Accordion tab title -->
                        <a href="#" class="accordion-title">Chosen Columns</a>
                        <!-- Accordion tab content: it would start in the open state due to using the `is-active` state class. -->
                        <div class="accordion-content" data-tab-content>
                            <div class="scroller" id="spotforecast-columns" style="margin-left:-16px;margin-right:-16px">
                            <div style="margin-left:16px;margin-right:16px">
                                <template v-for="(index,column) in (revision && forecastColumns)" track-by="$index" >
                                    <template v-if="column.group">
                                    <div class='row feature-row {{column===selectedColumn?"feature-selected":""}}' @click="selectColumn(index,-1,column)" id="active-column-{{index}}">
                                        <div class="small-12">
                                            {{ column.group}}
                                            <div class="text-right float-right">
                                                <a v-bind:disabled="index <= 0" @click.stop.prevent="moveUp(index,-1,column)" title="Move Up" class="button tiny secondary">
                                                    <i class="fa fa-arrow-up"></i>
                                                </a>
                                                <a v-bind:disabled="index >= forecastColumns.length - 1" @click.stop.prevent="moveDown(index,-1,column)" title="Move Down" class="button tiny secondary">
                                                    <i class="fa fa-arrow-down"></i>
                                                </a>
                                                <a @click.stop.prevent="removeColumn(index,-1,column)" class="button tiny secondary alert" title="Remove"><i class="fa fa-close"></i></a>
                                            </div>
                                        </div>
                                    </div>
                                    <div v-for="(subindex,subcolumn) in revision && column.datasources" track-by="id" class='row feature-row {{subcolumn===selectedColumn?"feature-selected":""}}'
                                        @click.stop.prevent="selectColumn(index,subindex,subcolumn)" id=active-column-{{index}}-{{subindex}} style="margin-left:0px;">
                                        <div class="small-12">
                                            {{ subcolumn.name}}
                                            <div class="text-right float-right">
                                                <a v-bind:disabled="subindex <= 0" @click.stop.prevent="moveUp(index,subindex,subcolumn)" title="Move Up" class="button tiny secondary">
                                                    <i class="fa fa-arrow-up"></i>
                                                </a>
                                                <a v-bind:disabled="subindex >= column.datasources.length - 1" 
                                                    @click.stop.prevent="moveDown(index,subindex,subcolumn)" title="Move Down" class="button tiny secondary">
                                                    <i class="fa fa-arrow-down"></i>
                                                </a>
                                                <a @click.stop.prevent="removeColumn(index,subindex,subcolumn)" class="button tiny secondary alert" title="Remove"><i class="fa fa-close"></i></a>
                                            </div>
                                        </div>
                                    </div>
                                    </template>
                                    <template v-if="column.id">
                                    <div class='row feature-row {{column===selectedColumn?"feature-selected":""}}' @click="selectColumn(index,-1,column)" id="active-column-{{index}}">
                                        <div class="small-12">
                                            {{ column.name}}
                                            <div class="text-right float-right">
                                                <a v-bind:disabled="index <= 0" @click.stop.prevent="moveUp(index,-1,column)" title="Move Up" class="button tiny secondary">
                                                    <i class="fa fa-arrow-up"></i>
                                                </a>
                                                <a v-bind:disabled="index >= forecastColumns.length - 1" @click.stop.prevent="moveDown(index,-1,column)" title="Move Down" class="button tiny secondary">
                                                    <i class="fa fa-arrow-down"></i>
                                                </a>
                                                <a @click.stop.prevent="removeColumn(index,-1,column)" class="button tiny secondary alert" title="Remove"><i class="fa fa-close"></i></a>
                                            </div>
                                        </div>
                                    </div>
                                    </template>
                                </template>
                            </div>
                            </div>

                            <div class="row" id="spotforecast-column-editor" style="margin-left:-10px;margin-right:-10px" >
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
                        <div class="accordion-content scroller" data-tab-content id="spotforecast-datasources">

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
                                           <input class="switch-input ctlgsw" id="forecast_ds_{{ $index }}"  type="checkbox" @change="toggleDatasource(ds)" v-bind:checked="isDatasourceSelected(ds)"/>
                                           <label class="switch-paddle" for="forecast_ds_{{ $index }}">
                                               <span class="show-for-sr">Toggle</span>
                                           </label>
                                        </div>
                                    </div>
                                </div>
                                <div class="small-6 datasource-desc">
                                    <div class="forecast-datasources">Type: {{ ds.metadata.type }}</div>
                                </div>
                                <div class="small-6 datasource-desc">
                                    <div class="forecast-datasources" v-if="isDegreeUnit(ds)">Unit: &deg;
                                    </div>
                                    <div class="forecast-datasources" v-if="ds.metadata.unit && !isDegreeUnit(ds)">Unit: {{ ds.metadata.unit}}
                                    </div>
                                </div>
                                <div class="small-12 datasource-desc">
                                    <div class="forecast-datasources">Title: {{ ds.options.title }}</div>
                                </div>
                                <div class="small-12 datasource-desc">
                                    <div class="forecast-datasources">Updated: {{ ds.metadata.refresh_time?ds.metadata.refresh_time.toLocaleString():"" }}</div>
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
    <div id="spotforecast_control" class="ol-selectable ol-control">
        <button type="button" title="{{settingTitle()}}" @click="toggleSpotForecast()" v-bind:class="{'selected':isControlSelected}" style="height:36px;border-bottom-left-radius:0px;border-bottom-right-radius:0px">
            <img v-bind:src="forecastSetting.icon" width="36" height="36">
        </button>
        <button type="button" style="height:16px;border-top-left-radius:0px;border-top-right-radius:0px"  @click="showSettings=!showSettings" >
            <i class="fa fa-angle-double-down" aria-hidden="true"></i>
        </button>
        <div v-show="showSettings" style="position:absolute;width:300px;right:0px">
            <button type="button" v-for="s in forecastSettings" title="{{settingTitle(s)}}"  style="margin:1px;float:right" track-by="$index" @click.stop.prevent="selectSetting(s)">
                <img v-bind:src="s.icon" width="36" height="36">
            </button>
        </div>
    </div>
    </div>

    <form id="get_spotforecast" name="spotforecast" action="{{env.gokartService + '/spotforecast/html'}}" method="post" target="spotforecast">
        <input type="hidden" name="data" id="spotforecast_data">
    </form>
  </div>
</template>

<style>
.datasource-desc {
    font-style:italic;
    padding-left:24px;
    color:#6dd8ef;
    font-size:14px;
}

#spotforecast-data-config .accordion {
    background-color: transparent
}
#spotforecast-data-config .accordion-content {
    background-color: transparent
}
#daily-title.alert{
    background-color: rgba(171, 116, 107, 0.7);
}
.forecast-datasources {
    font-size: 100%;
}
#spotforecast_control .selected{
    background-color: #2199E8;
}
#spotforecast_control {
    position: absolute;
    top: 180px;
    left: auto;
    right: 16px;
    bottom: auto;
    padding: 0;
}

</style>

<script>
  import { ol,$,moment,utils} from 'src/vendor.js'
  export default {
    store: {
        reportType:'settings.spotforecast.reportType',
        reportHours:'settings.spotforecast.reportHours',
        dailyTitle:'settings.spotforecast.dailyTitle',
        forecastDays:'settings.spotforecast.forecastDays',
        forecastColumns:'settings.spotforecast.forecastColumns',
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
        forecastSetting:{},
        forecastSettings:[
            {name:"default",title:"Default outlook forecast",icon:"/dist/static/images/default-outlook-forecast.svg"},
            {name:"customized",title:"Customized outlook forecast",icon:"/dist/static/images/customized-outlook-forecast.svg"}
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
                element: $('#spotforecast_control').get(0),
        	target: $('#external-controls').get(0)
            })
        }
        return this._controller
      },
      isControlSelected:function() {
        if (this.annotations) {
            return this.annotations.tool === this._spotforecastTool
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
        if (!this.showSettings) {
            return 52
        } else {
            return 52 + Math.ceil(this.forecastSettings.length / 6) * 50
        }
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
    },
    // methods callable from inside the template
    methods: {
      adjustHeight:function() {
        if (this.activeMenu === "settings" && this.activeSubmenu === "spotforecast") {
            //the 'chosen columns' is selected by default, so the first time when the user entries into the sportforecast setting panel, the 'column editor' should have valid height value.
            this._columnEditorHeight = this._columnEditorHeight || $("#spotforecast-column-editor").height()
            var height = this.screenHeight - this.leftPanelHeadHeight - $("#spotforecast-settings").height() - 200
            $("#spotforecast-header").height(height)
            $("#spotforecast-columns").height(height - this._columnEditorHeight)
            $("#spotforecast-datasources").height(height)
        }
      },
      settingTitle: function(s){
        s = s || this.forecastSetting
        return (s.name === "default")?"Default 4 Day Outlook":(this.forecastDays + " Day Outlook")
      },
      selectSetting:function(s) {
        this.showSettings = false
        if (this.forecastSetting === s) {
            return
        }
        this.forecastSetting = s
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
            this.editingColumnGroup = subindex >= 0 ?this.forecastColumns[index]["group"]:""
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
                groupIndex = this.forecastColumns.findIndex(function(o) {return o.group?o.group === vm.editingColumnGroup:false})
                if (groupIndex >= 0) {
                    //group already exist,move the columns to existing groups
                    this.forecastColumns[groupIndex].datasources.push.apply(this.forecastColumns[groupIndex].datasources,this.selectedColumn.datasources)
                    //remove the old group
                    this.forecastColumns.splice(this.selectedIndex,1)
                    if (this.selectedIndex < groupIndex) {
                        this.selectedIndex = groupIndex - 1
                    } else {
                        this.selectedIndex = groupIndex
                    }
                    this.selectedIndex = groupIndex
                    this.selectedSubindex = -1
                    this.selectedColumn = this.forecastColumns[groupIndex]
                    this.selectedRow = null
                    this.selectedDatasource = null
                    this.editingColumnTitle = ""

                } else {
                    //group does not exist, rename the group
                    this.forecastColumns[vm.selectedIndex]["group"] = this.editingColumnGroup
                    this.columnGroups.push(this.editingColumnGroup)
                    this.columnGroups.sort()
                }
                

            } else {
                //remove group
                this.forecastColumns.splice(this.selectedIndex,1)
                $.each(this.selectedColumn.datasources,function(index,col){
                    vm.forecastColumns.splice(vm.selectedIndex + index,0,col)
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
                if (this.selectedSubindex >=0  && this.forecastColumns[this.selectedIndex]["group"] === this.editingColumnGroup) {
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
                this.forecastColumns[this.selectedIndex]["datasources"].splice(this.selectedSubindex,1)
                if (this.forecastColumns[this.selectedIndex]["datasources"].length === 0) {
                    //group is empty, remove it
                    var groupIndex = this.columnGroups.findIndex(function(o){return o === vm.forecastColumns[vm.selectedIndex]["group"]})
                    if (groupIndex >= 0) {
                        this.columnGroups.splice(groupIndex,1)
                    }
                    this.forecastColumns.splice(this.selectedIndex,1)
                } else {
                    this.selectedIndex += 1
                }
            } else {
                //not in a group, remove it from forecastColumns
                this.forecastColumns.splice(this.selectedIndex,1)
            }
            if (this.editingColumnGroup) {
                var groupIndex = this.forecastColumns.findIndex(function(o) {return o.group?o.group === vm.editingColumnGroup:false})
                if (groupIndex >= 0) {
                    //new  group already exist, add it into the existing group
                    this.forecastColumns[groupIndex]["datasources"].push(this.selectedColumn)
                    this.selectedIndex = groupIndex
                    this.selectedSubindex = this.forecastColumns[groupIndex]["datasources"].length - 1
                } else {
                    //group doesn't exist, add a new group
                    this.forecastColumns.splice(this.selectedIndex,0,{group:this.editingColumnGroup,datasources:[this.selectedColumn]})
                    this.selectedSubindex = 0
                    this.columnGroups.push(this.editingColumnGroup)
                    this.columnGroups.sort()
                }
            } else {
                //not in a group
                this.forecastColumns.splice(this.selectedIndex,0,this.selectedColumn)
                this.selectedSubindex = -1
                
            }
        }
        this.revision += 1

      },
      toggleSpotForecast: function () {
        if (!this._spotforecastTool || this.annotations.tool === this._spotforecastTool) {
            this.annotations.setTool(this.annotations.currentTool,true)
        } else  {
            this.annotations.setTool(this._spotforecastTool)
        }
      },
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
                var groupIndex = this.forecastColumns.findIndex(function(o) {return o.group?o.group === group:false})
                if (groupIndex >= 0) {
                    //group already exist
                    this.forecastColumns[groupIndex]["datasources"].push({workspace:ds["workspace"],id:ds["id"],name:ds["name"]})
                } else {
                    //group does not exist
                    this.forecastColumns.push({group:group,datasources:[{workspace:ds["workspace"],id:ds["id"],name:ds["name"]}]})
                }
                groupIndex = this.columnGroups.findIndex(function(o) {return o === group})
                if (groupIndex < 0) {
                    this.columnGroups.push(group)
                    this.columnGroups.sort()
                }
            } else {
                //no default group
                this.forecastColumns.push({workspace:ds["workspace"],id:ds["id"],name:ds["name"]})
            }

        } else {
            //remove
            if (index === null || index === undefined) {
                $.each(this.forecastColumns,function(i,column){
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
                this.forecastColumns[index]["datasources"].splice(subindex,1)
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
                if (this.forecastColumns[index]["datasources"].length === 0) {
                    var groupIndex = this.columnGroups.findIndex(function(o){return o === vm.forecastColumns[index]["group"]})
                    if (groupIndex >= 0) {
                        this.columnGroups.splice(groupIndex,1)
                    }
                    this.forecastColumns.splice(index,1)
                    if (this.selectedIndex > index) {
                        this.selectedIndex -= 1
                    }
                }
            } else if (index >= 0) {
                this.forecastColumns.splice(index,1)
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
            if (index >= this.forecastColumns.length || index < 0) {
                return
            }
            if (subindex >= this.forecastColumns[index]["datasources"].length - 1 || subindex < 0) {
                return
            }
        } else {
            if (index >= this.forecastColumns.length - 1 || index < 0) {
                return
            }
        }
        if (subindex >= 0) {
            this.forecastColumns[index]["datasources"][subindex] = this.forecastColumns[index]["datasources"][subindex + 1]
            this.forecastColumns[index]["datasources"][subindex + 1] = column
            if (this.selectedSubindex === subindex ) {
                this.selectedSubindex += 1
            } else if (this.selectedSubindex === subindex - 1) {
                this.selectedSubindex -= 1
            }
        } else {
            this.forecastColumns[index] = this.forecastColumns[index + 1]
            this.forecastColumns[index + 1] = column
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
            if (index >= this.forecastColumns.length || index < 0) {
                return
            }
            if (subindex >= this.forecastColumns[index]["datasources"].length || subindex <= 0) {
                return
            }
        } else {
            if (index >= this.forecastColumns.length || index <= 0) {
                return
            }
        }
        if (subindex >= 0) {
            this.forecastColumns[index]["datasources"][subindex] = this.forecastColumns[index]["datasources"][subindex - 1]
            this.forecastColumns[index]["datasources"][subindex - 1] = column
            if (this.selectedSubindex === subindex ) {
                this.selectedSubindex -= 1
            } else if (this.selectedSubindex === subindex - 1) {
                this.selectedSubindex += 1
            }
        } else {
            this.forecastColumns[index] = this.forecastColumns[index - 1]
            this.forecastColumns[index - 1] = column
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
      setForecastColumns:function(columns) {
        var vm = this
        vm.forecastColumns = columns
        vm.columnGroups.length = 0
        $.each(vm._datasources["datasources"],function(index,ds){ds["selected"] = false})

        for(var index = vm.forecastColumns.length - 1;index >= 0;index--) {
            column = vm.forecastColumns[index]
            if (column.group){
                for(var subindex = column.datasources.length - 1;subindex >= 0;subindex--) {
                    subcolumn = column.datasources[subindex]
                    var ds = vm._datasources["datasources"].find(function(o){return o["workspace"] === subcolumn["workspace"] && o["id"] === subcolumn["id"]})
                    if (ds) {
                        ds["selected"] = true
                        subcolumn["name"] = ds["name"]
                    } else {
                        //column is unavailable
                        column.datasources.splice(subindex,1)
                    }
                }
                var groupIndex = vm.columnGroups.findIndex(function(o){return o === column["group"]})
                if (column.datasources.length === 0) {
                    vm.forecastColumns.splice(index,1)
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
                } else {
                    //column is unavailable
                    vm.forecastColumns.splice(index,1)
                }

            }
        }
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
        this._spotforecastStatus.phaseBegin("load_datasources",80,"Load datasources")
        this.refreshDatasources(true,function(){
            vm._spotforecastStatus.phaseEnd("load_datasources")
        },function(){
            vm._spotforecastStatus.phaseFailed("load_datasources","Failed to loading datasources. status = " + xhr.status + " , message = " + (xhr.responseText || message))
        })
      },
      refreshDatasources:function(refresh,callback,failedCallback) {
        var vm = this
        this._datasources = []
        $.ajax({
            url: vm.env.gokartService + "/forecastmetadata" + (refresh?"?refresh=true":""),
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
                var columns = vm.forecastColumns
                vm.forecastColumns = null
                vm.formatDailyTitle()
                vm.revision += 1
                vm.$nextTick(function(){vm.setForecastColumns(columns)})
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
      setSpot:function(coordinate) {
        this._features.clear()
        this._features.push(new ol.Feature({geometry:new ol.geom.Point(coordinate)}))
      },
      getSpotforecast:function(coordinate) {
        if (this.reportTimes.length === 0) {
            alert("No spot forecast report times are configured in settings module")
            return
        }
        if (!this.forecastColumns || this.forecastColumns.length === 0) {
            this.setForecastColumns(JSON.parse(JSON.stringify(this._defaultForecastColumns)))
            this.systemsetting.saveState()
        }
        var vm = this
        var _getSpotforecast = function(position) {
            var requestData = null;
            if (vm.forecastSetting.name === "default") {
                requestData = {
                    point:coordinate,
                    options: {
                        title:"<h3>Spot Fire Weather 4 Day Outlook for " + position + "(" + Math.round(coordinate[0] * 10000) / 10000 + "," + Math.round(coordinate[1] * 10000) / 10000 + ")</h3>",
                    },
                    forecasts:[
                        {
                            days:utils.getDatetimes(["00:00:00"],4,1).map(function(dt) {return dt.format("YYYY-MM-DD")}),
                            times:["09:00:00","15:00:00"],
                            options:{
                                daily_title_pattern: "{date} {weather}"
                            },
                            daily_data:{"weather":{"workspace":"bom","id":"IDW71152_WA_DailyWxIcon_SFC_DESC"}},
                            times_data:vm._defaultForecastColumns,
                        }
                    ]
                }
            } else {
                requestData = {
                    point:coordinate,
                    options: {
                        title:"<h3>Spot Fire Weather " + vm.forecastDays + " Day Outlook for " + position + "(" + Math.round(coordinate[0] * 10000) / 10000 + "," + Math.round(coordinate[1] * 10000) / 10000 + ")</h3>",
                    },
                    forecasts:[
                        {
                            days:utils.getDatetimes(["00:00:00"],parseInt(vm.forecastDays),1).map(function(dt) {return dt.format("YYYY-MM-DD")}),
                            times:vm.reportTimes,
                            options:{
                                daily_title_pattern: vm.dailyTitle || "{date}"
                            },
                            daily_data:vm.dailyData||{},
                            times_data:vm.forecastColumns,
                        }
                    ]
                }
            }
            if (vm.format === "json") {
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
                utils.submitForm("get_spotforecast",{width: (screen.width > 1890)?1890:screen.width, height:(screen.height > 1060)?1060:screen.height})
            }
        }

        this.map.getPosition(coordinate,_getSpotforecast)
        
      },
    },
    ready: function () {
      var vm = this
      this._spotforecastStatus = vm.loading.register("spotforecast","BOM Spot Forecast Component")

      this._spotforecastStatus.phaseBegin("initialize",20,"Initialize")
      this.forecastSetting = this.forecastSettings[0]
      
      vm.map.mapControls["spotforecast"] = {
          enabled:false,
          autoenable:false,
          controls:vm.mapControl
      }

      this.editingReportHours = this.reportHours
      this.editingDailyTitle = this.dailyTitle

      this._defaultForecastColumns = [
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

      this.forecastColumns = (this.forecastColumns && this.forecastColumns.length > 0)?this.forecastColumns:JSON.parse(JSON.stringify(this._defaultForecastColumns))

      this.loadDatasources()

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
        keepSelection:true,
        interactions:[
            spotforecastInter
        ]
      }

      this.annotations.tools.push(this._spotforecastTool)

      this.updateReportTimes()

      this.adjustHeight()

      this._spotforecastStatus.phaseEnd("initialize")

    }
  }
</script>
