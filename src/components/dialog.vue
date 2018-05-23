<template>
    <div class="{{classes}} reveal" id="userdialog" data-reveal data-close-on-click='false' > 
        <h3 v-show="title">{{title}}</h3>
        <div v-for="line in messages" class="row" track-by="$index" >
            <div v-for="message in line" class="small-{{message[1]}} columns {{messageClass(message)}}" track-by="$index">
                 <p v-if="messageType(message) === 'show'" style="white-space:pre-wrap;">{{message[0]}}</p>
                 <a v-if="messageType(message) === 'link'" href="{{message[0]}}" @click.stop.prevent="utils.editResource($event)" target="{{messageAttr(message,'target')}}">{{message[0]}}</a>
                 <input v-if="['radio','checkbox'].indexOf(messageType(message)) >= 0" type="{{message[2]['type']}}" name="{{messageAttr(message,'name')}}" value="{{message[0]}}" @click.stop="processEvent(messageAttr(message,'click'),$event)" disabled="{{messageAttr(message,'disabled',false)}}" checked="{{isChecked(message)}}">
                 <input v-if="messageType(message) === 'text'" type="text" name="{{messageAttr(message,'name')}}"  disabled="{{messageAttr(message,'disabled')}}" value="{{getValue(message)}}">
            </div>
        </div>

        <div class="row align-center" v-if="hasProgressBar">
            <div class="small-2 columns small-centered" >
                Total: {{tasks}}
            </div>

            <div class="small-2 columns small-centered" >
                Succeed: {{succeedTasks}}
            </div>

            <div class="small-2 columns small-centered" >
                Succeed: {{mergedTasks}}
            </div>

            <div class="small-2 columns small-centered" >
                Warning: {{warningTasks}}
            </div>

            <div class="small-2 columns small-centered" >
                Failed: {{failedTasks}}
            </div>

            <div class="small-2 columns small-centered" >
                Ignore: {{ignoredTasks}}
            </div>

            <div class="small-12 columns small-centered" >
                <div class="progress" role="progressbar" tabindex="0" aria-valuenow="{{completedTasks}}" aria-valuemin="0" aria-valuemax="{{tasks}}">
                    <div class="progress-meter" v-bind:style="fillstyle"></div>
                </div>
            </div>
        </div>

        <br>
        <div class="row align-center" v-if="hasButton">
            <div class="small-12 columns small-centered" >
                <button  v-for="button in buttons" class="button {{button[2] || ''}}" @click="close(button)" track-by="$index" id="userdialog-button-{{button[0]}}" :disabled="button[3]">
                    {{button[1]}}
                </button>
            </div>
        </div>

        <button class="close-button" data-close aria-label="Close modal" type="button">
            <span aria-hidden="true">&times;</span>
        </button>
    </div>
</template>

<style>
#userdialog .button {
    padding-left:15px;
    padding-right:15px;
    margin-left:30px;
    margin-right:30px;
}
#userdialog .small-centered {
    text-align:center;
}
#userdialog .detail_name {
    font-weight:bold;
    text-align: right;
    padding-right:5px;
    background:white;
}
#userdialog .detail_value {
    text-align: left;
    padding-left:5px;
}
#userdialog .header {
    text-align: left;
    font-weight:bold;
}
</style>

