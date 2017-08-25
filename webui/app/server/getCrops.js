import { Meteor } from 'meteor/meteor';
import Future from 'fibers/future'; 
import { Queries, isQuery } from '../queries'

const fs = Npm.require('fs');
const exec = Npm.require('child_process').exec;

// TODO: OMG fix this.
const bag_path   = "/local/scratch/mot/data/bags/",
      util_path  = "/local/scratch/mot/util/"
      


function bagPath(day, bagName){
    return  bag_path + day + "/" + bagName.replace(/[\/|\\]/g, "SLASH")
}


function getParticlesToCrop(day, bagName, kind, flow, target, args, cb){
    const bag = bagPath(day, bagName)
          query = "particles_by_" + kind + "_with_flow_near " + flow + " " + target + " " + args.join(" ")
          cmd = util_path + "Query.py " + bag + " " + query
    exec(cmd, {cwd: util_path, maxBuffer: Infinity}, (err, stdout, stderr) => {
        cb(err, JSON.parse(stdout.toString()))
    })
}


function getParticleCrops(day, bagName, fp_pairs, cb){
    const bag = bagPath(day, bagName)
          query = "crops " + fp_pairs.map((fp) => fp.join(",")).join(" "),
          cmd = util_path + "Query.py " + bag + " " + query
    exec(cmd, {cwd: util_path, maxBuffer: Infinity}, (err, stdout, stderr) => {
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
    getCrops: function getCrops(day, bagName, query, points, args){
        
        console.info("getCrops")
        
        if(!query){   return "Select a Query" }
        if(!day){     return "Select a Day"   }
        if(!bagName){ return "Select a Bag"   }
        if (!Queries.includes(query)){ return "Invalid Query" } 
        if (!points) { points = [] }
        if (!args) { args = [] }
        
        var kind = query.match(/category/) ? "category" : "intensity"
        
        
        var particlesGroups = points.map((p) => {
            var fut = new Future()
            var resolve = fut.resolver()
            var flow = p.flow
            var target = kind == "category" ? p.trace : (p.trace == 0 ? "Dark" : "Light")
            getParticlesToCrop(day, bagName, kind, flow, target, args, (err, particles) => {
                resolve(err, {name: targetToLabel(target), particles: particles})
            })
            return fut
        }).map((future) => future.wait())
        
        
        var crops = particlesGroups.map((pg) => {
            
            var fut = new Future()
            var resolve = fut.resolver()
            
            fp_pairs = pg.particles.map((fp) => [fp.frame, fp.particle])
            getParticleCrops(day, bagName, fp_pairs, (err, crops) => {
                resolve(err, {name: pg.name, list: crops})
            })
            return fut
            
        }).map((future) => future.wait())
        
        
        return crops
    }
})
