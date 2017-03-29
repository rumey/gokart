<template>
    <gk-loading v-ref:loading application="SSS"></gk-loading>
    <div class="off-canvas-wrapper">
        <div class="off-canvas-wrapper-inner" data-off-canvas-wrapper>
            <div class="off-canvas position-left" id="offCanvasLeft" data-off-canvas>
                <a id="side-pane-close" class="button alert hide-for-medium">&#x2715;</a>
                <div class="tabs-content vertical" data-tabs-content="menu-tabs">
                    <gk-setting v-ref:setting></gk-setting>
                    <gk-layers v-ref:layers></gk-layers>
                    <gk-annotations v-ref:annotations></gk-annotations>
                    <gk-tracking v-ref:tracking></gk-tracking>
                    <gk-bfrs v-ref:bfrs></gk-bfrs>
                    <gk-dialog v-ref:dialog></gk-dialog>
                </div>
            </div>
            <div class="off-canvas-content" data-off-canvas-content>
                <ul class="tabs vertical map-widget" id="menu-tabs" data-tabs>
                    <li class="tabs-title side-button is-active" menu="layers">
                        <a href="#menu-tab-layers" title="Map Layers">
                            <svg class="icon">
                                <use xlink:href="dist/static/images/iD-sprite.svg#icon-layers"></use>
                            </svg>
                        </a>
                    </li>
                    <li class="tabs-title side-button" menu="annotations">
                        <a href="#menu-tab-annotations" title="Drawing Tools">
                            <i class="fa fa-pencil" aria-hidden="true"></i>
                        </a>
                    </li>
                    <li class="tabs-title side-button"  menu="tracking">
                        <a href="#menu-tab-tracking" title="Resources Tracking">
                            <i class="fa fa-truck" aria-hidden="true"></i>
                        </a>
                    </li>
                    <li class="tabs-title side-button" menu="bfrs">
                        <a href="#menu-tab-bfrs" title="Bushfire Report System">
                            <i class="fa fa-fire" aria-hidden="true"></i>
                        </a>
                    </li>
                    <li class="tabs-title side-button" menu="setting">
                        <a href="#menu-tab-setting" title="System Settings">
                            <i class="fa fa-cog" aria-hidden="true"></i>
                        </a>
                    </li>
                </ul>
                <gk-map v-ref:map></gk-map>
            </div>
        </div>
    </div>
    <div id="external-controls"></div>
</template>

<script>
    import gkMap from '../components/map.vue'
    import gkLayers from '../components/layers.vue'
    import gkAnnotations from '../components/annotations.vue'
    import gkTracking from '../components/sss/tracking.vue'
    import gkLoading from '../components/loading.vue'
    import gkSetting from '../components/setting.vue'
    import gkBfrs from '../components/sss/bfrs.vue'
    import gkDialog from '../components/dialog.vue'
    import { ol } from 'src/vendor.js'


    export default { 
      store:{
        activeMenu:'activeMenu'
      },
      data: function() {
        return {
        }
      },
      components: { gkMap, gkLayers, gkAnnotations, gkTracking, gkLoading,gkSetting , gkBfrs ,gkDialog},
      ready: function () {
        var vm = this
        $("#menu-tabs").on("change.zf.tabs",function(target,selectedTab){
            var menu = selectedTab.attr('menu')
            if (vm.activeMenu && vm.activeMenu == menu) {
                //click on the active menu, do nothing
                return
            } else {
                if (vm.activeMenu && vm.$root[vm.activeMenu].teardown) {
                  vm.$root[vm.activeMenu].teardown()
                }
                vm.activeMenu = menu
                if (vm.activeMenu && vm.$root[vm.activeMenu].setup) {
                  vm.$root[vm.activeMenu].setup()
                }
            }
            
        })
      }
    }
</script>

