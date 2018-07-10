export const Queries = {
    queries: {
        flow_vs_intensity_histogram: { 
            type: "analyse", 
            label: "Flow vs. Intensity (hist)",
            args: [
                {
                    "class": "threshold",
                    label: "Intensity threshold",
                    type: "number",
                    value: 0.5,
                    min: 0,
                    max: 1
                }
            ]
        },
        flow_vs_intensity_distribution: { 
            type: "_analyse", 
            label: "Flow vs. Intensity (dist)",
            args: [
                {
                    "class": "threshold",
                    label: "Intensity threshold",
                    type: "number",
                    value: 0.5,
                    min: 0,
                    max: 1
                }
            ]
        },
        flow_vs_intensity_violin: { 
            type: "_analyse", 
            label: "Flow vs. Intensity (violin)",
            args: [
                {
                    "class": "threshold",
                    label: "Intensity threshold",
                    type: "number",
                    value: 0.5,
                    min: 0,
                    max: 1
                }
            ]
        },
        flow_vs_category_histogram: { 
            type: "analyse", 
            label: "Flow vs. Category (hist)"
        },
        flow_vs_category_distribution: { 
            type: "_analyse", 
            label: "Flow vs. Category (dist)"
        },
        flow_vs_category_violin: { 
            type: "_analyse", 
            label: "Flow vs. Category (violin)" 
        },
        
        particle_size_distribution: {
            type: "analyse",
            label: "Particle Size Distribution"
        },
        particle_counts_over_time: {
            type: "analyse",
            label: "Particle Counts Over Time"
        },
        compare_particle_size_distribution: {
            type: "compare",
            label: "Compare PSD"
        },
        compare_particle_counts_over_time: {
            type: "compare",
            label: "Compare Particle Counts Over Time"
        },
        compare_flow_vs_category_violin2: {
            type: "_compare",
            label: "Compare Flow"
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
        value: p.x,
        category: p.curveNumber
    }},
    distribution: function(p){ return {
        value: p.x,
        category: p.curveNumber % (this.length / 2)
    }},
    violin: function(p){ return {
        value: p.y,
        category: Math.floor(p.curveNumber/(this.length / 5)) 
    }},
    violin2: function(p){ return {
        value: p.y,
        category: Math.floor(p.curveNumber/10) 
    }},
    time: function(p){ return {
        value: p.x,
        category: p.curveNumber
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