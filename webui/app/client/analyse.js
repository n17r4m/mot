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
    
    Meteor.call('experiment_days', (err, res) => { this.days.set(res.rows) })
    
    
    
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
            instance.experiments.set(res.rows)
        })
    },
    "change select[name=experiment]": function bagSelect(event, instance){
        instance.experiment.set(event.currentTarget.value)
        updateChart(instance)
    }
})



function updateChart(instance){
    const experiment = instance.experiment.get(),
          q  = instance.query.get()
    if(experiment && q){
        Meteor.call("getPlot", experiment, q, (err, res) => {
            if(err){ alert(err); return }
            var query = Queries[q]
            
            Plotly.newPlot($('#analysis_plot')[0], res.data, res.layout).then((plt) => {
                
                $('#analysis_plot a[data-title="Autoscale"]')[0].click() // hack
                plt.on("plotly_click", (data) => {
                    
                    $("#crop_loader").addClass("active")
                    console.info(plt, data.points)
                    console.info(data.points.map(query.isolate, plt.data))
                    Meteor.call("getCrops", experiment, q, data.points.map(query.isolate, plt.data), (err, res) => {
                        $("#crop_loader").removeClass("active")
                        console.info(err, res)
                        instance.crops.set(res)
                    })
                })
                
            })
        })
    }
}

