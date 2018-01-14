import { Meteor } from 'meteor/meteor'
import { Pool } from 'pg'


const pg = new Pool()


Meteor.methods({
    
    experiment(experiment){
        return pg.query(
            "SELECT experiment, name, to_char(day, 'YYYY-MM-DD') as day, method, notes \
             FROM Experiment WHERE experiment = $1", [experiment])
    },
    
    experiments(){
        return pg.query(
            "SELECT experiment, name, to_char(day, 'YYYY-MM-DD') as day, method, notes \
             FROM Experiment ORDER BY day DESC ")
    },
    
    experiment_days(){
        return pg.query(
            "SELECT DISTINCT to_char(day, 'YYYY-MM-DD') as _id \
             FROM Experiment WHERE method ILIKE 'tracking%' ORDER BY _id DESC ")
    },
    
    experiments_on_day(day){
        return pg.query(
            "SELECT experiment as _id, name \
            FROM Experiment WHERE method ILIKE 'tracking%' AND day = $1 ORDER BY _id ASC", [day])
    }
    
})



