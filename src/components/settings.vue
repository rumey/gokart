<template>
  <div class="tabs-panel" id="menu-tab-settings">
    <div class="row collapse">
      <div class="columns">
        <ul class="tabs" data-tabs id="settings-tabs">
          <li class="tabs-title is-active" menu="systemsetting"><a href="#systemsetting" aria-selected="true">System</a></li>
          <li class="tabs-title" menu="spotforecast"><a href="#spotforecast" aria-selected="true">Spot Outlook Forecast</a></li>
        </ul>
      </div>
    </div>
    <div class="row collapse" id="settings-tab-panels">
      <div class="columns">
        <div class="tabs-content vertical" data-tabs-content="settings-tabs">
          <gk-systemsetting v-ref:systemsetting></gk-systemsetting>
          <gk-spotforecast v-ref:spotforecast></gk-spotforecast>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import gkSystemsetting from './systemsetting.vue'
  import gkSpotforecast from './spotforecast.vue'

  export default { 
    store: {
        activeMenu:'activeMenu',
        activeSubmenu:'activeSubmenu'
    },
    components: { gkSystemsetting,gkSpotforecast },
    computed: {
        info: function () { return this.$root.info },
    },
    methods:{
        setup: function() {
            this.$root.annotations.setTool()
        },
        switchMenu:function(menu) {
            if ((this.activeSubmenu === menu) || (!this.activeSubmenu && !menu)) {
                //new active submenu is equal to current active submenu, do nothing
                return
            }
            if (this.activeSubmenu && this.$root[this.activeSubmenu].teardown) {
                this.$root[this.activeSubmenu].teardown()
            }
            this.activeSubmenu = menu || null
            if (this.activeSubmenu && this.$root[this.activeSubmenu].setup) {
                this.$root[this.activeSubmenu].setup()
            }
        }
    }, 
    ready: function () {
      var vm = this
      $("#settings-tabs").on("change.zf.tabs",function(target,selectedTab){
          var menu = selectedTab.attr('menu')
          vm.info.hoverable.splice(0,vm.info.hoverable.length)
          vm.switchMenu(menu)
          vm.$root.menuChanged()
      })
    }
  }
</script>
