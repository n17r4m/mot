

import './compare.html';
import './index.html';
import './simulate.html';
import './upload.html';


Template.hello.onCreated(function helloOnCreated() {
  // counter starts at 0
  var self = this
  this.startup_time = new ReactiveVar(new Date())
  this.button_presses = new ReactiveVar(0)
  Meteor.call("hello.stats", function(err, stats){
    self.startup_time.set(stats.startup_time)
    self.button_presses.set(stats.button_presses)
  })
});

Template.hello.helpers({
  startup_time() { return Template.instance().startup_time.get(); },
  button_presses() { return Template.instance().button_presses.get(); },
});

Template.hello.events({
  'click button'(event, instance) {
    // increment the counter when button is clicked
    Meteor.call("hello.button_press", function(err, button_presses){
      instance.button_presses.set(button_presses);
    })
  },
});





Template.simulate.onCreated(function helloOnCreated() {
  var self = this
  this.controls = new ReactiveVar([])
  Meteor.call("simulate.controls", function(err, controls){
    console.info(err, controls)
    self.controls.set(controls)
  })
});
Template.simulate.helpers({
  controls() { return Template.instance().controls.get(); },
});


