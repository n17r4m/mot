
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
        print("""path/to/video/file.avi 2017-10-31 Name-of_video "Notes. Notes." """)
    else:
        print(await detect_video(*args))



crop_side = 200


async def detect_video(video_fpath, date = "NOW()", name = "Today", notes = ""):
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
        db_writer_queue = multiprocessing.Queue(db_queue_max_size) # (method, query, args)
        db_writer = DBWriter(db_writer_queue)
        db_writer.start()
        
        print("Inserting experiment", name, "(", experiment_uuid, ") into database.")
        db_writer_queue.put(("execute", """
            INSERT INTO Experiment (experiment, day, name, method, notes) 
            VALUES ($1, $2, $3, $4, $5)
            """, experiment))
        
        
        
        print("Launching ffmpeg for raw video compression")
        compressor_raw = VideoFileCompressor(video_fpath, experiment_dir, "raw.mp4", vwidth, vheight)
        compressor_raw.start()
        
        print("Launching ffmpeg for extracted video compression")
        frame_bytes_norm = multiprocessing.Queue(queue_max_size) # bytes
        compressor_norm = VideoStreamCompressor(frame_bytes_norm, experiment_dir, "extraction.mp4", vwidth, vheight, fps, pix_format="gray")
        compressor_norm.start()
        
        print("Launching ffmpeg for binary mask visualization")
        frame_bytes_mask = multiprocessing.Queue(queue_max_size)  # bytes 
        compressor_mask = VideoStreamCompressor(frame_bytes_mask, experiment_dir, "mask.mp4", vwidth, vheight, fps, pix_format="gray" )
        compressor_mask.start()
        
        print("Launching ffmpeg for particle detection visualization")
        frame_bytes_detect = multiprocessing.Queue(queue_max_size)  # bytes
        compressor_detect = VideoStreamCompressor(frame_bytes_detect, experiment_dir, "detection.mp4", vwidth, vheight, fps, pix_format="rgb24" )
        compressor_detect.start()
        
        
        print("Launching Frame Getter")
        frame_queue = multiprocessing.Queue(queue_max_size) # (frame_uuid, normal_frame)
        frame_getter = VideoFrameGetter(video_fpath, experiment_uuid, db_writer_queue, frame_queue, frame_bytes_norm)
        frame_getter.start()
        
    
        print("Launching Frame Processor")
        frame_properties_queue = multiprocessing.Queue(queue_max_size) # (frame_uuid, frame, properties)
        frame_processors = []
        
        frame_processor_mask_queue = multiprocessing.Queue(queue_max_size)
        frame_processor_orderer = OrderProcessor(frame_processor_mask_queue, frame_bytes_mask)
        frame_processor_orderer.start()
        for g in range(config.GPUs):
            frame_processor = VideoFrameProcessor(frame_queue, frame_properties_queue, frame_processor_mask_queue)
            frame_processor.start()
            frame_processors.append(frame_processor)
        
        
        print("Launching Crop Writer")
        crop_writer_queue = multiprocessing.Queue(queue_max_size) # (frame_uuid, track_uuids, crops)
        crop_writer = CropWriter(experiment_dir, crop_writer_queue)
        crop_writer.start()
        
        print("Launching Crop Processor")
        frame_crops_queue = multiprocessing.Queue(queue_max_size) # (frame_uuid, frame, crops, pcrops, properties, coords, bboxes)
        crop_processors = []
        for g in range(config.GPUs):
            crop_processor = FrameCropProcessor(frame_properties_queue, frame_crops_queue)
            crop_processor.start()
            crop_processors.append(crop_processor)
            
            
        print("Launching Detection Video Writer")
        frame_detection_orderer_queue = multiprocessing.Queue(queue_max_size)
        frame_detection_orderer = OrderProcessor(frame_detection_orderer_queue, frame_bytes_detect)
        frame_detection_orderer.start()
        frame_detection_queue = multiprocessing.Queue(queue_max_size) # (normal_frame, properties, categories)
        detection_processors = []
        for g in range(config.GPUs):
            detection_processor = DetectionProcessor(frame_detection_queue, frame_detection_orderer_queue)
            detection_processor.start()
            detection_processors.append(detection_processor)
        
        
        print("Launching Classification Engine")
        lcp_queue = multiprocessing.Queue(queue_max_size) # (frame_uuid, crops, latents, categories, properties)
        classifiers = []
        for g in range(config.GPUs):
            os.environ["CUDA_VISIBLE_DEVICES"] = str(g)
            classifier = Classy(frame_crops_queue, lcp_queue, frame_detection_queue)
            classifier.start()
            classifiers.append(classifier)
            
        
        
        print("Launching Particle Commmitter")
        particle_commiter = ParticleCommitter(experiment_uuid, lcp_queue, crop_writer_queue, db_writer_queue)
        particle_commiter.start()
        
        processors = [frame_getter, frame_processor, frame_processor_orderer, frame_detection_orderer, crop_writer, *crop_processors, *classifiers, *detection_processors, particle_commiter, db_writer]
        compressors = [compressor_raw, compressor_norm, compressor_detect, compressor_mask, crop_writer]

        proc_buffers = [frame_queue, frame_properties_queue, frame_crops_queue, lcp_queue, db_writer_queue, crop_writer_queue, frame_processor_mask_queue, frame_detection_orderer_queue, frame_detection_queue]
        frame_buffers = [frame_bytes_norm, frame_bytes_detect, frame_bytes_mask]
        
        all_processors = processors + compressors
        all_buffers = proc_buffers + frame_buffers
        
        print("Launching Watchdog")
        watchdog = Watchdog(all_buffers)
        watchdog.start()
           
    
    except Exception as e:
        print("Uh oh. Something went wrong")
        traceback.print_exc()
        
        [c.stop() for c in all_processors]
        [q.put(None) for q in all_buffers]
        [c.join() for c in all_processors]
        
        if os.path.exists(experiment_dir):
            print("Removing files from", experiment_dir)
            shutil.rmtree(experiment_dir)
        
        watchdog.stop()
        watchdog.join()
        
    else:
        
        print("Waiting for all processes to complete.")
        [c.join() for c in all_processors]
        watchdog.stop()
        watchdog.join()
        
    finally:
        print("Fin.")
        
    return experiment[0]






