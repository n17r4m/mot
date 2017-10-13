
from skimage import io
from skimage.transform import downscale_local_mean
from skimage.filters import threshold_minimum
from skimage.segmentation import clear_border, random_walker
from skimage.measure import label, regionprops
from skimage.morphology import binary_opening, square, remove_small_objects


import config

from lib.Crop import Crop
from lib.Video import Video
from lib.Database import Database
from lib.Background import Background
from lib.models.Classifier import Classifier

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

import tempfile
import time
import os
import sys

import matplotlib.pyplot as plt


async def main(args):
    
    if len(args) < 4: 
        
        print("What you want to process and insert?")
        print("USING: path/to/video/file.avi 2017-03-24 'experiment name' 'notes notes notes'")
    else:
        print(await insert_video(*args))




async def insert_video(video_fpath, date, name, notes):
    
    
    cpus = multiprocessing.cpu_count()
    loop = asyncio.get_event_loop()
    
    _db = Database()
    db, transaction = await _db.transaction()
    
    classifier = Classifier()
    classifier.load()
    
    experiment_uuid = uuid4()
    experiment_day = dateparse(date)
    experiment_dir = os.path.join(config.experiment_dir, str(experiment_uuid))
    
    experiment = (experiment_uuid, experiment_day, name, notes)
    
    
    try:
        
        
        print("Loading raw video for processing", video_fpath)
        
        video = Video(video_fpath)
        
        
        print("Creating data directory", experiment_dir)
        os.mkdir(experiment_dir)
        
        
        print("Launching ffmpeg for raw video compression")
        compressor_raw = VideoFileCompressor(video_fpath, experiment_dir, "raw.mp4")
        compressor_raw.start()
        
        print("Launching ffmpeg for extracted video compression")
        frame_bytes_queue = queue.Queue()
        compressor_norm = VideoStreamCompressor(frame_bytes_queue, experiment_dir, "extraction.mp4", str(video.width)+"x"+str(video.height), 300)
        compressor_norm.start()
        
        compressors = [compressor_raw, compressor_norm]
        
        
        cat_map = await _db.category_map()
        cat_map2 = ["X", "U", "O", "S", "B"]
        
        plt.ion()
        plt.show()
        
        print("Inserting experiment", name, "(", experiment_uuid, ") into database.")
        await db.execute("""
            INSERT INTO Experiment (experiment, day, name, notes) 
            VALUES ($1, $2, $3, $4)
            """, *experiment)
        
        
        
        print("Subtracting background from video")
        
        extracted = np.zeros([len(video), *video.shape], dtype="uint8")
        
        for i in range(100, 300): #len(video)):
            print("Processing frame", i)
            frame = video.normal_frame(i)
            sframe = frame.squeeze()
            
            frame_bytes_queue.put(frame.tobytes())
        
            cropper = Crop(frame)
            thresh  = threshold_minimum(sframe)
            binary  = binary_opening((sframe < thresh), square(3))
            cleared = clear_border(binary)
            labeled = label(cleared)
            filtered = remove_small_objects(labeled, 5)
            properties = regionprops(filtered, sframe)
            
            """
            plt.imshow(binary, cmap='gray', vmin = 0, vmax = 1)
            plt.draw()
            plt.pause(0.1)
            """
            
            frame = (uuid4(), experiment_uuid, i)
            await db.execute("""
                INSERT INTO Frame (frame, experiment, number)
                VALUES ($1, $2, $3)
            """, *frame)
            
            crop_dir = os.path.join(experiment_dir, str(frame[0]))
            os.mkdir(crop_dir)
            
            
            print("Found", len(properties), "particles.")
            batchSize = 300
            for b in batch(properties, batchSize):
                
                print(".", end='', flush=True)
                
                coords = [(p.centroid[1], p.centroid[0]) for p in b]
                bboxes = [((p.bbox[1], p.bbox[0]), (p.bbox[3], p.bbox[2])) for p in b]
                crops = np.array([cropper.crop(int(round(c[0])), int(round(c[1]))) for c in coords])
                pcrops = np.array([classifier.preproc(crop) for crop in crops])
                
                pcrops = np.lib.pad(pcrops, ((0, len(pcrops) % config.GPUs), (0,0), (0,0), (0,0)), 'constant', constant_values=0)
                
                print(".", end='', flush=True)
                
                latents = classifier.encoder.predict(pcrops.reshape((len(pcrops), *(pcrops[0].shape))))
                
                print(".", end='', flush=True)
                
                categories = [np.argmax(c) for c in classifier.featureclassifier.predict(latents.reshape(len(latents), *(latents[0].shape)))]
                
                print(".", end='', flush=True)
                
                particles = [(uuid4(), experiment_uuid, p.area, p.mean_intensity, p.perimeter, p.major_axis_length, categories[i]) 
                    for i, p in enumerate(b)]
                
                await db.executemany("""
                    INSERT INTO Particle (particle, experiment, area, intensity, perimeter, radius, category)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, particles)
                
                tracks = [(uuid4(), frame[0], particles[i][0], coords[i], bboxes[i], ",".join(list(latents[i].astype("str"))))
                    for i, p in enumerate(b)]
                
                await db.executemany("""
                    INSERT INTO Track (track, frame, particle, location, bbox, latent)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, tracks)
                
                print(".", end='', flush=True)
                
                [io.imsave(os.path.join(crop_dir, str(tracks[i][0]) + ".jpg"), crop.squeeze(), quality=90) 
                    for i, crop in enumerate(crops)]
                
                
                print(":", end='', flush=True)
                
                
                
                
                
            print("Done")
        
        """
        
        raise ValueError("Early bail")
        """
        
    
    except Exception as e:
        print("Uh oh. Something went wrong")
        traceback.print_exc()
        print("Waiting for compression to complete")
        frame_bytes_queue.put(None) # Close stream
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
        frame_bytes_queue.put(None) # Close stream
        [c.join() for c in compressors]
        
    finally:
        print("Fin.")
        
    return experiment[0]



