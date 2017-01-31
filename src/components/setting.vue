<template>
  <div class="tabs-panel" id="menu-tab-setting" v-cloak>
    <div class="row collapse">
      <div class="columns">
        <ul class="tabs" id="setting-tabs">
          <li class="tabs-title is-active"><a class="label" aria-selected="true">System Settings</a></li>
        </ul>
      </div>
    </div>
    <div class="row collapse" id="setting-tab-panels">
      <div class="columns">
        <div class="tabs-content vertical" data-tabs-content="setting-tabs">
          <div class="tabs-panel is-active" id="system-settings" v-cloak>

            <div class="tool-slice row collapse">
              <div class="switch tiny">
                <input class="switch-input" id="toggleGraticule" type="checkbox"  v-bind:checked="graticule" @change="toggleGraticule"/>
                <label class="switch-paddle" for="toggleGraticule">
                    <span class="show-for-sr">Display graticule</span>
                </label>
              </div>
              <label for="toggleGraticule" class="side-label">Display graticule</label>
            </div>

            <div class="tool-slice row collapse">
              <div class="switch tiny">
                <input class="switch-input" id="toggleOverviewMap" type="checkbox"  v-bind:checked="overviewMap" @change="toggleOverviewMap"/>
                <label class="switch-paddle" for="toggleOverviewMap">
                    <span class="show-for-sr">Show overview map</span>
                </label>
              </div>
              <label for="toggleOverviewMap" class="side-label">Show overview map</label>
            </div>

            <div class="tool-slice row collapse">
              <div class="switch tiny">
                <input class="switch-input" id="toggleHoverInfo" type="checkbox" v-bind:checked="hoverInfo" @change="toggleHoverInfo" />
                <label class="switch-paddle" for="toggleHoverInfo">
                  <span class="show-for-sr">Display hovering feature info</span>
                </label>
              </div>
              <label for="toggleHoverInfo" class="side-label">Display hovering feature info</label>
            </div>

            <div class="tool-slice row collapse">
              <div class="switch tiny">
                <input class="switch-input" id="toggleRightHandTools" type="checkbox" v-bind:checked="rightHandTools" @change="toggleRightHandTools" />
                <label class="switch-paddle" for="toggleRightHandTools">
                  <span class="show-for-sr">Show right hand tools</span>
                </label>
              </div>
              <label for="toggleRightHandTools" class="side-label">Show right hand tools</label>
            </div>

            <div class="tool-slice row collapse">
              <div class="switch tiny">
                <input class="switch-input" id="toggleMeasureAnnotation" type="checkbox" v-bind:checked="measureAnnotation" @change="toggleMeasureAnnotation"/>
                <label class="switch-paddle" for="toggleMeasureAnnotation">
                  <span class="show-for-sr">Measure annotation</span>
                </label>
              </div>
              <label for="toggleMeasureAnnotation" class="side-label">Measure annotation</label>
            </div>

            <div class="tool-slice row collapse">
                <div class="small-4">
                    <label class="tool-label">Distance unit:</label>
                </div>
                <div class="small-8">
                    <select name="lengthUnit" v-model="lengthUnit" @change="saveState()">
                        <option value="nm">Nautical Mile</option>      
                        <option value="mile">Mile</option>      
                        <option value="km">Kilometer</option>      
                    </select>
                </div>
            </div>

            <div class="tool-slice row collapse">
                <div class="small-4">
                    <label class="tool-label">Area unit:</label>
                </div>
                <div class="small-8">
                    <select name="areaUnit" v-model="areaUnit" @change="saveState()">
                        <option value="ha">Hectare</option>      
                        <option value="km2">km<sup>2</sup></option>      
                    </select>
                </div>
            </div>

            <div class="tool-slice row collapse">
              <div class="columns small-4"><label class="tool-label">Undo limit:<br/>{{ undoLimitDesc }}</label></div>
              <div class="columns small-7"><input class="layer-opacity" type="range" min="0" max="1000" step="10" v-model="undoLimitInSetting" v-bind:disabled="!undoEnabled"></div>
              <div class="columns small-1">
                <a title="Disable undo feature" v-if="undoEnabled" class="button tiny secondary float-right" @click="enableUndo(false)" ><i class="fa fa-stop"></i></a>
                <a title="Enable undo feature" v-if="!undoEnabled"class="button tiny secondary float-right" @click="enableUndo(true)" ><i class="fa fa-play"></i></a>
              </div>
            </div>

           <div class="tool-slice row collapse">
               <hr class="small-12"/>
               <div class="small-3">
                   <label class="tool-label">Reset:</label>
               </div>
               <div class="small-9">
                  <div class="expanded button-group">
                    <a id="reset-sss" class="button alert" title="Clear the current drawing and layer selection (saved views will be retained)" @click="reset()"><i class="fa fa-refresh"></i> Reset SSS</a>
                  </div>
               </div>

               <div class="small-3">
               </div>
               <div class="small-9">
                  <div class="expanded button-group">
                    <a id="reset-settings" class="button alert" title="Reset to system default settings" @click="resetSettings()"><i class="fa fa-refresh"></i> Reset Settings</a>
                  </div>
               </div>

               <div class="small-3">
                   <label class="tool-label">Tour:</label>
               </div>
               <div class="small-9">
                  <div class="expanded button-group">
                    <a id="take-tour" class="button" title="Take a tour of the new SSS interface" @click="$root.takeTour()"><i class="fa fa-book"></i> Take Tour</a>
                  </div>
               </div>
            </div>
            

            <div class="about-pane row collapse about-pane">
              <hr class="small-12"/>
              <div class="small-12">
                <p><b>DISCLAIMER:</b> The Department of Parks and Wildlife does not guarantee that this map is without flaw of any kind and disclaims all liability for any error, or loss or other consequence which may arise from relying on any information depicted. Apart from any use permitted under the Copyright Act, no part of this map may be reproduced by any process without the written permission of the authors. Crown copyright reserved.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <img src="dist/static/images/about.svg" id="about" data-open="aboutModal">

    <div class="reveal" id="aboutModal" data-reveal>
        <div class="about-pane row collapse about-pane">
          <h5 class="small-12">{{profile.description}}</h5>
          <div class="small-4">Version:</div>
          <span class="small-8">{{profile.version}}</span>
          <div class="small-4">Branch:</div>
          <span class="small-8">{{profile.repositoryBranch}}</span>
          <div class="small-4">Last commit:</div>
          <span class="small-8">{{profile.lastCommit}}</span>
          <div class="small-4">Commit date:</div>
          <span class="small-8">{{profile.commitDate}}</span>
          <div class="small-12">
            <p><br/>© 2016 Government of Western Australia<br/>Licensed under the <a href="http://www.apache.org/licenses/LICENSE-2.0">Apache License, Version 2.0</a> (the "License"). Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.</p>
          </div>
        </div>
        <button class="close-button" data-close aria-label="Close Accessible Modal" type="button">
            <span aria-hidden="true">&times;</span>
        </button>
    </div>

  </div>
