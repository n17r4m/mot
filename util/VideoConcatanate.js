/*
var fluent_ffmpeg = require("fluent-ffmpeg");

var mergedVideo = fluent_ffmpeg();
var videoNames = ['./video1.mp4', './video2.mp4'];

videoNames.forEach(function(videoName){
    mergedVideo = mergedVideo.addInput(videoName);
});

mergedVideo.mergeToFile('./mergedVideo.mp4', './tmp/')
.on('error', function(err) {
    console.log('Error ' + err.message);
})
.on('end', function() {
    console.log('Finished!');
});