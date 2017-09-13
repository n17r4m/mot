import { Template } from 'meteor/templating';
import { ReactiveVar } from 'meteor/reactive-var';
import { Queries } from '../queries'

import './compare.html';



Template.compare.onCreated(function makeVars(){
    this.queries = new ReactiveVar([])
    this.bagList = new ReactiveVar([])
    this.bagName = new ReactiveVar()
    this.dayList = new ReactiveVar([])
    this.dayName = new ReactiveVar()
    this.experiments = new ReactiveVar([])
    this.query = new ReactiveVar()
    this.crops = new ReactiveVar([])
    
})


Template.compare.onRendered(function updateDayList(){
    this.$("select.dropdown").dropdown()
    this.queries.set(Queries.filter((q) => q.type == "compare"))
    Meteor.call("dayList", (err, list) => {
        return err ? this.dayList.set("Error") : this.dayList.set(list)
    })
    
})

Template.compare.helpers({
    queries()    { return Template.instance().queries.get()     },
    dayList()    { return Template.instance().dayList.get()     },
    bagList()    { return Template.instance().bagList.get()     },
    experiment() { return Template.instance().experiments.get() },
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
        instance.dayName.set(event.currentTarget.value)
        Meteor.call("bagList", instance.dayName.get(), (err, list) => {
            return err ? instance.bagList.set(["Error"]) : instance.bagList.set(list)
        })
    },
    "change select[name=bag]": function bagSelect(event, instance){
        instance.bagName.set(event.currentTarget.value)
        addExperiment(instance)
    },
    "click a.remove.button": function removeExperiment(event, instance){
        const a = event.currentTarget
        const index = a.dataset.index
        var experiments = instance.experiments.get()
        experiments.splice(index, 1)
        instance.experiments.set(experiments)
        updateChart(instance)
    }
})



function fieldSorter(fields) {
    return (a, b) => fields.map(o => {
        return a[o] > b[o] ? 1 : a[o] < b[o] ? -1 : 0;
    }).reduce((p,n) => p ? p : n, 0);
}

function addExperiment(instance){
    const day = instance.dayName.get(),
          bag = instance.bagName.get(),
          q  = instance.query.get()
    if(day && bag && q){
        var es = instance.experiments.get()
        if (!es.some((ex) => ex.day == day && ex.bag == bag)){
            es.push({day: day, bag: bag})
            es.sort(fieldSorter(["day", "bag"]))
            instance.experiments.set(es)
            updateChart(instance)
        }
        $("select[name=bag]").dropdown('clear')
    }
}

function updateChart(instance){
    const q = instance.query.get(),
       exps = instance.experiments.get().map((e) => ({day: e.day, bag: e.bag}))
    console.info(exps, exps == true)
    if(exps.length && q){
        Meteor.call("getPlots", exps, q, (err, res) => {
            if(err){ alert(err); return }
            var query = Queries[q]
            
            
            Plotly.newPlot($('#compare_plot')[0], res.data, res.layout).then((plt) => {
                
                $('#compare_plot a[data-title="Autoscale"]')[0].click() // hack
                plt.on("plotly_click", (data) => {
                    
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
                })
                
            })
        })
    }
}

