import { Meteor } from 'meteor/meteor'
import { Pool } from 'pg'
import { readdir } from 'fs'

const pg = new Pool()



Meteor.methods({
    
    categories(){
        return pg.query("SELECT * FROM Category ORDER BY category")  
    },
    
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
            "SELECT DISTINCT to_char(day, 'YYYY-MM-DD') as day  \
             FROM Experiment \
             ORDER BY day DESC ")
    },
    
    experiments_on_day(day){
        return pg.query(
            "SELECT experiment as _id, name \
            FROM Experiment \
            WHERE day = $1 ORDER BY _id ASC", [day])
    },
    
    experiment_segments(experiment){
        return pg.query(
            "SELECT segment as _id, number \
            FROM Segment WHERE experiment = $1 ORDER BY number ASC", [experiment])
    },
    
    
    experiment_particles_by_segment_category(experiment, segment, category, val_filter){
        var val_filters = {
            all:        "",
            verified:   "AND valid = TRUE",
            invalid:    "AND valid = FALSE",
            unverified: "AND valid IS NULL",
            'default':  ""
        }
        return pg.query(`
            SELECT 
                particle, 
                valid,
                array_agg(track ORDER BY Frame.number) as tracks, 
                array_agg(frame ORDER BY Frame.number) as frames
            FROM Track
            LEFT JOIN Particle USING(particle)
            LEFT JOIN Frame USING(frame)
            LEFT JOIN Segment USING(segment)
            WHERE segment.experiment = $1
            AND segment = $2
            AND category = $3
            ${val_filters[val_filter] || val_filters['default']}
            GROUP BY particle, valid`,
            [experiment, segment, category])  
    },
    
    experiment_particles_with_flow_near(experiment, flow, limit){
        // old_q = """
        //         SELECT 
        //             t2.particle AS particle, 
        //             f2.experiment || '/' || MAX( t2.frame || '/' || t2.track || '.jpg' ) AS path,
        //             AVG(ABS((t1.location[1] - t2.location[1]) * p.area - $1)) as dflow,
        //             c.label as category,
        //             valid,
        //             min(t1.location[0]) as x,
        //             min(t1.location[1]) as y
        //         FROM Track t1, Track t2, Frame f1, Frame f2, Particle p, Category c
        //         WHERE p.particle = t1.particle AND p.particle = t2.particle
        //         AND t1.particle = t2.particle
        //         AND t1.frame = f1.frame AND t2.frame = f2.frame
        //         AND p.category = c.category
        //         AND f1.number = f2.number - 1
        //         AND f1.experiment = $2 AND f2.experiment = $2
        //         AND p.experiment = $2
        //         GROUP BY f2.experiment, t2.particle, c.label, p.valid
        //         ORDER BY dflow ASC 
        //         LIMIT $3
        //         """
        q = `SELECT p.particle, 
                    p.experiment || '/' || MAX( t.frame || '/' || t.track || '.jpg' ) AS path,
                    ABS(p.velocity[1] - $1) as dflow,
                    c.label as category,
                    valid,
                    min(t.location[0]) as x,
                    min(t.location[1]) as y
            FROM track t, particle p, category c
            WHERE p.particle = t.particle
            AND p.category = c.category
            AND p.experiment = $2
            GROUP BY p.experiment, p.particle, c.label, p.valid
            ORDER BY dflow ASC
            LIMIT $3
            `

        return pg.query(q, [flow, experiment, limit || 50])
    },
    experiment_particles_with_area_near(experiment, area, limit){
        
        return pg.query(`
            SELECT 
                p.particle AS particle, 
                p.experiment || '/' || MAX( t1.frame || '/' || t1.track || '.jpg' ) AS path,
                ABS(2*p.radius-$1) as dDiameter,
                c.label as category,
                valid,
                min(t1.location[0]) as x,
                min(t1.location[1]) as y
            FROM Track t1, Frame f1, Particle p, Category c
            WHERE p.particle = t1.particle
            AND p.experiment = f1.experiment
            AND t1.frame = f1.frame
            AND p.category = c.category
            AND p.experiment = $2
            GROUP BY p.experiment, p.particle, c.label, p.valid
            ORDER BY dDiameter ASC 
            LIMIT $3`,
            [area, experiment, limit || 50])
    },
    experiment_particles_with_frame_near(experiment, frame, limit){
        
        return pg.query(`
            SELECT 
                p.particle AS particle, 
                p.experiment || '/' || MAX( t1.frame || '/' || t1.track || '.jpg' ) AS path,
                c.label as category,
                valid,
                min(t1.location[0]) as x,
                min(t1.location[1]) as y
            FROM Track t1, Frame f1, Particle p, Category c
            WHERE p.particle = t1.particle
            AND p.experiment = f1.experiment
            AND t1.frame = f1.frame
            AND f1.number = $1
            AND p.category = c.category
            AND p.experiment = $2
            GROUP BY p.experiment, p.particle, c.label, p.valid
            LIMIT $3`,
            [frame, experiment, limit || 50])
    },
    update_particle_category(particle, category){
        
        return pg.query(`
            UPDATE Particle 
            SET category = $2
            WHERE particle = $1
        `, [particle, category])
        
    },
    
    update_particle_validity(particle, valid){
        return pg.query(`
            UPDATE Particle 
            SET valid = $2
            WHERE particle = $1
        `, [particle, valid])
    }
    

    
})



