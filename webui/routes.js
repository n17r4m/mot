import { FlowRouter } from 'meteor/ostrio:flow-router-extra';

FlowRouter.route('/', {
    action: function(params) {
        BlazeLayout.render("index");
    }
});

FlowRouter.route('*', {
    action: function() {
        BlazeLayout.render("notFound");
    }
});