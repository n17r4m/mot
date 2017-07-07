import { Meteor } from 'meteor/meteor'
import Future from 'fibers/future'
import { Queries, isQuery } from '../queries'

const fs = Npm.require('fs');
const exec = require('child_process').exec;

// TODO: OMG fix this.
const bag_path = "/local/scratch/mot/data/bags/",
     util_path = "/local/scratch/mot/util/"

Meteor.methods({
    runQuery: function runQuery(bagName, query, args){
        
        if (!Queries.includes(query)){ return [] } 
        console.info(args)
        if (!args) { args = [] }
        
        var future = new Future(),
            file = bagName.replace(/[\/|\\]/g, "SLASH"), // Kill slashes
            cmd = util_path + "Query.py " + bag_path + file + " "
        
        exec(cmd + query + " " + args.join(" "), {cwd: util_path, maxBuffer: Infinity}, (err, stdout, stderr) => {
            err ? future.throw(err) : future.return(JSON.parse(stdout.toString()))
        })
        
        return future.wait()
        
    }
})
