import { Template } from 'meteor/templating';
import { ReactiveVar } from 'meteor/reactive-var';
import { Queries } from '../queries'

import './analyse.html';



Template.analyse.onCreated(function makeVars(){
    this.queries = new ReactiveVar([])
    this.bagList = new ReactiveVar([])
    this.bagName = new ReactiveVar()
    this.dayList = new ReactiveVar([])
    this.dayName = new ReactiveVar()
    this.query = new ReactiveVar()
    this.crops = new ReactiveVar([])
    //this.plot = new ReactiveVar("<p>Select a Query</p>")
})

Template.analyse.onRendered(function updateBagList(){
    this.$("select.dropdown").dropdown()
    
    
})

Template.analyse.onRendered(function updateDayList(){
    this.$("select.dropdown").dropdown()
    this.queries.set(Queries.filter((q) => q.type == "analyse"))
    Meteor.call("dayList", (err, list) => {
        return err ? this.dayList.set("Error") : this.dayList.set(list)
    })
    
})

Template.analyse.helpers({
    queries() { return Template.instance().queries.get() },
    dayList() { return Template.instance().dayList.get() },
    bagList() { return Template.instance().bagList.get() },
    crops()   { return Template.instance().crops.get()   },
    arg()     {
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
        instance.dayName.set(event.currentTarget.value)
        Meteor.call("bagList", instance.dayName.get(), (err, list) => {
            return err ? instance.bagList.set(["Error"]) : instance.bagList.set(list)
        })
    },
    "change select[name=bag]": function bagSelect(event, instance){
        instance.bagName.set(event.currentTarget.value)
        updateChart(instance)
    }
})



function updateChart(instance){
    const day = instance.dayName.get(),
          bn = instance.bagName.get(),
          q  = instance.query.get()
    if(day && bn && q){
        Meteor.call("getPlot", day, bn, q, (err, res) => {
            if(err){ alert(err); return }
            var query = Queries[q]
            
            
            Plotly.newPlot($('#analysis_plot')[0], res.data, res.layout).then((plt) => {
                
                $('#analysis_plot a[data-title="Autoscale"]')[0].click() // hack
                plt.on("plotly_click", (data) => {
                    
                    $("#crop_loader").addClass("active")
                    console.info(plt, data.points)
                    console.info(data.points.map(query.isolate, plt.data))
                    Meteor.call("getCrops", day, bn, q, data.points.map(query.isolate, plt.data), (err, res) => {
                        $("#crop_loader").removeClass("active")
                        console.info(err, res)
                        instance.crops.set(res)
                    })
                })
                
            })
        })
    }
}

