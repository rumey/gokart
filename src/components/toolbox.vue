<template>
    <div style="display:none">
    <div id="toolbox_control" class="ol-selectable ol-control" v-bind:style="topPositionStyle">
        <button type="button" id="toolbox_tool" title="{{toolTitle}}" style="width:48px;height:36px;border-bottom-left-radius:0px;border-bottom-right-radius:0px" @click="toggleTool()" v-bind:class="{'selected':isControlSelected,'warning':isControlWarning}">
            <img v-bind:src="tool.icon" width=36 height=36>
        </button>
        <button type="button" id="toolbox_expand" style="height:16px;border-top-left-radius:0px;border-top-right-radius:0px"  @click="showTools=!showTools" >
            <i class="fa fa-angle-double-down" aria-hidden="true"></i>
        </button>
        <div v-show="showTools" style="position:absolute;width:200px;right:0px">
            <button type="button" v-for="t in tools" title="{{t.title}}" id="{{t.name}}" style="margin:1px;float:right" track-by="$index" @click.stop.prevent="selectTool(t)">
                <img v-bind:src="t.icon" width="36" height="36">
            </button>
        </div>
        <template v-for="t in tool.assistantButtons" track-by="$index" >
            <button type="button" v-show="showAssistantButton(t)" style="margin-top:1px" title="{{t.title}}" @click.stop.prevent="clickAssistantButton(t)">
                <img v-bind:src="t.icon">
            </button>
        </template>
    </div>
    </div>
  </div>
</template>

<style>
#toolbox_control button{
    width: 48px;
    height: 48px;
    margin: 0;
}

#toolbox_control .selected{
    background-color: #2199E8;
}
#toolbox_control .warning{
    background-color: rgba(125, 47, 34, 0.7);
}
#toolbox_control {
    position: absolute;
    left: auto;
    right: 16px;
    bottom: auto;
    width:48px;
    height:48px;
    padding: 0;
}

</style>

<script>
  import { ol,$,utils} from 'src/vendor.js'
  export default {
    store: {
    },
    data: function () {
      return {
        tool:{},
        tools:[],
        showTools:false,
      }

    },
    // parts of the template to be computed live
    computed: {
      loading: function () { return this.$root.loading },
      annotations: function () { return this.$root.annotations },
      map: function () { return this.$root.map },
      env: function () { return this.$root.env },
      components:function() {
        return [this.$root.spotforecast,this.$root.featuredetail,this.$root.measure]
      },
      enabled:function() {
        return this.layers.length > 0
      },
      topPosition:function() {
        return this.$root.measure.topPosition + this.$root.measure.height;
      },
      topPositionStyle:function() {
        return "top:" + this.topPosition + "px";
      },
      mapControl:function() {
        if (!this._controller) {
            this._controller = new ol.control.Control({
                element: $('#toolbox_control').get(0),
        	target: $('#external-controls').get(0)
            })
        }
        return this._controller
      },
      isControlSelected:function() {
        return (this.tool && this.tool._component)?this.tool._component.isToolActivated(this.tool):false
      },
      isControlWarning:function() {
        return (this.tool && this.tool._component && this.tool._component.isToolWarning)?this.tool._component.isToolWarning(this.tool):false
      },
      toolTitle:function() {
        return this.tool.title
      }
    },
    watch:{
    },
    // methods callable from inside the template
    methods: {
      inToolbox:function(component) {
        return this.components.findIndex(function(o){return o === component}) >= 0
      },
      selectTool:function(tool,enabled) {
        this.showTools = false
        enabled = (enabled === null || enabled === undefined)?true:enabled
        if (this.tool === tool) return
        this.tool = tool
        this.tool._component.selectTool(this.tool)
        if (enabled) {
            this.tool._component.toggleTool(true,this.tool)
        }
      },
      toggleTool:function(enabled) {
        this.tool._component.toggleTool(enabled,this.tool)
      },
      showAssistantButton:function(button) {
        return this.showTools?false:(this.tool._component.showAssistantButton && this.tool._component.showAssistantButton(button))
      },
      clickAssistantButton:function(button) {
        this.tool._component.clickAssistantButton(button)
      }
    },
    ready: function () {
      var vm = this
      this._toolboxStatus = vm.loading.register("toolbox","Toolbox Component")

      this._toolboxStatus.phaseBegin("gk-init",80,"Listen 'gk-init' event",true,true)
      this.$on('gk-init', function() {
        vm._toolboxStatus.phaseEnd("gk-init")

        vm._toolboxStatus.phaseBegin("initialize",20,"Initialize",true,false)
        
        var defaultTool = null;
        var index = 0
        $.each(vm.components,function(index1,component){
            $.each(component.tools,function(index2,tool){
                tool._component = component
                tool.assistantButtons = (tool.assistantButtons === null || tool.assistantButtons === undefined)?[]:tool.assistantButtons
                vm.tools.splice( Math.floor(index / 4) * 4,0,tool)
                if (index === 0) {
                    defaultTool = tool
                }
                index += 1
            })
        })
        if (vm.tools.length) {
            vm.map.mapControls["toolbox"] = {
                enabled:false,
                autoenable:false,
                controls:vm.mapControl
            }
    
            vm.selectTool(defaultTool,false)
        }
        vm.revision += 1

        vm._toolboxStatus.phaseEnd("initialize")
      })
        
    }
  }
</script>