<script>
  import { $,Vue,utils } from 'src/vendor.js'
  export default {
    data: function () {
      return {
        classes:"small",
        title:"",
        //[['msg',columnSize,'classes'],]
        //[['buttonvalue','buttontext','classes'],]
        buttons:[],
        messages:[],
        tasks:null,
        succeedTasks:null,
        mergedTasks:null,
        failedTasks:null,
        warningTasks:null,
        ignoredTasks:null,
        callback:null,
        value:null,
        defaultValue:null,
        targetWindow:null,
      }
    },
    computed: {
      loading: function () { return this.$root.loading },
      utils: function () { return this.$root.utils },
      hasButton:function() {
        return this.buttons.length > 0
      },
      hasProgressBar:function() {
        return this.tasks > 0
      },
      completedTasks:function() {
        return this.succeedTasks + this.failedTasks + this.warningTasks + this.ignoredTasks
      },
      fillstyle:function() {
        return "width:" + (this.completedTasks / this.tasks) * 100 + "%"
      },
    },
    methods: {
      //options
      //title: dialog title
      //messages: 
      // 1. string. 
      // 2. array of string or [message(string), columns,type(link, radio, checkbox,input,text(default)), {element properies,event handlers,classes}  ]
      //buttons: array of [value,"button name",button class,disable status,click event]
      //defaultOption: used if user close the dialog 
      //callback: called if user click one button or have a defaultOption
      show:function(options) {
        if (options === undefined) {
            $("#userdialog").foundation('open')
            return
        }
        var vm = this
        this.classes = options.classes || "small"
        this.title = options.title || ""
        this.messages.splice(0,this.messages.length)
        var messageLine = null
        if (Array.isArray(options.messages)) {
            $.each(options.messages,function(index,line){
                vm.addMessage(line,false)
            })
        } else {
            this.messages.push([[options.messages,12]])
        }
        this.buttons = (options.buttons === undefined)?[[true,"Ok"],[false,"Cancel"]]:(options.buttons || [])
        this.callback = options.callback
        this.defaultOption = options.defaultOption === undefined?null:options.defaultOption
        this.option = null
        this.tasks = options.tasks
        this.succeedTasks = this.hasProgressBar?0:null
        this.failedTasks = this.hasProgressBar?0:null
        this.warningTasks = this.hasProgressBar?0:null
        this.ignoredTasks = this.hasProgressBar?0:null
        this.mergedTasks = this.hasProgressBar?0:null
        this._initData = options.initData || null
        this._initFunc = options.initFunc || null
        this.$nextTick(function(){
            if (vm._initFunc) {
                vm._initFunc()
            }
            $("#userdialog").foundation('open')
        })
      },
      close:function(button) {
        if (button && button[4]) {
            if (button[4](button,this.getData()) === false) {
                return
            }
        }
        this.option = (button && button[0] !== undefined)?button[0]:this.defaultOption
        $("#userdialog").foundation('close')
      },
      addMessage:function(message) {
        messageLine = []
        this.messages.push(messageLine)
        if (Array.isArray(message)) {
            $.each(message,function(index,column){
                if (Array.isArray(column)) {
                    messageLine.push(column)
                } else {
                    messageLine.push([column,12])
                }
            })
        } else {
            messageLine.push([message,12])
        }
      },
      addSucceedTask:function() {
        this.succeedTasks += 1
      },
      addWarningTask:function() {
        this.warningTasks += 1
      },
      addFailedTask:function() {
        this.failedTasks += 1
      },
      addIgnoredTask:function() {
        this.ignoredTasks += 1
      },
      addMergedTask:function() {
        this.mergedTasks += 1
      },
      addTasks:function(newTasks) {
        this.tasks += newTasks
      },
      isLink:function(msg) {
        this._linkRe = this._linkRe || /^\s*https?\:\/\/.+/i
        return this._linkRe.test(msg)
      },
      messageAttr:function(msg,attr,defaultValue) {
        return (msg[2] && msg[2][attr])?msg[2][attr]:defaultValue
      },
      messageClass:function(msg) {
        return this.messageAttr(msg,"class","")
      },
      messageType:function(msg) {
        return this.messageAttr(msg,"type","show")
      },
      messageName:function(msg) {
        return this.messageAttr(msg,"name","")
      },
      getValue:function(msg) {
        if (this._initData && this.messageName(msg) in this._initData) {
            return this._initData[this.messageName(msg)]
        } else {
            return msg[0]
        }
      },
      isChecked:function(msg) {
        if (this._initData && this.messageName(msg) in this._initData) {
            value = this._initData[this.messageName(msg)]
            if (Array.isArray(value)) {
                return value.indexOf(msg[0])
            } else {
                return value === msg[0]
            }
        } else {
            return this.messageAttr(msg,"checked",false)
        }
      },
      getData:function(){
        result = {}
        $("#userdialog input").each(function(index){
            if ($(this).prop("disabled")) {
                //is disabled,ignore
                return
            } else if ( $(this).val().trim().length === 0) {
                //is empty,ignore
                return
            } else if ( ["radio","checkbox"].indexOf($(this).prop("type").toLowerCase()) >= 0 && !($(this).prop("checked")) ) {
                //is not checked
            } else if (!($(this).prop("name") in result)) {
                // is not in results
                result[$(this).prop("name")] = $(this).val().trim()
            } else if ( typeof result[$(this).prop("name")] === "string") {
                //is string value, change it to array
                result[$(this).prop("name")] = [result[$(this).prop("name")],$(this).val().trim()]
            } else {
                //is array value, append the new value
                result[$(this).prop("name")].push($(this).val().trim())
            }
        })
        return result
      },
      processEvent:function(eventHandler,ev) {
        if (eventHandler) {
            eventHandler(ev)
        }
      }
    },
    ready: function () {
      var vm = this
      var dialogStatus = this.loading.register("dialog","Dialog Component")
      dialogStatus.phaseBegin("initialize",100,"Initialize")

      $("#userdialog").on("open.zf.reveal",function(){
        $("#userdialog").css("top",Math.floor(($("#userdialog").parent().height() - utils.getHeight($("#userdialog"))) / 2) + "px" )
      })

      $("#userdialog").on("closed.zf.reveal",function(){
        vm.messages.splice(0,vm.messages.length)
        vm.buttons.splice(0,vm.buttons.length)
        vm.revision += 1
        if (vm.callback) {
            var value = ((vm.option === null || vm.option === undefined )?vm.defaultOption:vm.option)
            if (value !== null && value !== undefined) {
                vm.callback(value,vm.getData())
            }
            vm.callback = null
        }
      })

      dialogStatus.phaseEnd("initialize")
    }
  }
</script>
