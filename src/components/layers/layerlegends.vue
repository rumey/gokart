<template >
  <div class="reveal" id="active-layers-legend" data-reveal data-v-offset="0px" data-h-offset="auto" data-overlay="true" data-close-on-esc="false" data-close-on-click="false">
    <h4>Legends ({{displayLegendLayers.length}}/{{legendLayers.length}})</h4>
    <div id="active-layer-legend-list">
        <template v-for="l in displayLegendLayers" track-by="id">
            <div class="layer-legend-row row" >
                <div class="small-11">
                    <a class="layer-title" style="cursor:hand">{{ l.name || l.id }} </a>
                </div>
                <div class="small-1">
                    <a class="button tiny secondary" @click="hideLegend(l)" title="Hide"><i class="fa fa-eye-slash"></i></a>
                </div>
                <div class="small-12">
                    <img v-bind:src="l.legend" class="cat-legend" @error="loadLegendFailed($index,l)" crossOrigin="use-credentials"/>
                </div>
            </div>
         </template>
     </div>
     <button v-bind:class={disabled:disableShowall} v-bind:disabled="disableShowall" type="button" class="showall-button" @click="showAll()" title="Show All">
       <i class="fa fa-eye"></i>
     </button>
     <button v-bind:class="{disabled:disablePrint}" v-bind:disabled="disablePrint" type="button" class="print-button" @click="printLegends()" title="Print">
       <i class="fa fa-print"></i>
     </button>
     <button class="close-button" data-close aria-label="Close modal" type="button" title="Close">
       <span aria-hidden="true">&times;</span>
     </button>
  </div>
</template>
<style>
#active-layers-legend .disabled{
    color: #8a8a8a;
}
#active-layers-legend button{
    position: absolute;
    color: #2199e8;
    top: 1rem;
    font-size: 1.3em;
}
#active-layers-legend .showall-button{
    right: 4.5rem;
}
#active-layers-legend .print-button{
    right: 2.5rem;
}

