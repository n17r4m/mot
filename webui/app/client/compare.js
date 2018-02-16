import { Template } from 'meteor/templating';
import { ReactiveVar } from 'meteor/reactive-var';
import { Queries } from '../queries'

import './compare.html';



Template.compare.onCreated(function makeVars(){
    
    this.queries = new ReactiveVar([])
    this.days = new ReactiveVar([])
    this.day = new ReactiveVar()
    this.experiments = new ReactiveVar([])
    this.selectedExperiments = new ReactiveVar([])
    this.query = new ReactiveVar()
    this.crops = new ReactiveVar([])
    
    Meteor.call('experiment_days', (err, res) => { 
        if (err){ alert(err) }
        else { this.days.set(res.rows) }
    })
    
})


Template.compare.onRendered(function updateDayList(){
    this.$("select.dropdown").dropdown()
    this.queries.set(Queries.filter((q) => q.type == "compare"))
})

Template.compare.helpers({
    queries()  { return Template.instance().queries.get()     },
    dayList()  { return Template.instance().days.get()        },
    nameList() { return Template.instance().experiments.get() },
    
    experiment() { return Template.instance().selectedExperiments.get() },
    crops()      { return Template.instance().crops.get()       },
    arg()        {  
        let q = Queries.get(Template.instance().query.get())
        if (q) return q.args || []; else return []
    }
});

Template.compare.events({
    "change select[name=query]": function bagSelect(event, instance){
        instance.query.set(event.currentTarget.value)
        updateChart(instance)
    },
    "change select[name=day]": function daySelect(event, instance){
        instance.day.set(event.currentTarget.value)
        Meteor.call("experiments_on_day", instance.day.get(), (err, res) => {
            if (err) { alert(err) } 
            else { instance.experiments.set(res.rows) }
        })
    },
    "change select[name=experiment]": function experimentSelect(event, instance){
        
        var name = event.currentTarget[event.currentTarget.selectedIndex].text
        addExperiment(instance, event.currentTarget.value, name)
    },
    "click a.remove.button": function removeExperiment(event, instance){
        const index = event.currentTarget.dataset.index
        var selectedExperiments = instance.selectedExperiments.get()
        selectedExperiments.splice(index, 1)
        instance.selectedExperiments.set(selectedExperiments)
        updateChart(instance)
    }
})



function fieldSorter(fields) {
    return (a, b) => fields.map(o => {
        return a[o] > b[o] ? 1 : a[o] < b[o] ? -1 : 0;
    }).reduce((p,n) => p ? p : n, 0);
}


function addExperiment(instance, experiment, name){
    const day = instance.day.get(),
          q  = instance.query.get()
    if(day && experiment && q){
        var es = instance.selectedExperiments.get()
        console.log(es)
        if (!es.some((ex) => ex.day == day && ex.experiment == experiment)){
            es.push({day, experiment, name})
            es.sort(fieldSorter(["day", "name", "experiment"]))
            instance.selectedExperiments.set(es)
            updateChart(instance)
        }
        $("select[name=bag]").dropdown('clear')
    }
}



function flowNearestZero(fcs){
    return fcs.reduce((min, fc) => {
        return Math.abs(fc.flow) < Math.abs(min) ? fc.flow : min
    }, Infinity)
}


function updateChart(instance){
    const q = instance.query.get(),
       exps = instance.selectedExperiments.get().map((e) => e.experiment)
    console.info(exps, exps == true)
    if(exps.length && q){
        
        Meteor.call("getPlots", exps, q, (err, res) => {
            if(err){ alert(err); return }
            var query = Queries[q]
            
            
            Plotly.newPlot($('#compare_plot')[0], res.data, res.layout).then((plt) => {
                
                $('#compare_plot a[data-title="Autoscale"]')[0].click() // hack
                plt.on("plotly_click", (data) => {
                    
                    
                    
                    $("#crop_loader").addClass("active")
                    
                    
                    const flow = flowNearestZero(data.points.map(query.isolate, plt.data))
                    var points = data.points.map(query.isolate, plt.data)
                    
                    
                    
                    var experiment = exps[points[0].category]
                    
                    
                    console.info(plt, points, flow, experiment, exps)
                    
                    
                    Meteor.call("experiment_particles_with_flow_near", experiment, flow, (err, res) => {
                        $("#crop_loader").removeClass("active")
                        if(err){
                            console.info(err)
                        } else {
                            console.info(res)
                            cat_groups = res.rows.reduce((grps, p) => {
                                p.url = `/mot/data/experiments/${p.path}`
                                if (!grps[p.category]){
                                    grps[p.category] = [p]
                                } else {
                                    grps[p.category].push(p)
                                }
                                return grps
                            }, {})
                            console.info(cat_groups)
                            merged = []
                            //try{
                            for (let cat in cat_groups){
                                merged.push({category: cat, particles: cat_groups[cat]})
                            }
                            //} catch(e){
                            //    console.info(e)
                            //}
                            
                            console.info(merged)
                            instance.crops.set(merged)
                        }
                            
                    })
                    
                    
                    
                    /*
                    $("#crop_loader").addClass("active")
                    
                    if (q == "compare_flow_vs_category_violin2"){
                        var points = data.points.map(query.isolate, plt.data)
                        // we want only a single experiments crops
                        var ex = exps[points[0].trace]
                        
                        // hack for bitumen/sand comparision
                        points[0].trace = 2
                        points[1] = {flow: points[0].flow, trace: 3}
                    }
                    
                    Meteor.call("getCrops", ex.day, ex.bag, q, points, (err, res) => {
                        $("#crop_loader").removeClass("active")
                        instance.crops.set(res)
                    })
                    */
                    
                })
                
            })
        })
        
    }
}

