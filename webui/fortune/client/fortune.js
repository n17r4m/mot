import { Template } from 'meteor/templating';


import './fortune.html';



Template.fortune.onCreated(function source(arg1) {
  var self = this
  self.fortune = new ReactiveVar("")
  Meteor.call("fortune", function(err, fortune){
    if (err){
        self.fortune.set("Error")
    } else {
        self.fortune.set(fortune)
    }
  })
});

Template.fortune.helpers({
  fortune() { return Template.instance().fortune.get() }
});
