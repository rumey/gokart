import {
  $,
  svg4everybody,
  ol,
  proj4,
  moment,
  localforage,
  Vue,
  VueStash
} from 'src/vendor.js'
import App from './sss.vue'
import tour from './sss-tour.js'
import profile from './sss-profile.js'

global.tour = tour

global.debounce = function (func, wait, immediate) {
  // Returns a function, that, as long as it continues to be invoked, will not
  // be triggered. The function will be called after it stops being called for
  // N milliseconds. If `immediate` is passed, trigger the function on the
  // leading edge, instead of the trailing.
  'use strict'
  var timeout
  return function () {
    var context = this
    var args = arguments
    var later = function () {
      timeout = null
      if (!immediate) func.apply(context, args)
    }
    var callNow = immediate && !timeout
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
    if (callNow) func.apply(context, args)
  }
}
var volatileData = {
  // overridable defaults for WMTS and WFS loading
  remoteCatalogue: env.cswService + "?format=json&application__name=sss",
  defaultWMTSSrc: env.wmtsService,
  defaultWFSSrc: env.wfsService,
  defaultLegendSrc: env.legendSrc,
  gokartService: env.gokartService,
  oimService:env.oimService,
  sssService:env.sssService,
  s3Service:env.s3Service,
  //bfrsService:env.bfrsService,
  appType:env.appType,
  // fixed scales for the scale selector (1:1K increments)
  fixedScales: [0.25, 0.5, 1, 2, 2.5, 5, 10, 20, 25, 50, 80, 100, 125, 250, 500, 1000, 2000, 3000, 5000, 10000, 25000],
  // default matrix from KMI
  resolutions: [0.17578125, 0.087890625, 0.0439453125, 0.02197265625, 0.010986328125, 0.0054931640625, 0.00274658203125, 0.001373291015625, 0.0006866455078125, 0.0003433227539062, 0.0001716613769531, 858306884766e-16, 429153442383e-16, 214576721191e-16, 107288360596e-16, 53644180298e-16, 26822090149e-16, 13411045074e-16],
  mmPerInch: 25.4,
  whoami: { email: null },
  // filters for finding layers
  catalogueFilters: [
    ['basemap', 'Base Imagery'],
    ['boundaries', 'Admin Boundaries'],
    ['communications', 'Communications'],
    ['fire', 'Fire Operations'],
    ['meteorology', 'Meteorology'],
    ['vegetation', 'Vegetation'],
    ['tenure', 'Tenure and Land Use'],
    ['infrastructure', 'Infrastructure'],
    ['grid', 'Grid Systems'],
    ['resources', 'Resource Tracking']
  ],
  matrixSets: {
    'EPSG:4326': {
      '1024': {
        'name': 'gda94',
        'minLevel': 0,
        'maxLevel': 17
      }
    }
  }
}

var persistentData = {
  view: {
    center: [123.75, -24.966]
  },
  // id followed by properties to merge into catalogue
  activeLayers: [
    ['dpaw:resource_tracking_live', {}],
    ['cddp:state_map_base', {}]
  ],
  // blank annotations
  annotations: {
    type: 'FeatureCollection',
    features: []
  },
  drawingLogs:[],
  redoPointer:0,//pointer to the next redo log 
  drawingSequence:0,
  //data in settings will survive across reset
  settings:{
    tourVersion: null,
    undoLimit:0,
    lengthUnit:"km",
    areaUnit:"ha",
    measureAnnotation:false,
    maintainScaleWhenPrinting:true
  }
}

global.gokartService = volatileData.gokartService;

global.localforage = localforage
global.$ = $