</template>

<style>
.about-pane {
    font-size: 12px;
}

#about{
    position:absolute;
    bottom:0;
    right:0;
    width:32px;
    height:32px
}

</style>

<script>
  import { $,Vue } from 'src/vendor.js'
  export default {
    store: {
        settings:'settings',
        overviewMap:'settings.overviewMap',
        undoLimit:'settings.undoLimit',
        measureAnnotation:'settings.measureAnnotation',
        lengthUnit:'settings.lengthUnit',
        areaUnit:'settings.areaUnit',
        rightHandTools: 'settings.rightHandTools',
        graticule:'settings.graticule',
        tourVersion:'settings.tourVersion'
    },
    data: function () {
      return {
        undoLimit:0,
        undoEnabled:true,
      }
    },
    computed: {
      loading: function () { return this.$root.loading },
      profile: function () { return this.$root.profile },
      measure: function () { return this.$root.measure },
      info: function () { return this.$root.info },
      annotations: function () { return this.$root.annotations },
      export: function () { return this.$root.export },
      drawinglogs: function () { return this.$root.annotations.drawinglogs },
      map: function () { return this.$root.map },
      undoLimitDesc:function() {
        return (this.undoEnabled?(this.undoLimit === 0?"Unlimited":this.undoLimit):"Off") + "/" + (this.undoLimit < 0?"Off":(this.undoLimit === 0?"Unlimited":this.undoLimit))
      },
      undoLimitInSetting:{
        get: function() {
            return this.undoLimit
        },
        set: function(val) {
            var vm = this
            if (val < 0) {
                this.undoEnabled = false
            } else {
                this.undoLimit =  val
                this.undoEnabled = true
            }
            this._changeUndoLimit = vm._changeUndoLimit || global.debounce(function () {
                //console.log("Change undo limit from " +  (vm.undoLimit < 0?"Off":(vm.undoLimit === 0?"Unlimited":vm.undoLimit)) + " to " + (vm.undoEnabled?(vm.undoLimit === 0?"Unlimited":vm.undoLimit):"off"))
                vm.drawinglogs.size = vm.undoEnabled?vm.undoLimit:-1
            }, 5000)
            this._changeUndoLimit()
        }
      },
      hoverInfoSwitchable: function () {
        return this.$root.annotations.tool && this.$root.annotations.tool.name === "Pan"
      },
      hoverInfo: function() {
        return this.map?this.info.enabled:false
      }
    },
    watch:{
      rightHandTools:function(newValue,oldValue) {
        this.showRightHandTools(newValue)
      },
      overviewMap:function(newValue,oldValue) {
        this.showOverviewMap(newValue)
      }
    },
    methods: {
      setup: function() {
        this.annotations.setTool()
      },
      saveState:function() {
        this.export.saveState()
      },
      enableUndo:function(enable) {
        if (enable) {
            this.undoLimitInSetting = this.undoLimit
        } else {
            this.undoLimitInSetting = -1
        }
      },
      toggleRightHandTools: function (ev) {
        var vm = this
        vm.rightHandTools = ev.target.checked
        this.saveState()
      },
      showRightHandTools: function (show) {
        var vm = this
        $.each(vm.map.mapControls,function(key,control){
            if (["overviewMap","fullScreen","search","mousePosition","attribution"].indexOf(key) < 0) {
                vm.map.enableControl(key,show)
            }
        })
      },
      toggleGraticule: function (ev) {
        this.graticule = ev.target.checked
        this.saveState()
      },
      toggleHoverInfo: function (ev) {
        this.info.hoverInfo = ev.target.checked
        this.saveState()
      },
      toggleMeasureAnnotation:function(ev) {
        this.measureAnnotation = ev.target.checked
        this.export.saveState()
      },
      toggleOverviewMap:function(ev) {
        this.overviewMap = !this.overviewMap
        this.export.saveState()
      },
      showOverviewMap:function(show) {
        if (show) {
           this.map.getControl("overviewMap").setCollapsed(false)
        }
        this.map.enableControl("overviewMap",show)
      },
      reset: function () {
        if (window.confirm('This will clear all of your selected layers and drawings. Are you sure?')) {
          //except settings, clear everything
          localforage.setItem('sssOfflineStore', {settings:this.$root.persistentData.settings}).then(function (v) {
            document.location.reload()
          })
        }
      },
      resetSettings: function () {
        if (window.confirm('This will clear all customized settings and reset to system default settings. Are you sure?')) {
          this.$root.store.settings = $.extend({},JSON.parse(JSON.stringify(this.$root.defaultSettings)),{tourVersion:this.tourVersion})
          this.export.saveState()
        }
      },
    },
    ready: function () {
        var vm = this
        var settingStatus = this.loading.register("setting","Setting Component", "Initialize")
        if (this.undoLimit < 0) {
            this.undoLimit = 0
            this.undoEnabled = false
        } else {
            this.undoLimit = this.undoLimit
            this.undoEnabled = true
        }

      settingStatus.wait(30,"Listen 'gk-init' event")
      this.$on('gk-init', function() {
        settingStatus.progress(80,"Process 'gk-init' event")

        vm.showOverviewMap(vm.overviewMap)
        vm.showRightHandTools(vm.rightHandTools)

        settingStatus.end()
      })
        
    }
  }
</script>