def batch(iterable, n=1):
    #https://stackoverflow.com/a/8290508
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]




class VideoFileCompressor(threading.Thread):
    def __init__(self, video_fpath, experiment_dir, fname):
        super(VideoFileCompressor, self).__init__()
        self.stop_event = threading.Event()
        self.cmd = ''.join(('ffmpeg -i "{}"'.format(video_fpath),
          ' -c:v libx264 -crf 15 -preset fast',
          ' "{}"'.format(os.path.join(experiment_dir, fname))))
    
    def run(self):
        proc = subprocess.Popen(shlex.split(self.cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        for line in proc.stdout:
            if self.stopped():
                proc.kill()
    
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()
    
        


class VideoStreamCompressor(threading.Thread):
    def __init__(self, queue, experiment_dir, fname, video_size="2336x1729", fps=300, pix_format="gray"):
        super(VideoStreamCompressor, self).__init__()
        self.queue = queue
        self.stop_event = threading.Event()
        self.cmd = ''.join(('ffmpeg',
          ' -f rawvideo -pix_fmt {}'.format(pix_format),
          ' -video_size {}'.format(video_size),
          ' -framerate {}'.format(fps),
          ' -i -',
          ' -c:v libx264 -crf 15 -preset fast',
          ' -pix_fmt yuv422p',
          ' "{}"'.format(os.path.join(experiment_dir, fname))))
    
    def run(self):
        proc = subprocess.Popen(shlex.split(self.cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            if self.stopped():
                return self.close(proc)
            else:
                frame_bytes = self.queue.get()
                if frame_bytes is None:
                    return self.close(proc)
                proc.stdin.write(frame_bytes)
    
    def close(self, proc):
        proc.stdin.close()
        proc.wait()
    
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()
