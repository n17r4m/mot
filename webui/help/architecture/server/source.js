import { Meteor } from 'meteor/meteor';
import Future from 'fibers/future'; 

const fs = Npm.require('fs');
const exec = require('child_process').exec;

// TODO: OMG fix this.
const path = "/local/scratch/mot/util/"

Picker.route('/schema.svg', function (params, req, res, next){
  
  // read the file
  try {
    var chunk = fs.createReadStream(path + "schema/schema.svg"),
        headers = {"Content-type": "image/svg+xml"},
        statusCode = 200
  } catch (e) {
    var headers = {},
        statusCode = 404
  }

  // out content of the file to the output stream
  res.writeHead(statusCode, headers);
  chunk.pipe(res);
});

Meteor.methods({
    source: function readSourceFile(file){
        var future = new Future();
        
        file = file.replace(/[\/|\\]/g, "SLASH") // Kill slashes
        
        fs.readFile(path + file, function(err, res){
            err ? future.throw(err) : future.return(res.toString());
          
        })
        return future.wait();
    },
    source_list: function readSourceDir(){
        var future = new Future();
        fs.readdir(path, function(err, res){
            res = res.filter(function(file){
                return file.match(/^.*\.(py|m)$/i) // only .py and .m files
                    && file != "__init__.py"    // no __init__ files
            }).sort()
            err ? future.throw(err) : future.return(res);
          
        })
        return future.wait();
    },
    pydoc: function readpydoc(file){
        var future = new Future();
        
        file = file.replace(/[\/|\\]/g, "SLASH") // Kill slashes
        
        exec(path + "Documentor.py " + path + file, {cwd: path}, function(err, stdout, stderr){
            err ? future.throw(err) : future.return(stdout.toString())
          
        })
        return future.wait();
    },
    pyhelp: function readpydoc(file){
        var future = new Future();
        
        file = file.replace(/[\/|\\]/g, "SLASH") // Kill slashes
        
        exec(path + file + " --help", {cwd: path}, function(err, stdout, stderr){
            err ? future.throw(err) : future.return(stdout.toString())
          
        })
        return future.wait();
    }
})
