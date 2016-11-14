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
                <input class="switch-input" id="toggleHoverInfo" type="checkbox" v-bind:checked="hoverInfo" @change="toggleHoverInfo" />
                <label class="switch-paddle" for="toggleHoverInfo">
                  <span class="show-for-sr">Display hovering feature info</span>
                </label>
              </div>
              <label for="toggleHoverInfo" class="side-label">Display hovering feature info</label>
            </div>

            <div class="tool-slice row collapse">
              <div class="switch tiny">
                <input class="switch-input" id="toggleRightHandTools" type="checkbox" v-bind:checked="showRightHandTools" @change="toggleRightHandTools" />
                <label class="switch-paddle" for="toggleRightHandTools">
                  <span class="show-for-sr">Show Right Hand Tools</span>
                </label>
              </div>
              <label for="toggleRightHandTools" class="side-label">Show Right Hand Tools</label>
            </div>

           <div class="tool-slice row collapse">
               <hr class="small-12"/>
               <div class="small-3">
                   <label class="tool-label">Reset:</label>
               </div>
               <div class="small-9">
                  <div class="expanded button-group">
                    <a id="reset-sss" class="button alert" title="Clear current config and annotations" @click="reset()"><i class="fa fa-refresh"></i> Reset SSS</a>
                  </div>
               </div>
               <div class="small-3">
                   <label class="tool-label">Tour:</label>
               </div>
               <div class="small-9">
                  <div class="expanded button-group">
                    <a id="take-tour" class="button" title="Take tour" @click="$root.takeTour()"><i class="fa fa-book"></i> Take Tour</a>
                  </div>
               </div>
            </div>

            <div class="tool-slice row collapse">
              <hr class="small-12">
              <h6 class="small-4">Name:</h6>
              <span class="small-8">{{profile.name}}</span>
              <h6 class="small-4">Description:</h6>
              <span class="small-8">{{profile.description}}</span>
              <h6 class="small-4">Version:</h6>
              <span class="small-8">{{profile.version}}</span>
              <h6 class="small-4">Branch:</h6>
              <span class="small-8">{{profile.repositoryBranch}}</span>
              <h6 class="small-4">Last Commit:</h6>
              <span class="small-8">{{profile.lastCommit}}</span>
              <h6 class="small-4">Commit Date:</h6>
              <span class="small-8">{{profile.commitDate}}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<style>
</style>

<script>
  import { $,Vue } from 'src/vendor.js'
  export default {
    data: function () {
      return {
        hoverInfoCache: false,
        showRightHandTools: true
      }
    },
    computed: {
      loading: function () { return this.$root.loading },
      profile: function () { return this.$root.profile },
      measure: function () { return this.$root.measure },
      map: function () { return this.$root.map },
      graticule: {
        cache: false,
        get: function () {
          return this.$root.map && this.$root.map.graticule && this.$root.map.graticule.getMap() === this.$root.map.olmap
        }
      },
      hoverInfoSwitchable: function () {
        return this.$root.annotations.tool && this.$root.annotations.tool.name === "Pan"
      },
      hoverInfo: {
        cache: false,
        get: function () {
          return this.$root.map && this.$root.info && this.$root.info.enabled
        },
        set: function (val) {
          this.$root.info.enabled = val
        }
      },
    },
    methods: {
      init: function() {
        this.setTool()
      },
      toggleRightHandTools: function () {
        var vm = this
        vm.showRightHandTools = !vm.showRightHandTools
        $.each(vm.map.mapControls,function(key,control){
            if (["fullScreen","search","mousePosition","attribution"].indexOf(key) < 0) {
                vm.map.enableControl(key,vm.showRightHandTools)
            }
        })
      },
      toggleGraticule: function () {
        var map = this.$root.map
        if (this.graticule) {
          map.graticule.setMap(null)
        } else {
          map.graticule.setMap(map.olmap)
        }
      },
      toggleHoverInfo: function (ev) {
        this.hoverInfoCache = ev.target.checked
        this.hoverInfo = ev.target.checked
      },
      reset: function () {
        if (window.confirm('This will clear all of your selected layers and annotations. Are you sure?')) {
          //except settings, clear everything
          localforage.setItem('sssOfflineStore', {settings:this.$root.persistentData.settings}).then(function (v) {
            document.location.reload()
          })
        }
      },
    },
    ready: function () {
        var vm = this
        var settingStatus = this.loading.register("setting","Setting Component", "Initialize")
        settingStatus.end()
    }
  }
</script>
