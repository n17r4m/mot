FlowRouter.route('/discussion', {
    action: function(params) {
        BlazeLayout.render("discussion", {main: "discussion_index"});
    }
});

FlowRouter.route('/discussion/architecture', {
    action: function(params) {
        BlazeLayout.render("discussion", {main: "discussion_architecture"});
    }
});

FlowRouter.route('/discussion/detection', {
    action: function(params) {
        BlazeLayout.render("discussion", {main: "discussion_detection"});
    }
});

FlowRouter.route('/discussion/infrastructure', {
    action: function(params) {
        BlazeLayout.render("discussion", {main: "discussion_infrastructure"});
    }
});

FlowRouter.route('/discussion/tracking', {
    action: function(params) {
        BlazeLayout.render("discussion", {main: "discussion_tracking"});
    }
});

console.info("[Discussion] routes created")