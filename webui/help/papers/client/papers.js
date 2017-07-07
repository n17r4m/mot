import { Template } from 'meteor/templating';


import './papers.html';

Template.papers.onCreated(function source() {
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


Template.papers.helpers({
  list() { return Template.instance().source_list.get() },
  about(source) { return about_source[source] || "" }
});
