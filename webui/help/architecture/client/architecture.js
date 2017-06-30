import { Template } from 'meteor/templating';


import './architecture.html';

Template.architecture_modules.onCreated(function source(arg1) {
  var self = this
  self.source_list = new ReactiveVar([])
  Meteor.call("source_list", function(err, list){
    console.info(err, list)
    if (err){
        self.source_list.set(["Error"])
    } else {
        self.source_list.set(list)
    }
  })
});


const about_source = {
  "BackgroundExtractor.py": "Curate a static background from a video file",
  "Bag2PymotJson.py": "Convert a DataBag into a format ready for use by PyMot",
  "Bag2Video.py": "Convert a DataBag into simulated video",
  "BinaryExtractor.py": "Seperate foreground from background",
  "BurstGrabber.py": "Returns a single burst from a video of many",
  "ComponentExtractor.py": "Given an array of binary images, returns a dictionary of component information",
  "DataBag.m": "Database system for storing detection and tracking results (matlab)",
  "DataBag.py": "Database system for storing detection and tracking results",
  "DetectorValidator.py": "A utility to assign an error rate to a detector, while simultaneously building a ground truth set.",
  "Documentor.py": "Powers this page's ability to generate pydoc html files",
  "ForegroundExtractor.py": "Given a background image and an array of images (np.arrays), returns an array of images containing foregrounds.",
  "FrameGrabber.py": "Return a particular frame from a video file",
  "Query.py": "Useful tools when negotiating with a DataBag",
  "Simulation.py": "Create a DataBag via simulation",
  "Tracker.py": "Compress a DataBag of detections into a DataBag of tracks",
  "TrackerValidator.py": "A utility to assign an error rate to a detector, while simultaneously building a ground truth set.",
  
  
  
}

Template.architecture_modules.helpers({
  list() { return Template.instance().source_list.get() },
  about(source) { return about_source[source] || "" }
});