Vue.use(VueStash)
localforage.getItem('sssOfflineStore').then(function (store) {
  var settings = $.extend({},persistentData.settings,store?(store.settings || {}):{})
  var storedData = $.extend({}, persistentData, store || {}, volatileData)
  storedData.settings = settings

  global.gokart = new Vue({
    el: 'body',
    components: {
      App
    },
    data: {
      // store contains state we want to reload/persist
      store: storedData,
      pngs: {},
      fixedLayers:[],
      saved: null,
      touring: false,
      tints: {
        'selectedPoint': [['#b43232', '#2199e8']],
        'selectedDivision': [['#000000', '#2199e8'], ['#7c3100','#2199e8'], ['#ff6600', '#ffffff']],
        'selectedRoadClosurePoint': [['#000000', '#2199e8']],
        'selectedPlusIcon': [['#006400', '#2199e8']],
      }
    },
    computed: {
      loading: function () { return this.$refs.app.$refs.loading },
      map: function () { return this.$refs.app.$refs.map },
      scales: function () { return this.$refs.app.$refs.map.$refs.scales },
      search: function () { return this.$refs.app.$refs.map.$refs.search },
      measure: function () { return this.$refs.app.$refs.map.$refs.measure },
      info: function () { return this.$refs.app.$refs.map.$refs.info },
      active: function () { return this.$refs.app.$refs.layers.$refs.active },
      catalogue: function () { return this.$refs.app.$refs.layers.$refs.catalogue },
      export: function () { return this.$refs.app.$refs.layers.$refs.export },
      annotations: function () { return this.$refs.app.$refs.annotations },
      tracking: function () { return this.$refs.app.$refs.tracking },
      setting: function () { return this.$refs.app.$refs.setting },
      //bfrs: function () { return this.$refs.app.$refs.bfrs },
      geojson: function () { return new ol.format.GeoJSON() },
      wgs84Sphere: function () { return new ol.Sphere(6378137) },
      activeMenu: function() {return this.$refs.app.activeMenu},
      profile: function(){return profile},
      persistentData:function() {
          var vm = this
          $.each(persistentData,function(key,val){
              persistentData[key] = vm.store[key]
          })
          return persistentData
      }
    },
    methods: {
      takeTour: function() {
          this.store.settings.tourVersion = tour.version
          this.export.saveState()
          this.touring = true
          tour.start()
      }
    },
    ready: function () {
      var self = this
      self.loading.app.progress(5,"Initialize UI")
      // setup foundation, svg url support
      $(document).foundation()
      svg4everybody()
      // set title
      $('title').text(profile.description)
      // calculate screen res
      $('body').append('<div id="dpi" style="width:1in;display:none"></div>')
      self.dpi = parseFloat($('#dpi').width())
      self.store.dpmm = self.dpi / self.store.mmPerInch
      $('#dpi').remove();
      // get user info
      (function () {
        var req = new window.XMLHttpRequest()
        req.withCredentials = true
        req.onload = function () {
          self.store.whoami = JSON.parse(this.responseText)
        }
        req.open('GET', self.store.oimService + '/api/whoami')
        req.send()
      })()
      // bind menu side-tabs to reveal the side pane
      var offCanvasLeft = $('#offCanvasLeft')
      $('#menu-tabs').on('change.zf.tabs', function (ev) {
        offCanvasLeft.addClass('reveal-responsive')
        self.map.olmap.updateSize()
      }).on('click', '.tabs-title a[aria-selected=false]', function (ev) {
        offCanvasLeft.addClass('reveal-responsive')
        $(this).attr('aria-selected', true)
        self.map.olmap.updateSize()
      }).on('click', '.tabs-title a[aria-selected=true]', function (ev) {
        offCanvasLeft.toggleClass('reveal-responsive')
        self.map.olmap.updateSize()
      })
      $('#side-pane-close').on('click', function (ev) {
        offCanvasLeft.removeClass('reveal-responsive')
        $('#menu-tabs').find('.tabs-title a[aria-selected=true]').attr('aria-selected', false)
        self.map.olmap.updateSize()
      })

      self.loading.app.progress(10,"Initialize Fixed Layers")
      // pack-in catalogue
      self.fixedLayers = self.fixedLayers.concat([{
        type: 'TimelineLayer',
        name: 'Himawari-8 Hotspots',
        id: 'himawari8:hotspots',
        source: self.store.gokartService + '/hi8/AHI_TKY_FHS',
        params: {
          FORMAT: 'image/png'
        },
        refresh: 300
      }, {
        type: 'TimelineLayer',
        name: 'Himawari-8 True Colour',
        id: 'himawari8:bandtc',
        source: self.store.gokartService + '/hi8/AHI_TKY_b321',
        refresh: 300,
        base: true
      /*
      }, {
        type: 'TimelineLayer',
        name: 'Himawari-8 Band 3',
        id: 'himawari8:band3',
        source: self.store.gokartService + '/hi8/AHI_TKY_b3',
        refresh: 300,
        base: true
      */
      }, {
        type: 'TimelineLayer',
        name: 'Himawari-8 Band 7',
        id: 'himawari8:band7',
        source: self.store.gokartService + '/hi8/AHI_TKY_b7',
        refresh: 300,
        base: true
     /*
      }, {
        type: 'TimelineLayer',
        name: 'Himawari-8 Band 15',
        id: 'himawari8:band15',
        source: self.store.gokartService + '/hi8/AHI_TKY_b15',
        refresh: 300,
        base: true
      */
      }, {
        type: 'TileLayer',
        name: 'State Map Base',
        id: 'cddp:state_map_base',
        base: true
      }, {
        type: 'TileLayer',
        name: 'Virtual Mosaic',
        id: 'landgate:LGATE-V001',
        base: true
      }, {
        type: 'TileLayer',
        name: 'DFES Active Fireshapes',
        id: 'landgate:dfes_active_fireshapes',
        refresh: 60
      }, {
        type: 'TileLayer',
        name: 'Forest Fire Danger Index',
        id: 'bom:forest_fire_danger_index',
        timelineSize:72,
        updateTime:[["07:00:00","19:00:00"],"HH:mm:ss","UTC"],
        getLayerId: function(latestUpdateTime,timelineIndex) {
            return "bom:IDZ71117" + (timelineIndex < 10?"00":(timelineIndex < 100?"0":"")) + timelineIndex
        },
        layerTimeInterval:3600 * 1000
      }, {
        type: 'TileLayer',
        name: 'Maximum Forest Fire Danger Index',
        id: 'bom:maximum_forest_fire_danger_index',
        timelineSize:4,
        updateTime:[["00:00:00","12:00:00"],"HH:mm:ss","UTC"],
        getLayerId: function(latestUpdateTime,timelineIndex) {
            return "bom:IDZ71118" + (timelineIndex < 10?"00":(timelineIndex < 100?"0":"")) + timelineIndex
        },
        layerTimeInterval:24 * 3600 * 1000
      }, {
        type: 'TileLayer',
        name: 'Grassland Fire Danger Index',
        id: 'bom:grass_fire_danger_index',
        timelineSize:72,
        updateTime:[["07:00:00","19:00:00"],"HH:mm:ss","UTC"],
        getLayerId: function(latestUpdateTime,timelineIndex) {
            return "bom:IDZ71122" + (timelineIndex < 10?"00":(timelineIndex < 100?"0":"")) + timelineIndex
        },
        layerTimeInterval:3600 * 1000
      }, {
        type: 'TileLayer',
        name: 'Maximum Grassland Fire Danger Index',
        id: 'bom:maximum_grass_fire_danger_index',
        timelineSize:4,
        updateTime:[["00:00:00","12:00:00"],"HH:mm:ss","UTC"],
        getLayerId: function(latestUpdateTime,timelineIndex) {
            return "bom:IDZ71123" + (timelineIndex < 10?"00":(timelineIndex < 100?"0":"")) + timelineIndex
        },
        layerTimeInterval:24 * 3600 * 1000
      }])

      // load custom annotation tools
      self.loading.app.progress(20,"Initialize SSS tools")

      var sssTools = [
        {
          name: 'Fire Boundary',
          icon: 'dist/static/images/iD-sprite.svg#icon-area',
          style: self.annotations.getVectorStyleFunc(self.tints),
          selectedFillColour:[0, 0, 0, 0.25],
          fillColour:[0, 0, 0, 0.25],
          size:2,
          interactions: [self.annotations.polygonDrawFactory()],
          scope:["annotation"],
          showName: true,
          measureLength:true,
          measureArea:true,
          comments:[
            {name:"Tips",description:["Hold down the 'SHIFT' key during drawing to enable freehand mode. "]}
          ]
        },
        self.annotations.ui.defaultText,
        {
          name: 'Division',
          icon: 'dist/static/symbols/fire/division.svg',
          tints: self.tints,
          perpendicular: true,
          interactions: [self.annotations.pointDrawFactory(), self.annotations.snapToLineFactory()],
          style: self.annotations.getIconStyleFunction(self.tints),
          sketchStyle: self.annotations.getIconStyleFunction(self.tints),
          selectedTint: 'selectedDivision',
          scope:["annotation"],
          showName: true
        }, {
          name: 'Sector',
          icon: 'dist/static/symbols/fire/sector.svg',
          tints: self.tints,
          perpendicular: true,
          interactions: [self.annotations.pointDrawFactory(), self.annotations.snapToLineFactory()],
          style: self.annotations.getIconStyleFunction(self.tints),
          sketchStyle: self.annotations.getIconStyleFunction(self.tints),
          selectedTint: 'selectedDivision',
          scope:["annotation"],
          showName: true
        },{
        /*  name: 'Hot Spot',
          icon: 'fa-circle red',
          interactions: [hotSpotDraw],
          style: hotSpotStyle,
          showName: true
        }, {*/
          name: 'Origin Point',
          icon: 'dist/static/symbols/fire/origin.svg',
          tints: self.tints,
          interactions: [self.annotations.pointDrawFactory()],
          style: self.annotations.getIconStyleFunction(self.tints),
          sketchStyle: self.annotations.getIconStyleFunction(self.tints),
          selectedTint: 'selectedPoint',
          scope:["annotation"],
          showName: true,
        }, {
          name: 'Spot Fire',
          icon: 'dist/static/symbols/fire/spotfire.svg',
          tints: self.tints,
          interactions: [self.annotations.pointDrawFactory()],
          style: self.annotations.getIconStyleFunction(self.tints),
          sketchStyle: self.annotations.getIconStyleFunction(self.tints),
          selectedTint: 'selectedPoint',
          scope:["annotation"],
          showName: true,
        }, {
          name: 'Road Closure',
          icon: 'dist/static/symbols/fire/road_closure_point.svg',
          tints: self.tints,
          interactions: [self.annotations.pointDrawFactory()],
          style: self.annotations.getIconStyleFunction(self.tints),
          sketchStyle: self.annotations.getIconStyleFunction(self.tints),
          showName: true,
          selectedTint: 'selectedRoadClosurePoint',
          scope:["annotation"],
        }, {
          name: 'Control Line',
          icon: 'dist/static/symbols/fire/controlline.svg',
          interactions: [self.annotations.linestringDrawFactory()],
          size: 1,
          typeIcon: 'dist/static/symbols/fire/plus.svg',
          typeIconSelectedTint: 'selectedPlusIcon',
          typeIconDims: [20,20],
          colour: 'rgba(0, 0, 0, 0.1)',
          showName: true,
          scope:["annotation"],
          style: self.annotations.getVectorStyleFunc(this.tints)
        },
        self.annotations.ui.defaultLine,
        self.annotations.ui.defaultPolygon,
        self.annotations.ui.defaultPoint
      ]

      sssTools.forEach(function (tool) {
        self.annotations.tools.push(tool)
      })

      // load map without layers
      self.loading.app.progress(30,"Initialize ol map")
      self.map.init()
      self.loading.app.progress(40,"Load Remote Catalogue")
      try {
          self.catalogue.loadRemoteCatalogue(self.store.remoteCatalogue, function () {
            //add default layers
            try {
                self.loading.app.progress(50,"Initialize Active Layers")
                self.map.initLayers(self.fixedLayers, self.store.activeLayers)
                // tell other components map is ready
                self.loading.app.progress(60,"Broadcast 'gk-init' event")
                self.$broadcast('gk-init')
                // after catalogue load trigger a tour
                $("#menu-tab-layers-label").trigger("click")
                self.$refs.app.switchMenu("mapLayers",self.$refs.app.init)
                self.loading.app.progress(90,"Broadcast 'gk-postinit' event")
                self.$broadcast('gk-postinit')
                self.loading.app.end()
            } catch(err) {
                //some exception happens
                self.loading.app.failed(err)
                throw err
            }
            if (self.store.settings.tourVersion !== tour.version) {
              self.takeTour()
            }
          },function(reason){
            self.loading.app.failed(reason)
          })
      } catch(err) {
          //some exception happens
          self.loading.app.failed(err)
          throw err
      }
    }
  })
})
