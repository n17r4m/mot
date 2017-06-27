import { Template } from 'meteor/templating';
import { ReactiveVar } from 'meteor/reactive-var';

import './source.html';


Template.source.onCreated(function source(arg1) {
  var self = this
  self.code = new ReactiveVar("")
  Meteor.call("source", this.data.data(), function(err, code){
    if (err){
        self.code.set("Error")
    } else {
        self.code.set(code)
    }
  })
});

Template.source.helpers({
  source(file) { return Template.instance().code.get() }
});



Template.pydoc.onCreated(function source(arg1) {
  var self = this
  self.doc = new ReactiveVar("")
  Meteor.call("pydoc", this.data.data(), function(err, html){
    console.info(err, html)
    if (err){
        self.doc.set("Error")
    } else {
        self.doc.set(html)
    }
  })
});

Template.pydoc.helpers({
  pydoc(file) { return Template.instance().doc.get() }
});

