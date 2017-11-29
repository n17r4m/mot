
from skimage import io
from skimage.transform import downscale_local_mean
from skimage.filters import threshold_sauvola as threshold
from skimage.segmentation import clear_border, random_walker
from skimage.measure import label, regionprops
from skimage.morphology import binary_opening, square, remove_small_objects
from skimage.color import gray2rgb
from skimage.draw import circle

import config

from lib.Crop import Crop
from lib.Video import Video
from lib.Process import F
from lib.Database import Database, DBWriter
from lib.Background import Background
from lib.Compress import VideoFile, VideoStream

from dateutil.parser import parse as dateparse
from base64 import b64encode
from itertools import repeat

from PIL import Image
from io import BytesIO
from uuid import uuid4

import matplotlib.pyplot as plt
import numpy as np

import traceback
import multiprocessing
import subprocess
import threading
import concurrent.futures
import shutil
import shlex
import pexpect
import queue
import asyncio
import fcntl
import tempfile
import time
import os
import sys




import matplotlib.pyplot as plt


async def main(args):
    
    if len(args) < 2: 
        print("""path/to/video/file.avi 2017-10-31 Name-of_video "Notes. Notes." """)
    else:
        print(await detect_video(*args))



crop_side = 200


async def detect_video(video_file, date = "NOW()", name = "Today", notes = ""):
    # note: "NOW()" may not work.
    
    cpus = multiprocessing.cpu_count()

    experiment_uuid = uuid4()
    experiment_day = dateparse(date)
    experiment_dir = os.path.join(config.experiment_dir, str(experiment_uuid))
    experiment = (experiment_uuid, experiment_day, name, "detection", notes)
    vwidth, vheight, fps = 2336 - (crop_side*2), 1729, 300
    queue_max_size = 100
    db_queue_max_size = 300
    
    try:
        
        print("Creating data directory", experiment_dir)
        os.mkdir(experiment_dir)
        
        print("Launching Database Writer")
        
        dbwriter = DBWriter()
        wq = dbwriter.input()
        dbwriter.start()
        
        print("Inserting experiment", name, "(", experiment_uuid, ") into database.")
        wq.push(("execute", """
            INSERT INTO Experiment (experiment, day, name, method, notes) 
            VALUES ($1, $2, $3, $4, $5)
            """, experiment))
        
        print("Starting processor pipeline.")
        (   FrameIter(wq, video_file, experiment_uuid)
            .sequence()
            .count("Input Frame")
            .into(FrameProcessor(experiment_dir))
            .into(PropertiesProcessor())
            .into(CropProcessor())
            .order()
            .split([
                DetectionProcessor(experiment_dir),
                ParticleCommitter(wq).into(CropWriter(experiment_dir))
            ])
            .merge()
            .count("Output Frame")
            .execute()
        )
    
    except Exception as e:
        
        print("Uh oh. Something went wrong")
        
        traceback.print_exc()
        dbwriter.rollback()
        wq.push(None)
        
        if os.path.exists(experiment_dir):
            print("Removing files from", experiment_dir)
            shutil.rmtree(experiment_dir)

    else:
        
        dbwriter.commit()
        wq.push(None)
        
    finally:
        
        print("Fin.")
        
    return experiment_uuid



class FrameIter(F):
    def setup(self, wq, video_file, experiment_uuid):
        
        print("Starting FrameIter")
        
        self.meta["experiment_uuid"] = experiment_uuid
        self.meta["experiment_dir"] = os.path.join(config.experiment_dir, str(experiment_uuid))
        
        raw_compressor = VideoFile(video_file, self.meta["experiment_dir"], "raw.mp4")
        raw_compressor.start()
        
        norm_compressor = VideoStream(self.meta["experiment_dir"], "extraction.mp4", pix_format="gray")
        self.norm_q = norm_compressor.input()
        norm_compressor.start()
        
        print("Loading video.")
        video = Video(video_file)
        
        print("Saving background.")
        io.imsave(os.path.join(self.meta["experiment_dir"], "bg.png"), video.extract_background().squeeze())
        
        print("Iterating through frames.")
        for i in range(len(self.video)):
            if self.stopped():
                raw_compressor.stop()
                norm_compressor.stop()
            else:
                
                frame_uuid = uuid4()
                self.meta["frame_uuid"] = frame_uuid
                self.meta["frame_number"] = i
                
                wq.push(("execute", """
                    INSERT INTO Frame (frame, experiment, number)
                    VALUES ($1, $2, $3)
                """, (frame_uuid, experiment_uuid, i)))
                
                frame = video.normal_frame(i)
                
                self.norm_q.push(frame.tobytes())
                
                print("Pushing frame", i)
                
                self.push(frame)
        
        self.stop()
    
    def teardown(self):
        self.norm_q.push(None)





class FrameProcessor(F):
    def setup(self, experiment_dir):
        mask_compressor = VideoStream(experiment_dir, "mask.mp4", pix_format="gray")
        self.mask_q = mask_compressor.input()
        mask_compressor.start()
    
    def do(self, frame):
        
        sframe = frame.squeeze()
        thresh  = threshold(sframe)
        binary  = binary_opening((sframe < thresh), square(3))
        cleared = clear_border(binary)
        labeled = label(cleared)
        filtered = remove_small_objects(labeled, 64)
        properties = regionprops(filtered, sframe)
        
        self.mask_q.push((filtered.squeeze().astype("uint8") * 255).tobytes())
        
        self.meta["frame"] = frame
        self.push(properties)
            
    def teardown(self):
        self.mask_q.put(None)



