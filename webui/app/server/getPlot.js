import { Meteor } from 'meteor/meteor'
import Future from 'fibers/future'
import { Queries, isQuery } from '../queries'

const fs = Npm.require('fs');
const exec = Npm.require('child_process').exec;

// TODO: OMG fix this.
const bag_path = "/local/scratch/mot/data/bags/",
     util_path = "/local/scratch/mot/util/"


// remove slashes
function rs(path){ return path.replace(/[\/|\\]/g, "SLASH") }

Meteor.methods({
    getPlot: function getPlot(day, bagName, query, args){
        
        if(!query){   return "Select a Query" }
        if(!day){     return "Select a Day"   }
        if(!bagName){ return "Select a Bag"   }
        
        if (!Queries.includes(query)){ return "Invalid Query" } 
        
        if (!args) { args = [] }
        
        var future = new Future(),
            file = rs(day) + "/" + rs(bagName),
            cmd = util_path + "Plotter.py " + query + " " + bag_path + file + " " + args.join("")
        
        exec(cmd, {cwd: util_path, maxBuffer: Infinity}, (err, stdout, stderr) => {
            err ? future.throw(err) : future.return(JSON.parse(stdout.toString()))
        }) 
        
        return future.wait()
    },
    getPlots: function getPlots(experiments, query, args){
        if(!query){        return "Select a Query" }
        if(!experiments.length){  return "Select at least one experiment" }
        
        console.info(experiments, !experiments, query, args)
        
        if (!Queries.includes(query)){ return "Invalid Query" }
        if (!args) { args = [] }
        
        var future = new Future(),
            files = experiments.map((e) => bag_path + rs(e.day) + "/" + rs(e.bag)).join(" "),
            cmd = util_path + "Plotter.py " + query + " " + files + " " + args.join("")
        
        exec(cmd, {cwd: util_path, maxBuffer: Infinity}, (err, stdout, stderr) => {
            err ? future.throw(err) : future.return(JSON.parse(stdout.toString()))
        }) 
        
        return future.wait()
        
    }
})
