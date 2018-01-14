import { Meteor } from 'meteor/meteor'
import Future from 'fibers/future'
import { Queries, isQuery } from '../queries'

const fs = Npm.require('fs');
const exec = Npm.require('child_process').exec;

// TODO: OMG fix this.
const mot_path = "/home/mot/py/"


Meteor.methods({
    getPlot: function getPlot(experiment, query, args){
        
        if(!experiment){ return "Select a Experiment" }
        if(!query){      return "Select a Query"      }
        
        if (!Queries.includes(query)){ return "Invalid Query" } 
        
        if (!args) { args = [] }
        
        
        
        var future = new Future(),
            cmd = mot_path + "mot.py plot " + query + " " + experiment + " " + args.join("")
        
        console.log(cmd)
        
        exec(cmd, {cwd: mot_path, maxBuffer: Infinity}, (err, stdout, stderr) => {
            err ? future.throw(err) : future.return(JSON.parse(stdout.toString()))
        }) 
        
        return future.wait()
    },
    
    
    // not updated.
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
