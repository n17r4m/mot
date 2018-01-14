import { FlowRouter } from 'meteor/ostrio:flow-router-extra';

FlowRouter.route('/app', {
    action(params) {
        BlazeLayout.render("app", {main: "app_index"});
    }
});

FlowRouter.route('/app/analyse', {
    action(params) {
        BlazeLayout.render("app", {main: "analyse"});
    }
});

FlowRouter.route('/app/compare', {
    action(params) {
        BlazeLayout.render("app", {main: "compare"});
    }
});

FlowRouter.route('/app/simulate', {
    action(params) {
        BlazeLayout.render("app", {main: "simulate"});
    }
});

FlowRouter.route('/app/upload', {
    action(params) {
        BlazeLayout.render("app", {main: "upload"});
    }
});

FlowRouter.route('/app/experiment/:experiment', {
    action(params) {
        Session.set("experiment", params.experiment)
        BlazeLayout.render("app", {main: "experiment"});
    }
});