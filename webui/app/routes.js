
FlowRouter.route('/app', {
    action: function(params) {
        BlazeLayout.render("app", {main: "app_index"});
    }
});

FlowRouter.route('/app/analyse', {
    action: function(params) {
        BlazeLayout.render("app", {main: "analyse"});
    }
});

FlowRouter.route('/app/compare', {
    action: function(params) {
        BlazeLayout.render("app", {main: "compare"});
    }
});

FlowRouter.route('/app/simulate', {
    action: function(params) {
        BlazeLayout.render("app", {main: "simulate"});
    }
});

FlowRouter.route('/app/upload', {
    action: function(params) {
        BlazeLayout.render("app", {main: "upload"});
    }
});
