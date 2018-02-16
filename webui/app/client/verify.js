import { Template } from 'meteor/templating'
import { Session } from 'meteor/session'
import { FlowRouter } from 'meteor/ostrio:flow-router-extra'
import { ReactiveVar } from 'meteor/reactive-var';

import './verify.html';


Template.verify.onCreated(function sub(){
    this.experiment = new ReactiveVar()
    this.segments = new ReactiveVar([])
    this.segment = new ReactiveVar()
    this.categories = new ReactiveVar([])
    this.particles = new ReactiveVar([])
    this.currentParticle = new ReactiveVar()
    
    Meteor.call("experiment", Session.get("experiment"), (err, res) => {
        this.experiment.set(res.rows[0])
    })
    Meteor.call("experiment_segments", Session.get("experiment"), (err, res) => {
        this.segments.set(res.rows)
    })
    Meteor.call("categories", (err, res) => {
        this.categories.set(res.rows)
    })
    
})


Template.verify.onRendered(function prep(){
    this.$("select.dropdown").dropdown()
    this.$('input.radio.checkbox').checkbox()
    
    const instance = this
    this.arrowNavigation = function(e) {
        // Left/Right              "left"                   "right"
        let direction = e.keyCode == 37 ? -1 : (e.keyCode == 39 ? 1 : 0)
        if (direction != 0){
            let curParticle = instance.currentParticle.get()
            if (curParticle) {
                let newIdx = parseInt(curParticle.idx, 10) + direction
                let ps = instance.particles.get()
                if (newIdx < ps[curParticle.category].length && newIdx >= 0){
                    ps[curParticle.category][curParticle.idx].viewing = false
                    ps[curParticle.category][newIdx].viewing = true
                    instance.currentParticle.set({category: curParticle.category, idx: newIdx})
                    instance.particles.set(ps)
                    
                }
            }
        }
        // Prev/Next             "p"                     "n"
        direction = e.keyCode == 80 ? -1 : (e.keyCode == 78 ? 1 : 0)
        if (direction != 0){
            e.preventDefault()
            let cur = $("select[name=segment] > option:selected")
            if (direction > 0) { var opt = cur.next() } else { var opt = cur.prev() }
            if (opt) {
                $("select[name=segment").dropdown("set selected", opt.val())
                loadParticles(instance, Session.get("experiment"), opt.val())
            }
        }
    }
    
    // Almost same thing as "click img.particle" event below, using arrow keys.
    $(window).on("keydown", this.arrowNavigation)
})


Template.verify.onDestroyed(function teardown(){
    $(window).off('keydown', this.arrowNavigation)
})



Template.verify.helpers({
    experiment() { return Template.instance().experiment.get() },
    segments()   { return Template.instance().segments.get()   },
    categories() { return Template.instance().categories.get() },
    particles(category)  { 
        return Template.instance().particles.get()[category]
    },
    particle1_url(experiment, particle) {
        return `/mot/data/experiments/${experiment.experiment}/${particle.frames[0]}/${particle.tracks[0]}.jpg`
    },
    particleN_url(experiment, frame, track) {
        return `/mot/data/experiments/${experiment.experiment}/${frame}/${track}.jpg`
    },
    particles_track(category, idx) {
        console.info(category, idx)
        console.info(Template.instance())
        let ps = Template.instance().particles.get()
        let pt = ps && ps[category] && ps[category][idx]
        if (pt) {
            console.info(pt)
            return pt.tracks.map((t, i) => {
                return {track: t, frame: pt.frames[i]}
            })
        }
    }
})


function loadParticles(instance, exp, seg){
    const val_filter = $("input[name=val_filter]:checked").val()
    if (exp && seg){
        instance.segment.set(seg)
        instance.particles.set({})
        instance.currentParticle.set(undefined)
        instance.categories.get().forEach((cat) => {
            Meteor.call("experiment_particles_by_segment_category", exp, seg, cat.category, val_filter, (err, res) => {
                let ps = instance.particles.get()
                ps[cat.category] = res.rows
                instance.particles.set(ps)
            })
        })
    }
}


Template.verify.events({
    "click button.return": function(e){
        FlowRouter.go("/app/experiment/:experiment", {
            experiment: Session.get("experiment")
        })
    },
    "change select[name=segment]": function(e, instance) {
        const exp = Session.get("experiment")
        const seg = e.currentTarget.value
        loadParticles(instance, exp, seg)
    },
    "click button.refresh": function(e, instance) {
        const exp = Session.get("experiment")  
        const seg = instance.segment.get()
        loadParticles(instance, exp, seg)
    },
    "click input[name=val_filter]": function(e, instance) {
        const exp = Session.get("experiment")  
        const seg = instance.segment.get()
        loadParticles(instance, exp, seg)
    },
    "click img.particle": function(e, instance) {
        
        let ps = instance.particles.get()
        let curParticle = instance.currentParticle.get()
        if (curParticle) {
            ps[curParticle.category][curParticle.idx].viewing = false
        }
        let data = e.currentTarget.dataset
        ps[data.category][data.idx].viewing = true
        instance.currentParticle.set(data)
        instance.particles.set(ps)
    },
    "click button.change_category": function(e, instance) {
        let {particle, category} = e.currentTarget.dataset
        instance.$("button.change_category").removeClass("active")
        
        Meteor.call("update_particle_category", particle, category, (err, res) => {
            if (!err) { $(e.currentTarget).addClass("active") }
        })
        
    },
    "click button[name=valid]": function(e, instance) {
        let {particle} = e.currentTarget.dataset
        instance.$("button[name=invalid]").removeClass("active")
        Meteor.call("update_particle_validity", particle, true, (err, res) => {
            if (!err) { $(e.currentTarget).addClass("active") }
        })
    },
    "click button[name=invalid]": function(e, instance) {
        let {particle} = e.currentTarget.dataset
        instance.$("button[name=valid]").removeClass("active")
        Meteor.call("update_particle_validity", particle, false, (err, res) => {
            if (!err) { $(e.currentTarget).addClass("active") }
        })
    },
    
})