class Watchdog(multiprocessing.Process):
    def __init__(self, queues):
        super(Watchdog, self).__init__()
        self.queues = queues
        self.stop_event = multiprocessing.Event()
    def run(self):
        while True:
            if self.stopped():
                return
            print([q.qsize() for q in self.queues])
            time.sleep(5)
        
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()







class VideoFrameGetter(multiprocessing.Process):
    def __init__(self, video_path, experiment_uuid, db_writer_queue, frame_queue, frame_bytes_norm):
        super(VideoFrameGetter, self).__init__()
        self.video_path = video_path
        self.experiment_uuid = experiment_uuid
        self.db_writer_queue = db_writer_queue
        self.frame_queue = frame_queue
        self.frame_bytes_norm = frame_bytes_norm
        self.stop_event = multiprocessing.Event()
        
    def run(self):
        
        video = Video(self.video_path)
        
        experiment_dir = os.path.join(config.experiment_dir, str(self.experiment_uuid))
        io.imsave(os.path.join(experiment_dir, "bg.png"), video.extract_background().squeeze())
        
        for i in range(len(video)):
            if self.stopped():
                break
            else: 
                print("Processing frame", i)
                
                frame_uuid = uuid4()
                frame_insert = (frame_uuid, self.experiment_uuid, i)
                
                self.db_writer_queue.put(("execute", """
                    INSERT INTO Frame (frame, experiment, number)
                    VALUES ($1, $2, $3)
                """, frame_insert))
                
                
                frame = video.normal_frame(i)
                frame = frame[:, crop_side:-crop_side]
                self.frame_bytes_norm.put(frame.tobytes())
                self.frame_queue.put((frame_uuid, i, frame))
        
        self.frame_bytes_norm.put(None)
        for g in range(config.GPUs):
            self.frame_queue.put(None) 
        
        print("VideoFrameGetter Exiting")
        
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()


class VideoFrameProcessor(multiprocessing.Process):
    def __init__(self, frame_queue, frame_properties_queue, frame_processor_mask_queue):
        super(VideoFrameProcessor, self).__init__()

        self.frame_queue = frame_queue
        self.frame_properties_queue = frame_properties_queue
        self.frame_processor_mask_queue = frame_processor_mask_queue
        self.stop_event = multiprocessing.Event()

    
    def run(self):
        
        while True:
            if self.stopped():
                break
            
            frame_data = self.frame_queue.get()
            if frame_data is None:
                break
            
            frame_uuid, i, frame = frame_data
            
            sframe = frame.squeeze()
            
            thresh  = threshold(sframe)
            binary  = binary_opening((sframe < thresh), square(3))
            cleared = clear_border(binary)
            labeled = label(cleared)
            filtered = remove_small_objects(labeled, 64)
            properties = regionprops(filtered, sframe)
            
            self.frame_processor_mask_queue.put((i, (filtered.squeeze().astype("uint8") * 255).tobytes()))
            self.frame_properties_queue.put((frame_uuid, i, frame, properties))
            
        
        self.frame_processor_mask_queue.put(None)
        self.frame_properties_queue.put(None)
        print("VideoFrameProcessor Exiting")
            
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()


        
        

