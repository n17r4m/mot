import { Template } from 'meteor/templating'
import { Session } from 'meteor/session'
import { FlowRouter } from 'meteor/ostrio:flow-router-extra'


import './upload.html';




Template.upload.onCreated(function sub(){
    this.subscribe('experiments')
})



Template.upload.helpers({
    experiments() { return Experiments.find({}, {sort: { day: -1, name: -1, method: 1 }}) }
})

Template.upload.events({
    "click table.experiments tr": (e) => {
        FlowRouter.go("/app/experiment/:experiment", {experiment: e.currentTarget.dataset.experiment})
    }
    
})