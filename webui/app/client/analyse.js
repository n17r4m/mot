import { Template } from 'meteor/templating';
import { ReactiveVar } from 'meteor/reactive-var';
import { Queries } from '../queries'

import './analyse.html';



Template.analyse.onCreated(function makeVars(){
    this.bagList = new ReactiveVar([])
    this.bagName = new ReactiveVar()
    this.query = new ReactiveVar()
})

Template.analyse.onRendered(function updateBagList(){
    this.$("select.dropdown").dropdown()
    Meteor.call("bagList", (err, list) => {
        return err ? this.bagList.set("Error") : this.bagList.set(list)
    })
    
})

Template.analyse.helpers({
    bagList() { return Template.instance().bagList.get() },
    queries() { return Queries.filter((q) => q.type == "analyse") }
});

Template.analyse.events({
    "change select[name=query]": function bagSelect(event, instance){
        instance.query.set(event.currentTarget.value)
        updateChart(instance)
    },
    "change select[name=bag]": function bagSelect(event, instance){
        instance.bagName.set(event.currentTarget.value)
        updateChart(instance)
    }
})

function updateChart(instance){
    const bn = instance.bagName.get(),
          q  = instance.query.get()
          
    
    if (bn && q){
        
        var settings = { margin: { t: 0 } };
        
        Meteor.call("runQuery", bn, q, [110], (err, res) => {
            if (err) { alert(err) }
            
            switch(q){
                case "flow_vs_intensity_histogram":
                    light = res[0]
                    dark = res[1]
                    
                    
                    settings.barmode = "overlay"
                    
                    Plotly.newPlot($('#analysis_chart')[0], [
                        {x: light, name: "Light", type: 'histogram', opacity: 0.5, marker: {color: "orange"}},
                        {x: dark,  name: "Dark",  type: 'histogram', opacity: 0.6, marker: {color: "blue"}}
                    ], settings)
                    break;
            }
            
        })
    }
}

Template.analyse.onRendered(function genChart(){
  
  
})
