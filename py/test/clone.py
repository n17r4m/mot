'''
Clone a database experiment and its corresponding files.

Filter the results during the process:
 - the original db might be "raw"/"unfiltered",
   but later processing (tracking) is much more stable/
   efficient/accurate with preprocessed data.
'''

import config

import numpy as np
import os
from os.path import isdir, isfile, join
import traceback

from uuid import uuid4, UUID

from lib.Database import Database


async def main(args):
    await clone_experiment(args[0],args[1])

def particleFilter(p):
    if p["area"] < 100:
        return True
    if p["area"] > 2000:
        return True

async def clone_experiment(experiment_uuid, method, testing=False):
    
    try:
        db = Database()
        tx1, transaction = await db.transaction()
        
        txMessage = "Transaction 1"
        
        dbFrames = []
        osFrames = []
        frame_uuid_map = {}
        
        dbTracks = []
        osTracks = []
        trackInserts = []
        track_uuid_map = {}
        
        segment_uuid_map = {}
        segment_insert = []
        
        frame_segment_map = {}
        
        particleInserts = []
        particle_uuid_map = {}
        
        new_experiment_uuid = uuid4()
        experiment_path = join(config.experiment_dir, str(experiment_uuid))
        
        base_files = [file for file in os.listdir(experiment_path) if isfile(join(experiment_path, file))]
        
        s = """
            SELECT frame
            FROM frame
            WHERE experiment = '{experiment}'
            """
        q = s.format(experiment=experiment_uuid)
        
        async for row in tx1.cursor(q):
            dbFrames.append(str(row['frame']))
            
        osFrames = [frame for frame in os.listdir(experiment_path) if isdir(join(experiment_path, frame))]
        frame_uuid_map = {UUID(f): uuid4() for f in dbFrames}
        
        s = """
            SELECT t.frame as frame, t.particle as particle, track
            FROM track t, frame f
            WHERE t.frame = f.frame
            AND f.experiment = '{experiment}'
            """
        q = s.format(experiment=experiment_uuid)
        dbTracks = []
        async for row in tx1.cursor(q):
            dbTracks.append(str(row['track']))
        
        # osTracks: (oldFrame, (oldTrack, oldTrackExtension))
        osTracks = [(frame, os.path.splitext(track)) for frame in osFrames for track in os.listdir(join(experiment_path, frame)) if len(track) == 40]
        track_uuid_map = {UUID(track): uuid4() for track in dbTracks}
        
        new_experiment_path = join(config.experiment_dir, str(new_experiment_uuid))
        if not testing:
            os.mkdir(new_experiment_path)
        await tx1.execute("""
                INSERT INTO Experiment (experiment, day, name, method, notes) 
                SELECT $1, day, name, $3, notes FROM Experiment
                WHERE experiment = $2
                """, new_experiment_uuid, experiment_uuid, method)
        if not testing:
            for file in base_files:
                os.link(join(experiment_path, file), join(new_experiment_path, file))
            
        
            for old_frame_uuid, new_frame_uuid in frame_uuid_map.items():
                os.mkdir(join(new_experiment_path, str(new_frame_uuid)))
        
        # Clone db segments
        segment_uuid_map = {}
        segment_insert = []
        async for s in tx1.cursor("SELECT segment, number FROM Segment WHERE experiment = $1", experiment_uuid):
            segment_uuid = uuid4()
            segment_uuid_map[s["segment"]] = {"segment": segment_uuid, "number": s["number"]}
            segment_insert.append((segment_uuid, new_experiment_uuid, s["number"]))
        
        await tx1.executemany("INSERT INTO Segment (segment, experiment, number) VALUES ($1, $2, $3)", segment_insert)
        
        frame_segment_map = {}
        async for f in tx1.cursor("select frame, segment From Frame WHERE experiment = $1", experiment_uuid):
                frame_segment_map[f["frame"]] = segment_uuid_map[f["segment"]]["segment"]
        
        # Clone db frames
        await tx1.executemany("""
                INSERT INTO Frame (frame, experiment, segment, number) 
                SELECT $1, $2, $3, number FROM Frame
                WHERE frame = $4
                """, [(frame_uuid_map[UUID(frame)], new_experiment_uuid, frame_segment_map[UUID(frame)], UUID(frame)) for frame in dbFrames])
        
        # Clone db particles
        print("Inserting particles")
        s = """
            SELECT *
            FROM Particle
            WHERE experiment = '{exp}'
            """
        q = s.format(exp=experiment_uuid)
        particles_inserted = set()
        async for p in tx1.cursor(q):
            newParticleUUID = str(uuid4())
            
            # Filter by particle properties
            if particleFilter(p):
                continue
            particles_inserted.add(p["particle"])
            particle_uuid_map[p["particle"]] = newParticleUUID
            
            particleInserts.append((newParticleUUID, new_experiment_uuid, p["area"], p["intensity"], p["perimeter"], p["radius"], p["category"], p["valid"]))
        
        s = """
            INSERT INTO Particle (particle, experiment, area, intensity, perimeter, radius, category, valid)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """
        await tx1.executemany(s, particleInserts)
        # await transaction.commit()
        
        # Workaround until the table is changed to FK constraint deferrable
        # tx2, transaction = await db.transaction()
        txMessage = "Transaction 2"
        
        # Clone db tracks
        s = """
            SELECT *
            FROM Track t, Frame f
            WHERE t.frame = f.frame
            AND f.experiment = '{exp}'
            """
        q = s.format(exp=experiment_uuid)
        # tracks_inserted = set()
        old_tracks_inserted = set()
        async for t in tx1.cursor(q):
            # Check if it was filtered during particle insertion
            if t["particle"] not in particles_inserted:
                continue
            # tracks_inserted.add(track_uuid_map[t["track"]])
            old_tracks_inserted.add(str(t["track"]))
            trackInserts.append((track_uuid_map[t["track"]], frame_uuid_map[t["frame"]], particle_uuid_map[t["particle"]], t["location"], t["bbox"], t["latent"]))
        
        print("Inserting tracks")
        s = """
            INSERT INTO Track (track, frame, particle, location, bbox, latent)
            VALUES ($1, $2, $3, $4, $5, $6)
            """
        await tx1.executemany(s, trackInserts)
        
        count = 0
        if not testing:
            for track in osTracks:
                # Make sure the track wasn't filtered...
                if track[1][0] not in old_tracks_inserted:
                    continue
                count += 1
                from shutil import copyfile

                copyfile(join(experiment_path, track[0], "".join(track[1])), 
                    join(new_experiment_path, 
                        str(frame_uuid_map[UUID(track[0])]), 
                        str(track_uuid_map[UUID(track[1][0])]) + track[1][1]))
        print("Copied "+str(count)+" crop files")
        await transaction.commit()
        
        print("Success! "+ str(new_experiment_uuid))
    
    except Exception as e:
        print(e)
        print("Error during " + txMessage)
        print("Check db for experiment "+ str(new_experiment_uuid))
        
        traceback.print_exc()
        
        await transaction.rollback()