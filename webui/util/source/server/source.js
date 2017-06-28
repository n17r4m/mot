import { Meteor } from 'meteor/meteor';
import Future from 'fibers/future'; 

const fs = Npm.require('fs');
const exec = require('child_process').exec;

// TODO: OMG fix this.
const path = "/local/scratch/mot/util/"

Meteor.methods({
    source: function readSourceFile(file){
        var future = new Future();
        
        file = file.replace(/[\/|\\]/g, "SLASH") // Kill slashes
        
        fs.readFile(path + file, function(err, res){
            if (err){
                future.throw(err)
            } else {
                future.return(res.toString());  
            }
          
        })
        return future.wait();
    },
    source_list: function readSourceDir(){
        var future = new Future();
        fs.readdir(path, function(err, res){
            res = res.filter(function(file){
                return file.match(/\.py$|\.m/g) // only .py files
            }).sort()
            if (err){
                future.throw(err)
            } else {
                future.return(res);
            }
          
        })
        return future.wait();
    },
    pydoc: function readpydoc(file){
        var future = new Future();
        
        file = file.replace(/[\/|\\]/g, "SLASH") // Kill slashes
        
        exec(path + "Documentor.py " + path + file, {cwd: path}, function(err, stdout, stderr){
            if (err){
                future.throw(err)
            } else {
                future.return(stdout.toString());  
            }
          
        })
        return future.wait();
    },
    pyhelp: function readpydoc(file){
        var future = new Future();
        
        file = file.replace(/[\/|\\]/g, "SLASH") // Kill slashes
        
        exec(path + file + " --help", {cwd: path}, function(err, stdout, stderr){
            if (err){
                future.throw(err)
            } else {
                future.return(stdout.toString());  
            }
          
        })
        return future.wait();
    }
})
