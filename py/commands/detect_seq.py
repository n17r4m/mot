
from skimage import io
from skimage.transform import downscale_local_mean
from skimage.filters import threshold_triangle as threshold
from skimage.segmentation import clear_border, random_walker
from skimage.measure import label, regionprops
from skimage.morphology import binary_opening, square, remove_small_objects
from skimage.color import gray2rgb
from skimage.draw import circle

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
import fcntl
import tempfile
import time
import os
import sys

import matplotlib.pyplot as plt


async def main(args):
    
    if len(args) < 2: 
        
        print("What you want to process and insert?")
        print("""USING: path/to/video/file.avi 2017-10-31 T_NAME_ViDEO "Notes." """)
    else:
        print(await detect_video(*args))




async def detect_video(video_fpath, date = "NOW()", name = "Today", notes = ""):
    # note: "NOW()" may not work.
    
    cpus = multiprocessing.cpu_count()

    experiment_uuid = uuid4()
    experiment_day = dateparse(date)
    experiment_dir = os.path.join(config.experiment_dir, str(experiment_uuid))
    experiment = (experiment_uuid, experiment_day, name, "detection", notes)
    
    
    try:
        
        
        print("Loading raw video for processing", video_fpath)
        
        video = Video(video_fpath)
        
        
        print("Creating data directory", experiment_dir)
        os.mkdir(experiment_dir)
        
        
        print("Launching ffmpeg for raw video compression")
        compressor_raw = VideoFileCompressor(video_fpath, experiment_dir, "raw.mp4", video.width, video.height)
        compressor_raw.start()
        
        print("Launching ffmpeg for extracted video compression")
        frame_bytes_norm = multiprocessing.Queue()
        compressor_norm = VideoStreamCompressor(frame_bytes_norm, experiment_dir, "extraction.mp4", video.width, video.height, 300, pix_format="gray")
        compressor_norm.start()
        
        print("Launching ffmpeg for binary mask visualization")
        frame_bytes_mask = multiprocessing.Queue()
        compressor_mask = VideoStreamCompressor(frame_bytes_mask, experiment_dir, "mask.mp4", video.width, video.height, 300, pix_format="gray" )
        compressor_mask.start()
        
        print("Launching ffmpeg for particle detection visualization")
        frame_bytes_detect = multiprocessing.Queue()
        compressor_detect = VideoStreamCompressor(frame_bytes_detect, experiment_dir, "detection.mp4", video.width, video.height, 300, pix_format="rgb24" )
        compressor_detect.start()
        
        print("Launching CropWriter process")
        crop_writer_queue = multiprocessing.Queue()
        crop_writer = CropWriter(crop_writer_queue, experiment_dir)
        crop_writer.start()
        
        print("Launching Database Writer")
        db_writer_queue = multiprocessing.Queue()
        db_writer = DBWriter(db_writer_queue)
        db_writer.start()
        
        print("Loading Classifier")
        classifier = Classifier().load()
        
        compressors = [compressor_raw, compressor_norm, compressor_detect, compressor_mask, crop_writer]
        frame_buffers = [frame_bytes_norm, frame_bytes_detect, frame_bytes_mask, crop_writer_queue]

        print("Inserting experiment", name, "(", experiment_uuid, ") into database.")
        db_writer_queue.put(("execute", """
            INSERT INTO Experiment (experiment, day, name, method, notes) 
            VALUES ($1, $2, $3, $4, $5)
            """, experiment))
        
        
        for i in range(len(video)):
            print("Processing frame", i)
            frame = video.normal_frame(i)
            
            detection_frame = gray2rgb(frame.squeeze().copy()).astype("int32")
            
            sframe = frame.squeeze()
            
            frame_bytes_norm.put(frame.tobytes())
        
            cropper = Crop(frame)
            thresh  = threshold(sframe)
            binary  = binary_opening((sframe < thresh), square(3))
            cleared = clear_border(binary)
            
            frame_bytes_mask.put((cleared.squeeze().astype("uint8") * 255).tobytes())
            
            labeled = label(cleared)
            filtered = remove_small_objects(labeled, 64)
            properties = regionprops(filtered, sframe)

            
            frame = (uuid4(), experiment_uuid, i)
            frame_uuid = frame[0]
            
            
            db_writer_queue.put(("execute", """
                INSERT INTO Frame (frame, experiment, number)
                VALUES ($1, $2, $3)
            """, frame))
            
            crop_dir = os.path.join(experiment_dir, str(frame[0]))
            os.mkdir(crop_dir)
            
            
            print("Found", len(properties), "particles.")
            batchSize = 1024
            for b in batch(properties, batchSize):
                
                print(".", end='', flush=True)
                
                coords = [(p.centroid[1], p.centroid[0]) for p in b]
                bboxes = [((p.bbox[1], p.bbox[0]), (p.bbox[3], p.bbox[2])) for p in b]
                crops = np.array([cropper.crop(int(round(c[0])), int(round(c[1]))) for c in coords])
                pcrops = np.array([classifier.preproc(crop) for crop in crops])
                
                # need to pad the array of crop images into a number divisible by the # of GPUs
                pcrops = np.lib.pad(pcrops, ((0, len(pcrops) % config.GPUs), (0,0), (0,0), (0,0)), 'constant', constant_values=0)
                
                print(".", end='', flush=True)
                
                latents = classifier.encoder.predict(pcrops.reshape((len(pcrops), *(pcrops[0].shape))))
                
                print(".", end='', flush=True)
                
                categories = [np.argmax(c) for c in classifier.featureclassifier.predict(latents.reshape(len(latents), *(latents[0].shape)))]
                
                print(".", end='', flush=True)
                
                particles = [(uuid4(), experiment_uuid, p.area, p.mean_intensity, p.perimeter, p.major_axis_length, categories[i]) 
                    for i, p in enumerate(b)]
                
                track_uuids = [uuid4() for i in range(len(b))]
                tracks = [(track_uuids[i], frame_uuid, particles[i][0], coords[i], bboxes[i], ",".join(list(latents[i].astype("str"))))
                    for i, p in enumerate(b)]
                
                crop_writer_queue.put((frame_uuid, track_uuids, crops))
                
                print(".", end='', flush=True)
                
                db_writer_queue.put(("executemany", """
                    INSERT INTO Particle (particle, experiment, area, intensity, perimeter, radius, category)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, (particles,)))
                
                
                db_writer_queue.put(("executemany", """
                    INSERT INTO Track (track, frame, particle, location, bbox, latent)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, (tracks,)))
                
                print(".", end='', flush=True)
                
                
                # colorize detection_frame
                for i, p in enumerate(b):
                    rr, cc = circle(*p.centroid, p.major_axis_length, sframe.shape)
                    if categories[i] == 0: # Undefined
                        detection_frame[rr, cc, 0] += 25
                        detection_frame[rr, cc, 1] += 25 # R+G = Orange
                    if categories[i] == 1: # Unknown
                        detection_frame[rr, cc, 1] += 25
                        detection_frame[rr, cc, 2] += 25 # G+B = Cyan
                    if categories[i] == 2: # Bitumen
                        detection_frame[rr, cc, 2] += 50 # Blue
                    if categories[i] == 3: # Sand
                        detection_frame[rr, cc, 0] += 50 # Red
                    if categories[i] == 4: # Bubbple
                        detection_frame[rr, cc, 1] += 50 # Green
                    
                
                print(":", end='', flush=True)
                
            detection_frame = np.clip(detection_frame, 0, 255)
            frame_bytes_detect.put(detection_frame.astype("uint8").tobytes())
            
            
            
            while max([b.qsize() for b in frame_buffers]) > 8 or db_writer_queue.qsize() > 128:
                print("queues:", frame_bytes_norm.qsize(), frame_bytes_detect.qsize(), frame_bytes_mask.qsize(), crop_writer_queue.qsize(), db_writer_queue.qsize())
                time.sleep(5)
            
           
    
    except Exception as e:
        print("Uh oh. Something went wrong")
        traceback.print_exc()
        print("Waiting for rollback")
        
        db_writer.stop()
        db_writer_queue.put(None)
        db_writer.join()
        
        [c.stop() for c in compressors]
        [b.put(None) for b in frame_buffers]
        [c.join() for c in compressors]
        
            
        if os.path.exists(experiment_dir):
            print("Removing files from", experiment_dir)
            shutil.rmtree(experiment_dir)
    
    else:
        print("Comitting changes to database.")
        db_writer.commit()
        db_writer_queue.put(None)
        db_writer.join()
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



