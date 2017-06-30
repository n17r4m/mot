import { Template } from 'meteor/templating';
import { ReactiveVar } from 'meteor/reactive-var';

import './source.html';


Template.source.onCreated(function source(arg1) {
  var self = this
  self.code = new ReactiveVar("")
  Meteor.call("source", self.data.data(), function(err, code){
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
  Meteor.call("pydoc", self.data.data(), function(err, html){
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

Template.pyhelp.onCreated(function source(arg1) {
  console.info(arg1, this)
  var self = this
  var file = self.data.data instanceof Function ? self.data.data() : self.data.data
  self.help = new ReactiveVar("")
  
  Meteor.call("pyhelp", file, function(err, text){
    if (err){
        self.help.set("Error")
    } else {
        self.help.set(text)
    }
  })
});

Template.pyhelp.helpers({
  pyhelp(file) { return Template.instance().help.get() }
});

