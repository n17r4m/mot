import { Meteor } from 'meteor/meteor';
import mpg from 'meteor-pg';



Meteor.publish('experiments', () => {
  
    return mpg.select(
        'experiments', 
        "SELECT experiment AS _id, name, to_char(day, 'YYYY-MM-DD') as day, method, notes, MIN(number) AS startframe FROM Experiment LEFT JOIN Frame USING(experiment) GROUP BY experiment", 
        undefined, () => { return true }
    );
});


Meteor.publish('tracks', (experiment) => {
    console.info("loading tracks for", experiment)
    tracks = mpg.select(
        'tracks', 
        "SELECT frame AS _id, number, array_agg(location) AS locations FROM Track LEFT JOIN Frame USING(frame) WHERE Experiment = $1 GROUP BY _id, number ORDER BY number",
        experiment, () => { return false }
    )
    console.info("Got tracks for", experiment)
    return tracks
})