<template>
    <div class="{{classes}} reveal" id="userdialog" data-reveal data-close-on-click='false'> 
        <h3>{{title}}</h3>
        <div v-for="line in messages" class="row" track-by="$index" >
            <div v-for="message in line" class="small-{{message[1]}} columns {{message[2] || ''}}" track-by="$index">
                 <pre>  {{message[0]}}</pre>
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
                <button  v-for="button in buttons" class="button {{button[2] || ''}}" @click="close(button[0])" track-by="$index">
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
</style>

<script>
  import { $,Vue } from 'src/vendor.js'
  export default {
    data: function () {
      return {
        classes:"small",
        title:"",
        //[['msg',columnSize,'classes'],]
        //[['buttonvalue','buttontext','classes'],]
        buttons:[],
        tasks:null,
        succeedTasks:null,
        mergedTasks:null,
        failedTasks:null,
        warningTasks:null,
        ignoredTasks:null,
        callback:null,
        value:null,
        defaultValue:null,
        revision:1,
      }
    },
    computed: {
      loading: function () { return this.$root.loading },
      hasButton:function() {
        return this.buttons.length > 0
      },
      messages:function() {
        return this.revision && (this._messages || []);
      },
      hasProgressBar:function() {
        return this.tasks > 0
      },
      completedTasks:function() {
        return this.succeedTasks + this.failedTasks + this.warningTasks + this.ignoredTasks
      },
      fillstyle:function() {
        return "width:" + (this.completedTasks / this.tasks) * 100 + "%"
      }
    },
    methods: {
      //options
      //title: dialog title
      //messages: 
      // 1. string. 
      // 2. array of string or [string, columns, classes]
      //buttons: array of [value,"button name"]
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
        this._messages.length = 0
        var messageLine = null
        if (Array.isArray(options.messages)) {
            $.each(options.messages,function(index,line){
                vm.addMessage(line)
            })
        } else {
            this._messages.push([[options.messages,12]])
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

        $("#userdialog").foundation('open')
        this.revision += 1
      },
      close:function(option) {
        this.option = (option === undefined)?this.defaultOption:option
        $("#userdialog").foundation('close')
      },
      addMessage:function(message) {
        messageLine = []
        this._messages.push(messageLine)
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
        this.revision += 1
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
      }
    },
    ready: function () {
      var vm = this
      this._messages = []
      var dialogStatus = this.loading.register("dialog","Dialog Component")
      dialogStatus.phaseBegin("initialize",100,"Initialize")

      $("#userdialog").on("closed.zf.reveal",function(){
        if (vm.callback) {
            var value = ((vm.option === null || vm.option === undefined )?vm.defaultOption:vm.option)
            if (value !== null && value !== undefined) {
                vm.callback(value)
            }
            vm.callback = null
        }
      })

      dialogStatus.phaseEnd("initialize")
    }
  }
</script>