class FrameCropProcessor(multiprocessing.Process):
    def __init__(self, frame_properties_queue, frame_crops_queue):
        super(FrameCropProcessor, self).__init__()
        self.frame_properties_queue = frame_properties_queue
        self.frame_crops_queue = frame_crops_queue
        self.stop_event = multiprocessing.Event()
    
    def run(self):
        while True:
            if self.stopped():
                break 
            frame_props = self.frame_properties_queue.get()
            if frame_props is None:
                break
            
            frame_uuid, i, frame, properties = frame_props
            
            cropper = Crop(frame)
            
            coords = [(p.centroid[1], p.centroid[0]) for p in properties]
            bboxes = [((p.bbox[1], p.bbox[0]), (p.bbox[3], p.bbox[2])) for p in properties]
            crops = np.array([cropper.crop(int(round(c[0])), int(round(c[1]))) for c in coords])
            pcrops = np.array([Classifier.preproc(None, crop) for crop in crops])
            
            self.frame_crops_queue.put((frame_uuid, i, frame, crops, pcrops, properties, coords, bboxes))
        
        self.frame_crops_queue.put(None)
        
        print("FrameCropProcessor Exiting")
            
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()



      




class Classy(multiprocessing.Process):
    def __init__(self, crop_queue, latents_categories_properties_queue, frame_detection_queue):
        super(Classy, self).__init__()
        self.crop_queue = crop_queue
        self.lcp_queue = latents_categories_properties_queue 
        self.frame_detection_queue = frame_detection_queue
        self.stop_event = multiprocessing.Event()
    
    def batch(self, iterable, n=1):
        #https://stackoverflow.com/a/8290508
        l = len(iterable)
        for ndx in range(0, l, n):
            yield iterable[ndx:min(ndx + n, l)]

    def run(self):
        print("Classifier running on GPU", os.environ["CUDA_VISIBLE_DEVICES"])
        classifier = Classifier().load()
        batchSize = 512
        while True:
            if self.stopped():
                break
            
            crop_data = self.crop_queue.get()
            if crop_data is None:
                break
            
            frame_uuid, i, frame, crops, pcrops, properties, coords, bboxes = crop_data
            
            latents = []
            categories = []
            
            for crop_batch in self.batch(pcrops, batchSize):
                
                # need to pad the array of crop images into a number divisible by the # of GPUs
                crop_batch_padded = np.lib.pad(crop_batch, ((0, len(crop_batch) % config.GPUs), (0,0), (0,0), (0,0)), 'constant', constant_values=0)
                
                l = classifier.encoder.predict(crop_batch_padded.reshape((len(crop_batch_padded), *(crop_batch_padded[0].shape))))
                c = [np.argmax(c) for c in classifier.featureclassifier.predict(l.reshape(len(l), *(l[0].shape)))]
                
                latents += list(l[0:len(crop_batch)])
                categories += list(c[0:len(crop_batch)])
                
            self.lcp_queue.put((frame_uuid, crops, latents, categories, properties, coords, bboxes))
            self.frame_detection_queue.put((i, frame, properties, categories))
        
        self.lcp_queue.put(None)
        self.frame_detection_queue.put(None)
        print("Classy Exiting")
    
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()
        


class DetectionProcessor(multiprocessing.Process):
    def __init__(self, detection_queue, detection_orderer_queue):
        super(DetectionProcessor, self).__init__()
        self.detection_queue = detection_queue
        self.detection_orderer_queue = detection_orderer_queue
        self.stop_event = multiprocessing.Event()
    
    def run(self):
        
        while True:
            if self.stopped():
                break
            detections = self.detection_queue.get()
            if detections is None:
                break
                
            i, frame, properties, categories = detections
            detection_frame = gray2rgb(frame.squeeze().copy()).astype("int32")
            
            
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
            
            detection_frame = np.clip(detection_frame, 0, 255)
            self.detection_orderer_queue.put((i, detection_frame.astype("uint8").tobytes()))
        
        self.detection_orderer_queue.put(None)
        print("DetectionProcessor Exiting")
             
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()     