class VideoFileCompressor(multiprocessing.Process):
    def __init__(self, video_fpath, experiment_dir, fname, width=2336, height=1729, fps=300., rate=24.):
        super(VideoFileCompressor, self).__init__()
        self.edir = experiment_dir
        self.fname = fname
        self.stop_event = multiprocessing.Event()
        self.cmd = ''.join(('ffmpeg -i "{}"'.format(video_fpath),
          ' -c:v libx264 -crf 15 -preset fast',
          ' -pix_fmt yuv420p',
          ' -filter:v "setpts={}*PTS'.format(fps/rate),
          ', crop={}:{}:0:0"'.format(width, height-1) if height % 2 else '"',
          ' -r 24',
          ' -movflags +faststart',
          ' "{}"'.format(os.path.join(experiment_dir, fname))))
    
    def run(self):
        proc = subprocess.Popen(shlex.split(self.cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        fcntl.fcntl(proc.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        with open("{}.log".format(os.path.join(self.edir, self.fname)), 'wb', 0) as log_file:
            while proc.poll() is None:
                try:
                    log_file.write(proc.stdout.read())
                except:
                    time.sleep(0.5)
                
                if self.stopped():
                    proc.kill()
            
        
    
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()
    
        

class VideoStreamCompressor(multiprocessing.Process):
    def __init__(self, queue, experiment_dir, fname, width=2336, height=1729, fps=300., rate=24., pix_format="gray"):
        super(VideoStreamCompressor, self).__init__()
        self.queue = queue
        self.edir = experiment_dir
        self.fname = fname
        self.stop_event = multiprocessing.Event()
        self.cmd = ''.join(('ffmpeg',
          ' -f rawvideo -pix_fmt {}'.format(pix_format),
          ' -video_size {}x{}'.format(width,height),
          ' -framerate {}'.format(fps),
          ' -i -',
          ' -c:v libx264 -crf 15 -preset fast',
          ' -pix_fmt yuv420p',
          ' -filter:v "setpts={}*PTS'.format(fps/rate),
          ', crop={}:{}:0:0"'.format(width, height-1) if height % 2 else '"',
          ' -r 24',
          ' -movflags +faststart',
          ' "{}"'.format(os.path.join(experiment_dir, fname))))
    
    def run(self):
        proc = subprocess.Popen(shlex.split(self.cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        fcntl.fcntl(proc.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        with open("{}.log".format(os.path.join(self.edir, self.fname)), 'wb', 0) as log_file:
            while True:
                try:
                    log_file.write(proc.stdout.read())
                except:
                    pass
                
                if self.stopped():
                    return self.close(proc)
                else:
                    frame_bytes = self.queue.get()
                    if frame_bytes is None:
                        return self.close(proc)
                    else:
                        proc.stdin.write(frame_bytes)

                        
                
    
    def close(self, proc):
        proc.stdin.close()
        proc.wait()
    
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()



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
                    frame_uuid, track_uuids, crops = crop_data
                    frame_uuid = str(frame_uuid)
                    #print(crops[0].shape, np.min(crops[0]), np.max(crops[0]))
                    for i, crop in enumerate(crops):
                        io.imsave(os.path.join(self.edir, frame_uuid, str(track_uuids[i]) + ".jpg"), crop.squeeze(), quality=90) 
                
    
    def close(self, proc):
        proc.stdin.close()
        proc.wait()
    
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()



# 2am madness follows




def go(fn, args):
    return asyncio.new_event_loop().run_until_complete(fn(*args))


class DBWriter(multiprocessing.Process):
    def __init__(self, queue):
        super(DBWriter, self).__init__()
        self.queue = queue
        self.stop_event = multiprocessing.Event()
        self.commit_event = multiprocessing.Event()
        
    def run(self):
        # await self.inner_loop(Database().transaction, self.queue)
        go(self.inner_loop, (Database().transaction, self.queue))
    
    # dun know if this works or not.. todo: test.
    async def inner_loop(self, tx, queue):
        tx, transaction = await tx()
        print("DBWriter ready.")
        while True:
            if not self.stopped():
                sql_drop = self.queue.get()
                if sql_drop is None:
                    pass
                else:
                    method, query, args = sql_drop
                    await getattr(tx, method)(query, *args)
            else:
                if self.stop_event.is_set():
                    await transaction.commit()
                else:
                    await transaction.rollback()
                return
    
    def commit(self):
        self.commit_event.set()
        self.stop()
        
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()            


# class DBTransciever(multiprocessing.Process):
#     """TODO, R/W support"""
#      def __init__(self, queue):
#         super(DBTransciver, self).__init__()




# class Classy(multiprocessing.Process):
#     def __init__(self, preprocessed_crops_queue, latents_categories_mirror_queue = None):
#         super(Classy, self).__init__()
#         self.pc = preprocessed_crops_queue
#         self.lcm = latents_categories_mirror_queue # or dump_queue()
#         self.stop_event = multiprocessing.Event()
        
#     def run(self):
#         return go(self.inner_loop, self, Classifier().load(), self.pc, self.lcm)
    
    
#     async def inner_loop(self, classifier, crops, queue):
#         while True:
            
#             if not self.stopped():
#                 crop_batch = crops.get()
#                 if crop_batch is None:
#                     return
#                 else:
#                     # todo: test if further proc splitting helps or hinders
#                     categories = [np.argmax(c) for c in classifier.featureclassifier.predict(latents.reshape(len(latents), *(latents[0].shape)))]
#                     latents = classifier.encoder.predict(crop_batch.reshape((len(crop_batch), *(crop_batch[0].shape))))
#                     mirror = classifier.decoder.predict(latents.reshape((len(latents), *(latents[0].shape))))
#                     queue.put((categories, latents, mirror))
#             else:
#                 queue.put(None)
#                 return
            
