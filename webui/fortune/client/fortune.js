import { Template } from 'meteor/templating';


import './fortune.html';



Template.fortune.onCreated(function fortune(verbose) {
  var self = this
  self.fortune = new ReactiveVar("")
  Meteor.call("fortune", function(err, fortune){
    if (verbose){ console.info("Fortune:", fortune) }
    if (err){
        self.fortune.set("Error")
    } else {
        self.fortune.set(fortune)
    }
  })
});

Template.fortune.helpers({
  fortune(verbose) { 
    if (verbose) { console.info("Your fortune is:", Template.instance().fortune.curValue) }
    return Template.instance().fortune.get().replace(/\n/g, "<br>") }
});
