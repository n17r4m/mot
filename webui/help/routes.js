FlowRouter.route('/help', {
    action: function(params) {
        BlazeLayout.render("help", {main: "help_index"});
    }
});

FlowRouter.route('/help/detection', {
    action: function(params) {
        BlazeLayout.render("help", {main: "help_detection"});
    }
});

FlowRouter.route('/help/infrastructure', {
    action: function(params) {
        BlazeLayout.render("help", {main: "help_infrastructure"});
    }
});

FlowRouter.route('/help/tracking', {
    action: function(params) {
        BlazeLayout.render("help", {main: "help_tracking"});
    }
});
