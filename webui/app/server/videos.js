import { Meteor } from 'meteor/meteor'
import Future from 'fibers/future'; 
import { readdir } from 'fs'

const fs = Npm.require('fs');

Meteor.methods({    
    experiment_videos(experiment){
        
        var future = new Future();
        // TODO: OMG fix me
        const experiment_path = `/home/mot/data/experiments/${experiment}`
        fs.readdir(experiment_path, function(err, res){
            if (res) {
                res = res.filter(function(file){ return file.match(/^.*\.(mp4|avi|mkv)$/i) })
                console.log(res)
                err ? future.throw(err) : future.return(res);
            } else {
                future.return([err]);
            }
        })
        return future.wait();
        
    }
})