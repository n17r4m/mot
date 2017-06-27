FlowRouter.route('/source', {
    action: function(params) {
        BlazeLayout.render("source_index");
    }
});

FlowRouter.route('/source/:file', {
    action: function(params) {
        BlazeLayout.render("source", {data: params.file});
    }
});

FlowRouter.route('/pydoc/:file', {
    action: function(params) {
        BlazeLayout.render("pydoc", {data: params.file});
    }
});