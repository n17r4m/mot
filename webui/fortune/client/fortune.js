import { Template } from 'meteor/templating';


import './fortune.html';



Template.fortune.onCreated(function fortune() {
  this.fortune = new ReactiveVar("")
  Meteor.call("fortune", (err, fortune) => {
    err ? this.fortune.set("Error") : this.fortune.set(fortune)
  })
});

Template.fortune.helpers({
  fortune() { 
    return Template.instance().fortune.get().replace(/\n/g, "<br>") }
});