class ParticleCommitter(multiprocessing.Process):
    def __init__(self, experiment_uuid, lcp_queue, crop_writer_queue, db_writer_queue):
        super(ParticleCommitter, self).__init__()
        self.experiment_uuid = experiment_uuid
        self.lcp_queue = lcp_queue
        self.crop_writer_queue = crop_writer_queue
        self.db_writer_queue = db_writer_queue
        self.stop_event = multiprocessing.Event()
    
    def run(self):
        noneCounts = 0
        while True:
            if self.stopped():
                break
            lcp = self.lcp_queue.get()
            if lcp is None:
                noneCounts += 1
                if noneCounts >= config.GPUs:
                    break
                continue
            
            frame_uuid, crops, latents, categories, properties, coords, bboxes = lcp
            
            particles = [(uuid4(), self.experiment_uuid, p.area, p.mean_intensity, p.perimeter, p.major_axis_length, categories[i]) 
                for i, p in enumerate(properties)]
            
            track_uuids = [uuid4() for i in range(len(properties))]
            
            tracks = [(track_uuids[i], frame_uuid, particles[i][0], coords[i], bboxes[i], ",".join(list(latents[i].astype("str"))))
                for i, p in enumerate(properties)]
            
            self.db_writer_queue.put(("executemany", """
                INSERT INTO Particle (particle, experiment, area, intensity, perimeter, radius, category)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, (particles,)))
            
            
            self.db_writer_queue.put(("executemany", """
                INSERT INTO Track (track, frame, particle, location, bbox, latent)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, (tracks,)))
            
            
            self.crop_writer_queue.put((frame_uuid, track_uuids, crops))
        
        self.db_writer_queue.put(None)
        self.crop_writer_queue.put(None)
        print("ParticleCommitter Exiting")
    
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()


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
        
        proc = subprocess.Popen(shlex.split(self.cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        fcntl.fcntl(proc.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        with open("{}.log".format(os.path.join(self.edir, self.fname)), 'wb', 0) as log_file:
            while proc.poll() is None:
                try:
                    log_file.write(proc.stdout.read())
                except:
                    time.sleep(0.25)
                    
                time.sleep(0.25)
                if self.stopped():
                    proc.kill()
        print("VideoFileCompressor Exiting")
        
    
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
                        self.close(proc)
                        break
                    else:
                        proc.stdin.write(frame_bytes)
        print("VideoStreamCompressor Exiting")

    def close(self, proc):
        proc.stdin.close()
        proc.wait()
    
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()







class CropWriter(multiprocessing.Process):
    def __init__(self, experiment_dir, crop_queue):
        super(CropWriter, self).__init__()
        self.crop_queue = crop_queue
        self.edir = experiment_dir
        self.stop_event = multiprocessing.Event()
    
    def run(self):
        
        while True:
            if self.stopped():
                break
            else:
                crop_data = self.crop_queue.get()
                if crop_data is None:
                    break
                else:
                    frame_uuid, track_uuids, crops = crop_data
                    frame_uuid = str(frame_uuid)
                    frame_dir = os.path.join(self.edir, frame_uuid)
                    
                    os.makedirs(frame_dir, exist_ok=True)
                    
                    for i, crop in enumerate(crops):
                        io.imsave(os.path.join(frame_dir, str(track_uuids[i]) + ".jpg"), crop.squeeze(), quality=90) 
        print("CropWriter Exiting")
        
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()










class DBWriter(multiprocessing.Process):
    def __init__(self, queue):
        super(DBWriter, self).__init__()
        self.queue = queue
        self.stop_event = multiprocessing.Event()
        self.commit_event = multiprocessing.Event()
        
    def run(self):
        # await self.inner_loop(Database().transaction, self.queue)
        self.go(self.inner_loop, (self.queue,))
    
    def go(self, fn, args):
        return asyncio.new_event_loop().run_until_complete(fn(*args))
    
    # dun know if this works or not.. todo: test.
    async def inner_loop(self, queue):
        tx, transaction = await Database().transaction()
        print("DBWriter ready.")
        while True:
            if not self.stopped():
                sql_drop = self.queue.get()
                if sql_drop is None:
                    self.commit()
                else:
                    
                    method, query, args = sql_drop
                    await getattr(tx, method)(query, *args)
                
            else:
                if self.commit_event.is_set():
                    print("Comitting changes to database.")
                    await transaction.commit()
                else:
                    print("Rolling back database.")
                    await transaction.rollback()
                break
        print("DBWriter Exiting")
        
    def commit(self):
        self.commit_event.set()
        self.stop()
        
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()            

class OrderProcessor(multiprocessing.Process):
    def __init__(self, input_queue, output_queue):
        super(OrderProcessor, self).__init__()
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.stop_event = multiprocessing.Event()
    
    def run(self):
        pq = queue.PriorityQueue()
        seq = 0
        noneCount = 0
        while True:
            data = self.input_queue.get()
            if data is None:
                noneCount += 1
                if noneCount >= config.GPUs:
                    break
                continue
            pq.put(data)
            
            p, out = pq.get()
            
            
            
            if p == seq:
                self.output_queue.put(out)
                seq += 1
            else:
                pq.put((p, out))
        self.output_queue.put(None)
        print("OrderProcessor Exiting")
        
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()
