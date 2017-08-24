export const Queries = {
    queries: {
        flow_vs_intensity_histogram: { 
            type: "analyse", 
            label: "Flow vs. Intensity (hist)",
            args: [
                {
                    "class": "threshold",
                    label: "Intensity threshold",
                    type: "range",
                    value: 110,
                    min: 0,
                    max: 255
                }
            ]
        },
        flow_vs_intensity_distribution: { 
            type: "analyse", 
            label: "Flow vs. Intensity (dist)",
            args: [
                {
                    "class": "threshold",
                    label: "Intensity threshold",
                    type: "range",
                    value: 110,
                    min: 0,
                    max: 255
                }
            ]
        },
        flow_vs_intensity_violin: { 
            type: "analyse", 
            label: "Flow vs. Intensity (violin)" 
        },
        flow_vs_category_histogram: { 
            type: "analyse", 
            label: "Flow vs. Category (hist)"
        },
        flow_vs_category_distribution: { 
            type: "analyse", 
            label: "Flow vs. Category (dist)"
        },
        flow_vs_category_violin: { 
            type: "analyse", 
            label: "Flow vs. Category (violin)" 
        },
        compare_flow_violin_test: {
            type: "compare",
            label: "Test split violin"
        }
        /// ... 
    },
    get: function getQuery(q){
        return this.queries[q] || null
    },
    includes: function includesQuery(query){
        return query in this.queries  
    },
    list: function listQueries(){
        qs = []
        for (let query in this.queries){
            qs.push(this.queries[query])
        }
        return qs
    },
    filter: function filterQueries(filterFn){
        qs = []
        for (let query in this.queries){
            if (filterFn(this.queries[query])){
                qs.push(this.queries[query])
            }
        }
        return qs
    },
    some: function someQuery(someFn){
        for (let query in this.queries){
            if (someFn(this.queries[query])){
                return true
            }
        }
        return false
    }
}

var isolateParticleMaps = {
    histogram: function(p){ return {
        flow: p.x,
        trace: p.curveNumber
    }},
    distribution: function(p){ return {
        flow: p.x,
        trace: p.curveNumber % (this.length / 2)
    }},
    violin: function(p){ return {
        flow: p.y,
        trace: Math.floor(p.curveNumber/(this.length / 5)) 
    }}
}


for (let query in Queries.queries){
    let kind = query.split("_").pop()
    var ref = Queries.queries[query]
    ref.query = query
    ref.kind = kind
    ref.isolate = isolateParticleMaps[kind]
    Queries[query] = ref
}