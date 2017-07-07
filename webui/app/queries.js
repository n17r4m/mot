export const Queries = {
    queries: {
        flow_vs_intensity_histogram: { type: "analyse", label: "Flow vs. Intensity" }
        /// ... 
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

for (query in Queries.queries){
    Queries.queries[query].query = query
}