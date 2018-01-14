import { Template } from 'meteor/templating'
import { Session } from 'meteor/session'
import { FlowRouter } from 'meteor/ostrio:flow-router-extra'
import { Meteor } from 'meteor/meteor'
import { Client } from 'pg'

import './upload.html';




Template.upload.onCreated(function sub(){
    this.experiment_list = new ReactiveVar([]);
    Meteor.call("experiments", (err, res) => {
        this.experiment_list.set(res.rows)
    })
})



Template.upload.helpers({
    experiments() { return Template.instance().experiment_list.get() }
})

Template.upload.events({
    "click table.experiments tr": (event, instance) => {
        FlowRouter.go("/app/experiment/:experiment", {
            experiment: event.currentTarget.dataset.experiment
        })
    }
    
})