</style>
<script>
  import { saveAs, $, jsPDF } from 'src/vendor.js'
  export default {
    store: [ 'dpmm'],
    data: function() {
      return {
          legendLayers:[],
          filteredLegendLayers:[],
          hiddenLayers:{}
      }
    },
    computed: {
      displayLegendLayers:function() {
        return this.filteredLegendLayers || this.legendLayers
      },
      disableShowall:function() {
        return this.filteredLegendLayers?false:true
      },
      disablePrint:function() {
        return this.displayLegendLayers.length == 0
      }
    },
    methods:{
      showAll:function() {
        this.hiddenLayers = {}
        this.filteredLegendLayers = null
        
      },
      hideLegend:function(l) {
        if (this.hiddenLayers[l.id]) return
        this.hiddenLayers[l.id] = true
        if (this.showLengendLayers == null) {
            var vm = this
            this.filteredLegendLayers = this.legendLayers.filter(function(layer){
                return !vm.hiddenLayers[layer.id]
            })
        } else {
            this.filteredLegendLayers.splice(this.filteredLegendLayers.indexOf(l),1)
        }
      },
      toggleLegends: function() {
        var vm = this
        var watchActiveLayers = function(){
            var catalogue = vm.$root.catalogue
            var results = []
            var showLegendLen = 0
            vm.$root.active.olLayers.every(function (layer) {
              var catLayer = catalogue.getLayer(layer)
              if (catLayer) {
                if (catLayer.legend && (catLayer.loadLegendFailed == undefined || !catLayer.loadLegendFailed)) {
                    results.push(catLayer)
                    showLegendLen += catLayer.hidden?0:1
                }
                return true
              } else {
                return false
              }
            })
            if (results.length == vm.legendLayers) {
                results = results.reverse()
                var changed = false
                for(var i = 0;i < results.length; i++) {
                    if (results[i].id != vm.legendLayers.id) {
                        changed = true
                        break
                    }
                }
                if (!changed) {
                    return
                }
            }
            vm.legendLayers = results 
            if (vm.legendLayers.find(function(layer){return vm.hiddenLayers[layer.id]})) {
                vm.filteredLegendLayers = vm.legendLayers.filter(function(layer){
                    return !vm.hiddenLayers[layer.id]
                })
            } else {
                vm.filteredLegendLayers = null
            }
        }
        vm.activeLayerLegends = vm.activeLayerLegends || new Foundation.Reveal($("#active-layers-legend"))
        if (vm.activeLayerLegends.isActive) {
            vm.activeLayerLegends.close()
            vm.unwatchActiveLayers()
            vm.unwatchActiveLayers = false
            return
        }
        if (!vm.unwatchActiveLayers) {
            watchActiveLayers()
            vm.unwatchActiveLayers = this.$root.active.$watch("olLayers",function(newVal,oldVal){
                watchActiveLayers()
            })
        }
        vm.activeLayerLegends.open()
      },
      loadLegendFailed:function(index,l) {
        this.legendLayers.splice(index,1)
        l.loadLegendFailed = true
        if(!this.hiddenLayers[l.id]) {
            this.filteredLegendLayers.splice(this.filteredLegendLayers.indexOf(l),1)
        }
        
      },
      getImageDataURL: function(img,format) {
        format = format || "image/jpeg"
        var canvas = document.createElement("canvas");
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        $(document.body).append($(canvas))
        var ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0,img.naturalWidth,img.naturalHeight,0,0,canvas.width,canvas.height);
        return canvas.toDataURL(format,1);
      },
      printLegends:function() {
        var vm = this
        var paperSize = this.$root.export.paperSizes["A4"]
        var style = { 
          top: 20, 
          bottom: 20, 
          left: 20,
          right:20,
          width: paperSize[1],
          height:paperSize[0],
          fontHeight:10,
          padding:5,
          font:"helvetica",
          fontType:"bold",
          fontSize:10,
          textColor:[0,0,0],
          lineWidth: 1,
          lineColor:[77,77,77]
        }
        var getImageSize = function(img,textHeight) {
          var width = 0
          var height = 0
          var maxImageSize = [style.width - style.left - style.right,style.height - style.top - style.bottom - textHeight]
          var imgSize = [Math.floor(img.naturalWidth / vm.dpmm), Math.floor(img.naturalHeight / vm.dpmm)]
        
          if (imgSize[0] / imgSize[1] > maxImageSize[0] /maxImageSize[1]) {
            if (imgSize[0] <= maxImageSize[0]) {
                width = imgSize[0]
                height = imgSize[1]
            } else {
                width = maxImageSize[0]
                height = (imgSize[1] * width) / imgSize[0]
            }
          } else {
            if (imgSize[1] <= maxImageSize[1]) {
                height = imgSize[1]
                width = imgSize[0]
            } else {
                height = maxImageSize[1]
                width = (imgSize[0] * height) / imgSize[1]
            }
          }
          return [width,height]
        }
        var doc = new jsPDF();
        doc.setFontSize(style.fontSize)
        doc.setFont(style.font)
        doc.setFontType(style.fontType)
        doc.setTextColor(style.textColor[0],style.textColor[1],style.textColor[2])
        doc.setLineWidth(style.lineWidth)
        doc.setDrawColor(style.lineColor[0],style.lineColor[1],style.lineColor[2])
        var top = style.top
        $("#active-layer-legend-list .layer-legend-row").each(function(index,element){
            var imgElement = $(element).find("img").get(0)
            var imageSize = getImageSize(imgElement,style.fontHeight)
            if (top != style.top && top + style.fontHeight + imageSize[1] + style.bottom + 2 * style.padding + style.lineWidth > style.height) {
                doc.addPage()
                top = style.top
            } else if (top !=style.top) {
                top += style.padding
                doc.setLineWidth(style.lineWidth)
                doc.line(style.left,top,style.width - style.right,top)
                top += style.lineWidth
                top += style.padding
            }
            doc.text(style.left,top,$(element).find(".layer-title").text())
            top += style.fontHeight
            doc.addImage(vm.getImageDataURL(imgElement,"image/jpeg"),"JPEG",style.left,top,imageSize[0],imageSize[1])
            top += imageSize[1]
        })
        var filename = this.$root.export.finalTitle.replace(' ', '_') + ".legend.pdf"
        saveAs(doc.output("blob"),filename)

      },
    }
  }
</script>
