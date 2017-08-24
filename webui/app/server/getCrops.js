import { Meteor } from 'meteor/meteor';
import Future from 'fibers/future'; 
import { Queries, isQuery } from '../queries'

const fs = Npm.require('fs');
const exec = Npm.require('child_process').exec;

// TODO: OMG fix this.
const bag_path   = "/local/scratch/mot/data/bags/",
      bg_path    = "/local/scratch/mot/data/backgrounds/",
      util_path  = "/local/scratch/mot/util/",
      video_path = "/mnt/SIA/"
      


function bagPath(day, bagName){
    return  bag_path + day + "/" + bagName.replace(/[\/|\\]/g, "SLASH")
}


function findVideoFileHack(day, bagName, cb){
    const fuzzBag = bagName.replace(/[_.]|tracking|db/g, ""),
          file = day + "/" + fuzzBag.replace(/[\/|\\]/g, "SLASH") + "*", // Kill slashes
          cmd = "find " + video_path + file
    exec(cmd, {cwd: util_path, maxBuffer: Infinity}, (err, stdout, stderr) => {
        cb(err, stdout.toString().split("\n")[0], stderr.toString())
    })
}

function findBackgroundFileHack(day, bagName, cb){
    const fuzzBag = bagName.replace(/[_.]|tracking|db/g, ""),
          file = day + "/" + fuzzBag.replace(/[\/|\\]/g, "SLASH") + "*", // Kill slashes
          cmd = "find " + bg_path + file
    exec(cmd, {cwd: util_path, maxBuffer: Infinity}, (err, stdout, stderr) => {
        cb(err, stdout.toString().split("\n")[0], stderr.toString())
    })
}

function getParticlesToCrop(day, bagName, kind, flow, target, args, cb){
    const bag = bagPath(day, bagName)
          query = "particles_by_" + kind + "_with_flow_near " + flow + " " + target + " " + args.join(" ")
          cmd = util_path + "Query.py " + bag + " " + query
    console.info(cmd)
    exec(cmd, {cwd: util_path, maxBuffer: Infinity}, (err, stdout, stderr) => {
        console.info(stdout.toString())
        cb(err, JSON.parse(stdout.toString()))
    })
}


function getParticleCrop(day, bagName, video, background, id, cb){
    const bag = bagPath(day, bagName)
          cmd = util_path + "Cropper.py " + video + " " + bag + " - " + " -b " + background + " -p " + id
    console.info(cmd)
    exec(cmd, {cwd: util_path, maxBuffer: Infinity}, (err, stdout, stderr) => {
        //console.info(stdout.toString())
        cb(err, stdout)
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
        
        
        var vfuture = new Future()
        console.info("Searching for source video")
        findVideoFileHack(day, bagName, (err, res, stderr) => vfuture.return(res))
        
        var bfuture = new Future()
        console.info("Searching for existing background")
        findBackgroundFileHack(day, bagName, (err, res, stderr) => bfuture.return(res))
        
        var video = vfuture.wait(); if (!video){ return; }
        var background = bfuture.wait(); if (!background){ return; }
        
        
        console.info("Found video at", video, "and background at", background)
        
        
        var particlesGroups = points.map((p) => {
            var fut = new Future()
            var resolve = fut.resolver()
            var flow = p.flow
            var target = kind == "category" ? p.trace : (p.trace == 0 ? "Dark" : "Light")
            getParticlesToCrop(day, bagName, kind, flow, target, args, (err, res) => {
                resolve(err, {name: targetToLabel(target), particles: res})
            })
            return fut
        }).map((future) => future.wait())
        
        
        var crops = particlesGroups.map((pg) => {
            return {name: pg.name, list: pg.particles.map((p) => {
                var fut = new Future()
                var resolve = fut.resolver()
                getParticleCrop(day, bagName, video, background, p.id, (err, res) => {
                    var png64 = res.toString()
                    resolve(err, {id: p.id, png: "data:image/png;base64," + png64})
                })
                return fut
            }).map((future) => future.wait())}
        })
        
        
        return crops
    }
})
