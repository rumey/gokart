<template>
    <div class="{{classes}} reveal" id="userdialog" data-reveal data-close-on-click='false'> 
        <h3>{{title}}</h3>
        <div v-for="line in messages" class="row" track-by="$index" >
            <div v-for="message in line" class="small-{{message[1]}} columns {{message[2] || ''}}" track-by="$index">
                   <a>{{message[0]}}</a>
            </div>
        </div>

        <br>
        <div class="row align-center">
            <div class="small-12 columns small-centered" >
                <button  v-for="button in buttons" class="button {{button[2] || ''}}" @click="clickButton(button[0])" track-by="$index">
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
        messages:[],
        //[['buttonvalue','buttontext','classes'],]
        buttons:[],
        callback:null,
        value:null,
        defaultValue:null
      }
    },
    computed: {
      loading: function () { return this.$root.loading },
    },
    methods: {
      show:function(options) {
        var vm = this
        this.classes = options.classes || "small"
        this.title = options.title || "Hi"
        this.messages.length = 0
        var messageLine = null
        if (Array.isArray(options.messages)) {
            $.each(options.messages,function(index,line){
                messageLine = []
                vm.messages.push(messageLine)
                if (Array.isArray(line)) {
                    $.each(line,function(index,message){
                        if (Array.isArray(message)) {
                            messageLine.push(message)
                        } else {
                            messageLine.push([message,12])
                        }
                    })
                } else {
                    messageLine.push([line,12])
                }
            })
        } else {
            this.messages.push([[options.messages,12]])
        }
        this.buttons = options.buttons || [[true,"Ok"],[false,"Cancel"]]
        this.callback = options.callback
        this.defaultOption = options.defaultOption === undefined?null:options.defaultOption
        this.option = null

        $("#userdialog").foundation('open')
      },
      clickButton:function(option) {
        this.option = option
        $("#userdialog").foundation('close')
      }
    },
    ready: function () {
      var vm = this
      var dialogStatus = this.loading.register("dialog","Dialog Component")
      dialogStatus.phaseBegin("initialize",100,"Initialize")

      $("#userdialog").on("closed.zf.reveal",function(){
        if (vm.callback) {
            var value = (vm.option === null?vm.defaultOption:vm.option)
            if (value !== null) {
                vm.callback(value)
            }
            vm.callback = null
        }
      })

      dialogStatus.phaseEnd("initialize")
    }
  }
</script>
