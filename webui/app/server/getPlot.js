import { Meteor } from 'meteor/meteor'
import Future from 'fibers/future'
import { Queries, isQuery } from '../queries'

const fs = Npm.require('fs');
const exec = Npm.require('child_process').exec;

// TODO: OMG fix this.
const bag_path = "/local/scratch/mot/data/bags/",
     util_path = "/local/scratch/mot/util/"

Meteor.methods({
    getPlot: function getPlot(day, bagName, query, args){
        
        if(!query){   return "Select a Query" }
        if(!day){     return "Select a Day"   }
        if(!bagName){ return "Select a Bag"   }
        
        if (!Queries.includes(query)){ return "Invalid Query" } 
        
        if (!args) { args = [] }
        
        var future = new Future(),
            file = day + "/" + bagName.replace(/[\/|\\]/g, "SLASH"), // Kill slashes
            cmd = util_path + "Plotter.py " + query + " " + bag_path + file + " " + args.join("")
        
        exec(cmd, {cwd: util_path, maxBuffer: Infinity}, (err, stdout, stderr) => {
            err ? future.throw(err) : future.return(JSON.parse(stdout.toString()))
        }) 
        
        return future.wait()
        
    }
})
