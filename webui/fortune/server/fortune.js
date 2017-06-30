import { Meteor } from 'meteor/meteor';
import Future from 'fibers/future'; 

const fs = Npm.require('fs');
const exec = require('child_process').exec;

// TODO: OMG fix this.
const path = "/local/scratch/mot/util/"

Meteor.methods({
    fortune: function readpydoc(file){
        var future = new Future();
        exec("fortune", function(err, stdout, stderr){
            if (err){
                future.throw(err)
            } else {
                future.return(stdout.toString());  
            }
          
        })
        return future.wait();
    }
})