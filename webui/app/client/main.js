
Template.registerHelper('equals',
    function(v1, v2) {
        return (v1 === v2);
    }
);

Template.registerHelper('startsWith',
    function(x, searchString) {
        return x.substr(0, searchString.length).toLowerCase() === searchString.toLowerCase()
    }
);