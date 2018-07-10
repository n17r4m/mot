import { Template } from 'meteor/templating'
import { Session } from 'meteor/session'
import { FlowRouter } from 'meteor/ostrio:flow-router-extra'
import { ReactiveVar } from 'meteor/reactive-var';

import './experiment.html';


Template.experiment.onCreated(function sub(){
    this.experiment = new ReactiveVar()
    this.videos = new ReactiveVar([])
    Meteor.call("experiment", Session.get("experiment"), (err, res) => {
        this.experiment.set(res.rows[0])
    }),
    Meteor.call("experiment_videos", Session.get("experiment"), (err, res) => {
        this.videos.set(res)
    })
})

Template.experiment.helpers({
    experiment() { return Template.instance().experiment.get() },
    videos() { return Template.instance().videos.get() }
})

Template.experiment.events({
    "change #video_select": function(e) {
        exp = Session.get("experiment")
        vid = e.currentTarget.value
        if(vid) {
            $("#video")[0].src = FlowRouter.path("/data/experiments/:e/:v", {e: exp, v: vid})
        } else {
            $("#video")[0].src = ""
        }
    },
    "change,click #rate_select": function(e) {
        r = parseFloat(e.currentTarget.value)
        $("#video")[0].playbackRate = r
    },
    "click button.verify": function(e) {
        FlowRouter.go("/app/verify/:experiment", {
            experiment: Session.get("experiment")
        })
    }
})







/*
// CANVAS DAWING STUFF

Template.experiment.onCreated(function sub(){
    Session.setDefault("rate", 1.0)
    this.source = document.createElement("SOURCE")
    this.experiment = Experiments.findOne(Session.get("experiment"))
    this.source.src = FlowRouter.path("/data/experiments/:id/extraction.mp4", {id: this.experiment._id})
    this.video = document.createElement("VIDEO")
    this.video.appendChild(this.source)
    this.video.autoplay = true
    this.video.loop = true
})


Template.experiment.onRendered(function rendered(){
    let experiment = this.experiment
    this.video.addEventListener( "loadedmetadata", function (e) {
        let vw = this.videoWidth
        let vh = this.videoHeight
        
        let canvas = $('#tracking')[0]
        let context = tracking.getContext('2d')
        let cw = Math.floor(canvas.clientWidth)
        let ch = Math.floor(cw * (vh/vw))
        canvas.width = cw
        canvas.style.height = ch + "px"
        canvas.height = ch
        
        this.addEventListener('play', function(){
            
                
            var tracks = {}
            console.info("Loading tracks")
            Tracks.find({}, {sort: {number: 1}}).forEach((track, i) => {
                tracks[i] = track
            })
            console.info("Got Tracks")
            
            drawLoop(experiment, this, context, cw, ch, tracks)()
        },false)
        
    }, false )
    
    
    
})


Template.experiment.onDestroyed(function destroyed(){
    this.video.pause()
})


function drawLoop(e, v, c, w, h, t){
    
    return function drawTracks() {
        if(v.paused || v.ended) return false;
        
        
        v.playbackRate = Session.get("rate")
        
        c.globalAlpha = 1.0;
        // c.drawImage(v, 0, 0) // , w, h);
        
        f = Math.ceil(e.startframe + (v.currentTime * 24))
        c.fillText  ("Frame: " + f,  10, 15);
        
        c.globalAlpha = 0.5;
        c.fillStyle = 'green';
        c.strokeStyle = '#003300';
        c.lineWidth = 1;
        
        t[f].locations.forEach((location) => {
            c.beginPath();
            c.arc(location.x, location.y, 5, 0, 2 * Math.PI, false);
            c.fill();
            c.stroke();
        })
        
        
        
        requestAnimationFrame(drawTracks);
    }
}

Template.experiment.helpers({
    experiment() { return Experiments.findOne(Session.get("experiment")) }
})

Template.experiment.events({
    "change select[name=rate]": function(e){
        Session.set("rate", parseFloat(e.currentTarget.value))
    }
})


*/