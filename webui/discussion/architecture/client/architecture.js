import { Template } from 'meteor/templating';


import './architecture.html';

Template.architecture_modules.onCreated(function source(arg1) {
  var self = this
  self.source_list = new ReactiveVar([])
  Meteor.call("source_list", function(err, list){
    console.info(err, list)
    if (err){
        self.source_list.set(["Error"])
    } else {
        self.source_list.set(list)
    }
  })
});

Template.architecture_modules.helpers({
  list() { return Template.instance().source_list.get() }
});
