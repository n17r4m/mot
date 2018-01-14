import { Meteor } from 'meteor/meteor';
import Future from 'fibers/future'; 
import { Queries, isQuery } from '../queries'

const fs = Npm.require('fs');
const exec = Npm.require('child_process').exec;

// TODO: OMG fix this.
const data_path   = "/home/mot/data/experiments/",
      py_path  = "/home/mot/py/"
      


function bagPath(day, bagName){
    return  bag_path + day + "/" + bagName.replace(/[\/|\\]/g, "SLASH")
}





function getParticlesToCrop(experiment, kind, flow, target, args, cb){
    const cmd = [
        py_path + "mot.py",
        "query",
        "particles_by_" + kind + "_with_flow_near",
        experiment, flow, target, args.join(" ")
    ].join(" ")
    
    console.info(cmd)
    
    
    
    exec(cmd, {cwd: py_path, maxBuffer: Infinity}, (err, stdout, stderr) => {
        cb(err, JSON.parse(stdout.toString()))
    })
}


function getParticleCrops(experiment, fp_pairs, cb){
    const query = "crops " + fp_pairs.map((fp) => fp.join(",")).join(" "),
          cmd = util_path + "Query.py " + experiment + " " + query
    exec(cmd, {cwd: util_path, maxBuffer: Infinity}, (err, stdout, stderr) => {
        str = stdout.toString()
        // console.info(str)
        cb(err, JSON.parse(stdout.toString()))
    })
}


function targetToLabel(target){
    switch (target){
        case 0: return "Undefined"
        case 1: return "Unknown"
        case 2: return "Bitumen"
        case 3: return "Sand"
        case 4: return "Bubble"
        default: return target
    }
}


Meteor.methods({
    getCrops: function getCrops(experiment, query, points, args){
        
        if(!query){      return "Select a Query"         }
        if(!experiment){ return "Select an experiment"   }
        
        if (!Queries.includes(query)){ return "Invalid Query" } 
        if (!points) { points = [] }
        if (!args) { args = [] }
        
        const kind = query.match(/category/) ? "category" : "intensity"
        
        
        var particlesGroups = points.map((p) => {
            var fut = new Future()
            var resolve = fut.resolver()
            var flow = p.flow
            var target = kind == "category" ? p.trace : (p.trace == 0 ? "Dark" : "Light")
            getParticlesToCrop(experiment, kind, flow, target, args, (err, particles) => {
                resolve(err, {name: targetToLabel(target), particles: particles})
            })
            return fut
        }).map((future) => future.wait())
        
        var crops = particlesGroups.map((pg) => {
            
            var fut = new Future()
            var resolve = fut.resolver()
            
            fp_pairs = pg.particles.map((fp) => [fp.frame, fp.particle])
            
            getParticleCrops(experiment, fp_pairs, (err, crops) => {
                resolve(err, {name: pg.name, list: crops})
            })

            return fut
            
        }).map((future) => future.wait())
        
        
        return crops
    }
})
