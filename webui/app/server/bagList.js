import { Meteor } from 'meteor/meteor';
import Future from 'fibers/future'; 

const fs = Npm.require('fs');
// const exec = require('child_process').exec;

// TODO: OMG fix this.
const path = "/local/scratch/mot/data/bags/"

Meteor.methods({
    bagList: function bagList(dayName){
        var future = new Future();
        fs.readdir(path + dayName, function(err, res){                         //  *\|/*  only .db files
            res = res.filter(function(file){ return file.match(/^.*\.(db)$/i) }).sort()
            err ? future.throw(err) : future.return(res);
        })
        return future.wait();
    }
})