class PropertiesProcessor(F):
    def do(self, properties):
        
        cropper = Crop(self.meta["frame"])
    
        coords = [(p.centroid[1], p.centroid[0]) for p in properties]
        bboxes = [((p.bbox[1], p.bbox[0]), (p.bbox[3], p.bbox[2])) for p in properties]
        crops = np.array([cropper.crop(int(round(c[0])), int(round(c[1]))) for c in coords])
        pcrops = np.array([Classifier.preproc(None, crop) for crop in crops])
        
        self.meta["properties"] = properties
        self.push((crops, pcrops, coords, bboxes))
    


class CropProcessor(F):
    def setup(self):
        from lib.models.Classifier import Classifier
        self.classifier = Classifier().load()
    
    def make_batch(self, iterable, n=1):
        #https://stackoverflow.com/a/8290508
        l = len(iterable)
        for ndx in range(0, l, n):
            yield iterable[ndx:min(ndx + n, l)]
    
    def do(self, cpcb):
        crops, pcrops, coords, bboxes = cpcb
        latents, categories = [], []
        
        for crop_batch in self.make_batch(pcrops, batchSize):
                
            # need to pad the array of crop images into a number divisible by the # of GPUs
            crop_batch_padded = np.lib.pad(crop_batch, ((0, len(crop_batch) % config.GPUs), (0,0), (0,0), (0,0)), 'constant', constant_values=0)
            
            l = self.classifier.encoder.predict(crop_batch_padded.reshape((len(crop_batch_padded), *(crop_batch_padded[0].shape))))
            c = [np.argmax(c) for c in self.classifier.featureclassifier.predict(l.reshape(len(l), *(l[0].shape)))]
            
            latents += list(l[0:len(crop_batch)])
            categories += list(c[0:len(crop_batch)])
        
        self.push((crops, latents, categories, properties, coords, bboxes))
        
    


class DetectionProcessor(F):
    def setup(self, experiment_dir):
        self.detection_compressor = VideoStream(experiment_dir, "detection.mp4", pix_format="rgb24")
        self.detc_q = self.detection_compressor.input()
        self.detection_compressor.start()
        
    def do(self, detections):
        
        (crops, latents, categories, properties, coords, bboxes) = detections
        
        detection_frame = gray2rgb(self.meta["frame"].copy()).astype("int32")
            
        for x, p in enumerate(properties):
            rr, cc = circle(*p.centroid, p.major_axis_length, detection_frame.shape)
            if categories[x] == 0: # Undefined
                detection_frame[rr, cc, 0] += 25
                detection_frame[rr, cc, 1] += 25 # R+G = Orange
            if categories[x] == 1: # Unknown
                detection_frame[rr, cc, 1] += 25
                detection_frame[rr, cc, 2] += 25 # G+B = Cyan
            if categories[x] == 2: # Bitumen
                detection_frame[rr, cc, 2] += 50 # Blue
            if categories[x] == 3: # Sand
                detection_frame[rr, cc, 0] += 50 # Red
            if categories[x] == 4: # Bubbple
                detection_frame[rr, cc, 1] += 50 # Green
        
        self.dect_q.push(detection_frame.tobytes())
    
    def teardown(self):
        self.dect_q.push(None)
        
        

class ParticleCommitter(F):
    def setup(self, wq):
        self.wq = wq
    
    def do(self, detections):
        
        (crops, latents, categories, properties, coords, bboxes) = detections
        
        experiment_uuid = self.meta("experiment_uuid")
        frame_uuid = self.meta["frame_uuid"]
            
        particles = [(uuid4(), self.experiment_uuid, p.area, p.mean_intensity, p.perimeter, p.major_axis_length, categories[i]) 
            for i, p in enumerate(properties)]
            
        track_uuids = [uuid4() for i in range(len(properties))]
            
        tracks = [(track_uuids[i], frame_uuid, particles[i][0], coords[i], bboxes[i], ",".join(list(latents[i].astype("str"))))
            for i, p in enumerate(properties)]
            
        self.wq.push(("executemany", """
            INSERT INTO Particle (particle, experiment, area, intensity, perimeter, radius, category)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, (particles,)))
        
        
        self.wq.push(("executemany", """
            INSERT INTO Track (track, frame, particle, location, bbox, latent)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, (tracks,)))
            
            
        self.push((track_uuids, crops))
        



class CropWriter(F):
    def setup(self, experiment_dir):
        self.experiment_dir = experiment_dir
        
    
    def do(self, track_crops):
        frame_uuid = str(self.meta["frame_uuid"])
        frame_dir = os.path.join(self.experiment_dir, frame_uuid)
        track_uuids, crops = track_crops
        
        os.makedirs(frame_dir, exist_ok=True)
                    
        for i, crop in enumerate(crops):
            io.imsave(os.path.join(frame_dir, str(track_uuids[i]) + ".jpg"), crop.squeeze(), quality=90) 
