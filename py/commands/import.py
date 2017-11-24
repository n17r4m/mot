'''

'''
from skimage import io

import config

from lib.Crop import Crop
from lib.Video import Video
from lib.Database import Database
from lib.legacy.DataBag import DataBag
from lib.models.Classifier import Classifier

from dateutil.parser import parse as dateparse

from uuid import uuid4, UUID

import numpy as np
import traceback
import multiprocessing
import shutil

import os
import time

async def main(args):
    
    if len(args) == 0: print("What you want to import? [legacy|]")
        
    else:
        if   args[0] == "legacy":    await import_databag(args[1:])
        else:                         print("Invalid import sub-command")


async def import_databag(args):
    
    if len(args) < 5:
        print("Please supply \"databag_file date name method notes [video_file]\"")
        return
    
    file = args[0]
    date = args[1]
    name = args[2]
    method = args[3]
    notes = args[4]
    
    if len(args) == 6:
        PROCESS_VIDEO = True
        video_fpath = args[5]
        video = Video(video_fpath)
    else:
        PROCESS_VIDEO = False    
        
    # init our classifier
    classifier = Classifier()
    classifier.load()
    
    # open new connection
    _db = Database()
    db, transaction = await _db.transaction()
    
    # add new experiment
    experiment_uuid = uuid4()
    experiment_day = dateparse(date)
    experiment_dir = os.path.join(config.experiment_dir, str(experiment_uuid))
    
    experiment = (experiment_uuid, experiment_day, name, method, notes)
    
    try:
        print("Creating data directory", experiment_dir)
        os.mkdir(experiment_dir)    
        
        print("Inserting experiment", name, "(", experiment_uuid, ") into database.")
        await db.execute("""
            INSERT INTO Experiment (experiment, day, name, method, notes) 
            VALUES ($1, $2, $3, $4, $5)
            """, *experiment)
            
        print("Opening connection to", file)
        # open legacy connection
        legacy_db = DataBag(file)
        c = legacy_db.cursor()
        
        print("Launching CropWriter process")
        crop_writer_queue = multiprocessing.Queue()
        crop_writer = CropWriter(crop_writer_queue, experiment_dir)
        crop_writer.start()
    
        compressors = [crop_writer]
        frame_buffers = [crop_writer_queue]
        
        # find and insert legacy particles
        particle_map = dict()
        
        legacy_particles = c.execute("""
            SELECT id, area, intensity, perimeter, radius, category
            FROM particles p
        """).fetchall()         
        
        print("Found", len(legacy_particles), "particles.")
        batchsize = 300
        for b in batch(legacy_particles, batchsize):
            print(".", end='', flush=True)
            
            particles = [(uuid4(), experiment_uuid, p[1], p[2], p[3], p[4], p[5])
                for i, p in enumerate(b)]
                
            [particle_map.update({p[0]: particles[i][0]}) for i, p in enumerate(b)]
                
            await db.executemany("""
                INSERT INTO Particle (particle, experiment, area, intensity, perimeter, radius, category)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, particles) 
        print(".")
        # find and insert legacy frames, and corresponding assoc
        legacy_frames = c.execute("""
            SELECT DISTINCT frame 
            FROM frames 
            ORDER BY frame ASC
        """).fetchall()
        
        for legacy_frame in legacy_frames:
            
            if PROCESS_VIDEO:
                frame = video.normal_frame(legacy_frame[0])
                cropper = Crop(frame)
            
            frame = (uuid4(), experiment_uuid, legacy_frame[0])
            
            await db.execute("""
                INSERT INTO Frame (frame, experiment, number)
                VALUES ($1, $2, $3)
            """, *frame)
            
            crop_dir = os.path.join(experiment_dir, str(frame[0]))
            os.mkdir(crop_dir)
            
            print("Procesing frame", str(legacy_frame[0]))
            legacy_assoc = c.execute("""
                SELECT frame, particle, x, y, crop, scale
                FROM assoc a, particles p
                WHERE a.frame == $1 AND a.particle == p.id
            """, (str(legacy_frame[0]),)).fetchall()
                    
            print("Found", len(legacy_assoc), "assoc.")
            for b in batch(legacy_assoc, batchsize):
                
                print(".", end='', flush=True)
                
                # Coords like (col, row)
                coords = [(p[3], p[2]) for p in b]
                there_are_crops = True
                
                # Try to use existing crops
                try:
                    crops = np.array([np.frombuffer(p[4], dtype="uint8").reshape(64, 64) for p in b])
                    there_are_crops = True
                except AttributeError:
                    there_are_crops = False
                
                if PROCESS_VIDEO and not there_are_crops:
                    crops = np.array([cropper.crop(int(round(c[0])), int(round(c[1]))) for c in coords])
                    there_are_crops = True
                
                if there_are_crops:
                    pcrops = np.array([classifier.preproc(crop) for crop in crops])
                
                    # need to pad the array of crop images into a number divisible by the # of GPUs
                    pcrops = np.lib.pad(pcrops, ((0, len(pcrops) % config.GPUs), (0,0), (0,0), (0,0)), 'constant', constant_values=0)
                
                
                    print(".", end='', flush=True)
                
                    latents = classifier.encoder.predict(pcrops.reshape((len(pcrops), *(pcrops[0].shape))))
            
                print(".", end='', flush=True)
                
                # Need to think about this some more...
                #  depends on method (tracking/detection),
                '''
                categories = [np.argmax(c) for c in classifier.featureclassifier.predict(latents.reshape(len(latents), *(latents[0].shape)))]

                print(".", end='', flush=True)
                '''
                if there_are_crops:
                    tracks = [(uuid4(), frame[0], particle_map[p[1]], coords[i], ",".join(list(latents[i].astype("str"))))
                        for i, p in enumerate(b)]
                    
                    await db.executemany("""
                        INSERT INTO Track (track, frame, particle, location, latent)
                        VALUES ($1, $2, $3, $4, $5)
                    """, tracks)
                    
                    print(":", end='', flush=True)
                    
                    # todo: pass full batch.
                    [crop_writer_queue.put((str(frame[0]), str(tracks[i][0]), crop))
                        for i, crop in enumerate(crops)]
                    
                else:
                    tracks = [(uuid4(), frame[0], particle_map[p[1]], coords[i])
                        for i, p in enumerate(b)]
                    
                    await db.executemany("""
                        INSERT INTO Track (track, frame, particle, location)
                        VALUES ($1, $2, $3, $4)
                    """, tracks)
                    
                print(":")
            
            while max([b.qsize() for b in frame_buffers]) > 5:
                print("queue:", crop_writer_queue.qsize())
                time.sleep(0.1)
                
    except Exception as e:
        print("Uh oh. Something went wrong")
        traceback.print_exc()
        print("Waiting for compression to complete")
        [b.put(None) for b in frame_buffers]
        [c.stop() for c in compressors]
        [c.join() for c in compressors]
        
        print("Rolling back database.")
        await transaction.rollback()
        
        if os.path.exists(experiment_dir):
            print("Removing files from", experiment_dir)
            shutil.rmtree(experiment_dir)
            
    else:
        print("Comitting changes to database.")
        await transaction.commit()
        print("Waiting for compression to complete.")
        [b.put(None) for b in frame_buffers]
        [c.join() for c in compressors]
        
    finally:
        print("Fin.")
        
    return experiment[0]
    
def batch(iterable, n=1):
    #https://stackoverflow.com/a/8290508
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


class CropWriter(multiprocessing.Process):
    def __init__(self, queue, experiment_dir):
        super(CropWriter, self).__init__()
        self.queue = queue
        self.edir = experiment_dir
        self.stop_event = multiprocessing.Event()
    
    def run(self):
        
        while True:
            if self.stopped():
                return
            else:
                crop_data = self.queue.get()
                if crop_data is None:
                    return
                else:
                    frame, track, crop = crop_data
                    io.imsave(os.path.join(self.edir, frame, track + ".jpg"), crop.squeeze(), quality=90) 
                
    
    def close(self, proc):
        proc.stdin.close()
        proc.wait()
    
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()