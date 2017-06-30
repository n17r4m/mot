FlowRouter.route('/', {
    action: function(params) {
        BlazeLayout.render("index");
    }
});

FlowRouter.notFound = {
    action: function() {
        BlazeLayout.render("notFound");
    }
};