'''
Partition a video into 'segments',
in the droplet tracking case bursts, in regular video scene changes etc.
'''

import config
from lib.Database import Database

import traceback
from uuid import uuid4, UUID
import numpy as np

async def main(args):
    
    if len(args) < 1: 
        
        print("What you want to segment?")
        print("USING: experiment-uuid")
    else:
        print(await segment_experiment(*args))

async def segment_experiment(experiment_uuid):

    db = Database()
    
    print("Getting frame costs")
    frame_costs = []
    frame_uuids = []
    last_frame = None
    async for row in db.query("""
        SELECT f1.number as n, f1.frame AS frame, f2.frame AS frame2, AVG(LOG(cost)) AS cost
        FROM frame f1, frame f2
        JOIN LATERAL (
            SELECT t1.track AS tr1, tr2, cost
            FROM track t1
            JOIN LATERAL (
                SELECT 
                    T2.track AS tr2, 
                    ((1 + (t1.latent <-> t2.latent))
                    *(1 + (t1.location <-> t2.location))) AS cost
                FROM track t2 
                WHERE t2.frame = f2.frame
                ORDER BY cost ASC
                LIMIT 1
            ) C ON TRUE
            WHERE t1.frame = f1.frame) E on true
        WHERE f1.experiment = $1
        AND f2.experiment = $1
        AND f1.number = f2.number-1
        GROUP BY f1.frame, f2.frame
        ORDER BY f1.number ASC """, experiment_uuid):
        frame_uuids.append(row["frame"])
        frame_costs.append(row["cost"])
        last_frame = row["frame2"]
        print(row["n"], end=' ')
    
    np.save('framecosts', frame_costs)
    print("Getting interquartile range and outlier threshold")
    q75, q25 = np.percentile(frame_costs, [75 ,25])
    iqr = q75 - q25
    upper_outlier = q75 + 1.5 * iqr
    
    running_median = np.array([np.median(frame_costs[:i]) for i in range(len(frame_costs))])
    running_std = np.array([np.std(frame_costs[:i]) for i in range(len(frame_costs))])
    upper_outlier = running_median + running_std
    
    print("Computing database changes")
    segment_inserts = []
    frame_updates = []
    segment_counter = 0
    segment_uuid = uuid4()
    
    segment_inserts.append((segment_uuid, experiment_uuid, segment_counter))
    
    print('burst detected on frames: ', end='', flush=True)
    for i, frame_uuid in enumerate(frame_uuids):
        
        frame_updates.append((segment_uuid, frame_uuid))
        
        if frame_costs[i] > upper_outlier[i]:
            print(i+1, end=' ', flush=True)
            segment_uuid = uuid4()
            segment_counter += 1
            segment_inserts.append((segment_uuid, experiment_uuid, segment_counter))
    
    print(".")
    
    frame_updates.append((segment_uuid, last_frame))
    
    print("Applying changes to database")
    try:
        tx, transaction = await db.transaction()
        await tx.executemany("""
            INSERT INTO Segment (segment, experiment, number)
            VALUES ($1, $2, $3)
            """, segment_inserts)
            
        await tx.executemany("""
            UPDATE Frame SET segment = $1 WHERE frame = $2
            """, frame_updates)    
        
    except Exception as e:
        print("Uh oh. Something went wrong")
        traceback.print_exc()
        await transaction.rollback()
    else:
        await transaction.commit()
    
    return "Fin."