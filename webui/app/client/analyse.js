import { Template } from 'meteor/templating';
import { ReactiveVar } from 'meteor/reactive-var';
import { Meteor } from 'meteor/meteor'
import { Queries } from '../queries'

import './analyse.html';



Template.analyse.onCreated(function makeVars(){
    
    this.queries = new ReactiveVar([])
    this.days = new ReactiveVar([])
    this.experiments = new ReactiveVar([])
    this.experiment = new ReactiveVar()
    this.query = new ReactiveVar()
    this.crops = new ReactiveVar([])
    
    Meteor.call('experiment_days', (err, res) => { 
        if (err){ alert(err) }
        else { this.days.set(res.rows) }
    })
    
    
    
})

Template.analyse.onRendered(function updateDayList(){
    this.$("select.dropdown").dropdown()
    this.queries.set(Queries.filter((q) => q.type == "analyse"))
})

Template.analyse.helpers({
    queries()  { return Template.instance().queries.get()     },
    dayList()  { return Template.instance().days.get()        },
    nameList() { return Template.instance().experiments.get() },
    crops()    { return Template.instance().crops.get()       },
    arg()      {
        let q = Queries.get(Template.instance().query.get())
        if (q) return q.args || []; else return []
    }
});

Template.analyse.events({
    "change select[name=query]": function bagSelect(event, instance){
        instance.query.set(event.currentTarget.value)
        updateChart(instance)
    },
    "change select[name=day]": function daySelect(event, instance){
        Meteor.call("experiments_on_day", event.currentTarget.value, (err, res) => {
            if (err) { alert(err) } 
            else { instance.experiments.set(res.rows) }
        })
    },
    "change select[name=experiment]": function experimentSelect(event, instance){
        instance.experiment.set(event.currentTarget.value)
        updateChart(instance)
    },
    "change input": function argChange(event, instance){
        updateChart(instance)
    }
})



function valueNearestZero(fcs){
    return fcs.reduce((min, fc) => {
        return Math.abs(fc.value) < Math.abs(min) ? fc.value : min
    }, Infinity)
}


function updateChart(instance){
    const experiment = instance.experiment.get(),
          q  = instance.query.get()
    if(experiment && q){
        
        var query = Queries[q]
        var args = (query.args || []).map((props) => {
            return $("input." + props["class"]).val()
        })
        console.info(args)
        
        Meteor.call("getPlot", experiment, q, args, (err, res) => {
            if(err){ alert(err); return }
            
            
            Plotly.newPlot($('#analysis_plot')[0], res.data, res.layout).then((plt) => {
                
                $('#analysis_plot a[data-title="Autoscale"]')[0].click() // hack
                plt.on("plotly_click", (data) => {
                    
                    $("#crop_loader").addClass("active")
                    
                    console.info(plt, data.points)
                    console.info(data.points.map(query.isolate, plt.data))
                    console.log(q)
                    
                    switch(q) {
                        case "flow_vs_intensity_histogram":
                            var method_name = "experiment_particles_with_flow_near"
                            var value = valueNearestZero(data.points.map(query.isolate, plt.data))
                            break;
                        case "flow_vs_category_histogram":
                            var method_name = "experiment_particles_with_flow_near"
                            var value = valueNearestZero(data.points.map(query.isolate, plt.data))
                            break;
                        case "particle_size_distribution":
                            var method_name = "experiment_particles_with_area_near"
                            var value = valueNearestZero(data.points.map(query.isolate, plt.data))
                            break;
                        case "particle_counts_over_time":
                            var method_name = "experiment_particles_with_frame_near"
                            var value = valueNearestZero(data.points.map(query.isolate, plt.data))
                        default:
                            break
                    } 
                    
                    Meteor.call(method_name, experiment, value, (err, res) => {
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
                            
                            
                            merged_scatters = []
                            cat_scatters = res.rows.reduce((grps, p) => {
                                if (!grps[p.category]){
                                    // Note: need a way to specify trace label
                                    grps[p.category] = 
                                    {
                                        x: [], 
                                        y: [],
                                        mode: 'markers',
                                        type: 'scatter',
                                        marker: {
                                            color: 'rgba(31,119,180, 0.5)', // Give transparent markers
                                            size: 10,
                                            line: {
                                                color: 'rgb(68,68,68)',
                                                width: 1
                                            }}
                                        }
                                    }
                                                        
                                grps[p.category].x.push(p.x)
                                grps[p.category].y.push(p.y)
                            
                                return grps
                            }, {})
                            for (let cat in cat_scatters){
                                merged_scatters.push(cat_scatters[cat])
                            }
                            
                            // cat_scatters.push({x: [], y: [], mode: 'markers', type: 'scatter'});
                            // cat_scatters[p.category].x.push(p.x)
                            // cat_scatters[p.category].y.push(p.y)
                            
                            //try{
                            merged = []
                            for (let cat in cat_groups){
                                merged.push({category: cat, particles: cat_groups[cat]})
                            }
                            
                            //} catch(e){
                            //    console.info(e)
                            //}
                            var layout = 
                                {   
                                    yaxis: { autorange: "reversed" },
                                    title: "Particle Position"
                                };
                            
                            Plotly.newPlot($('#scatter_plot')[0], merged_scatters, layout);
                            
                            console.info(merged)
                            instance.crops.set(merged)
                        }
                            
                    })
                    
                    
                })
                
            })
        })
    }
}

