import { Meteor } from 'meteor/meteor';


Meteor.startup(() => {
  // code to run on server at startup
  var startup_time = new Date()
  var button_presses = 0
  Meteor.methods({
    "hello.stats": function(){ return {startup_time, button_presses} },
    "hello.button_press": function(){ return ++button_presses },
    
    "simulate.controls": function(){ return pyConfig("Simulator").args }
    
  })
  
});
