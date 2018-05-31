"""
2018-04-18
This is a modified legacy detection pipeline.

It's construction is for validating linescan / megaspeed data. 

It's designed to be fast, and use the previous multiprocessing facilities.

I reverted to this older code because I had trouble with mpyx library. 

The mpyx.Video video reader (skvideo.io.vread) loads the entire video into 
memory - this takes about 30 seconds. Also, the MegaSpeed videos have a last 
frame problem, and the video reader shits the bed as a result. Check if Martin's 
patch has been applied. https://github.com/scikit-video/scikit-video/issues/60

Currently handles:
- db writing (make experiment, frames, particles, tracks)
- video creation (raw, extraction, mask{labelled})
- detection
- crop writing
- segments using magic pixel work from detect_mp1

Todo:
-use newer video reader/background code <- for speed improvements.
"""

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
from mpyx.Video import Video

# from mpyx.Process import F

from mpyx.F import EZ, F
from mpyx.Vid import FFmpeg, BG, FG, Binary

from lib.Database import Database

from dateutil.parser import parse as dateparse
from base64 import b64encode
from itertools import repeat
import warnings

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


# crop_side = 0

"""
This is the main function. It performs detection, writes information to the 
database, creates some directories for the file resources,
and makes a few videos for later inspection.

Because it's multiprocessing, there is a lot of python3 input/output queue
code. This makes the code pretty nasty to look at, but don't be intimidated.

"""


async def detect_video(video_fpath, date="NOW()", name="Today", notes=""):
    verbose = False
    # note: "NOW()" may not work.

    cpus = multiprocessing.cpu_count()

    experiment_uuid = uuid4()
    experiment_day = dateparse(date)
    experiment_dir = os.path.join(config.experiment_dir, str(experiment_uuid))
    experiment = (experiment_uuid, experiment_day, name, "detection", notes)
    # vwidth, vheight, fps = 2336 - (crop_side*2), 1729, 300
    vwidth, vheight, fps = 2336, 1729, 300
    queue_max_size = 100
    db_queue_max_size = 300

    try:

        if verbose:
            print("Creating data directory", experiment_dir)
        os.mkdir(experiment_dir)

        if verbose:
            print("Launching Database Writer")
        db_writer_queue = multiprocessing.Queue(
            db_queue_max_size
        )  # (method, query, args)
        db_writer = DBWriter(db_writer_queue)
        db_writer.start()

        if verbose:
            print(
                "Inserting experiment", name, "(", experiment_uuid, ") into database."
            )
        db_writer_queue.put(
            (
                "execute",
                """
            INSERT INTO Experiment (experiment, day, name, method, notes) 
            VALUES ($1, $2, $3, $4, $5)
            """,
                experiment,
            )
        )

        """
        Here's the begining of the nasty multiprocessing code.
        
        There are 'processors', which can have input / output queues.
        
        A processor can take things off its input queue, process the things,
        and then add something (a result) to its output queue.
        We might call these "nodes"
        
        A processor might not need an input queue (eg. its job is to open a 
        video and put the video frames in its output queue). 
        We might call these "sources".
        
        
        A processor might not need an output queue (eg. its job is to write 
        things to the database)
        We might call these "sinks".
        """
        if verbose:
            print("Launching ffmpeg for raw video compression")

        """
        This node takes the video file path and creates a compressed version,
        storing the result in the experiment directory.
        
        """
        compressor_raw = VideoFileCompressor(
            video_fpath, experiment_dir, "raw.mp4", vwidth, vheight
        )
        compressor_raw.start()

        if verbose:
            print("Launching ffmpeg for extracted video compression")
        """
        The next two nodes needs an input queue "frame_bytes_norm"
        We'll put video frames that have been processed on this queue, 
        and the processor will create a video with them.
        
        """
        frame_bytes_norm = multiprocessing.Queue(queue_max_size)  # bytes
        compressor_norm = VideoStreamCompressor(
            frame_bytes_norm,
            experiment_dir,
            "extraction.mp4",
            vwidth,
            vheight,
            fps,
            pix_format="gray",
        )
        compressor_norm.start()

        if verbose:
            print("Launching ffmpeg for binary mask visualization")
        frame_bytes_mask = multiprocessing.Queue(queue_max_size)  # bytes
        compressor_mask = VideoStreamCompressor(
            frame_bytes_mask,
            experiment_dir,
            "mask.mp4",
            vwidth,
            vheight,
            fps,
            pix_format="gray",
        )
        compressor_mask.start()

        if verbose:
            print("Launching Frame Getter")
        frame_queue = multiprocessing.Queue(
            queue_max_size
        )  # (frame_uuid, normal_frame)
        frame_getter = VideoFrameGetter(
            video_fpath, experiment_uuid, db_writer_queue, frame_queue, frame_bytes_norm
        )
        frame_getter.start()

        if verbose:
            print("Launching Frame Processor")
        frame_properties_queue = multiprocessing.Queue(
            queue_max_size
        )  # (frame_uuid, frame, properties)
        frame_processors = []

        frame_processor_mask_queue = multiprocessing.Queue(queue_max_size)
        frame_processor_orderer = OrderProcessor(
            frame_processor_mask_queue, frame_bytes_mask
        )
        frame_processor_orderer.start()
        for g in range(config.GPUs):
            frame_processor = VideoFrameProcessor(
                frame_queue, frame_properties_queue, frame_processor_mask_queue
            )
            frame_processor.start()
            frame_processors.append(frame_processor)

        if verbose:
            print("Launching Crop Writer")
        crop_writer_queue = multiprocessing.Queue(
            queue_max_size
        )  # (frame_uuid, track_uuids, crops)
        crop_writer = CropWriter(experiment_dir, crop_writer_queue)
        crop_writer.start()

        if verbose:
            print("Launching Crop Processor")
        frame_crops_queue = multiprocessing.Queue(
            queue_max_size
        )  # (frame_uuid, frame, crops, pcrops, properties, coords, bboxes)
        crop_processors = []
        for g in range(config.GPUs):
            crop_processor = FrameCropProcessor(
                frame_properties_queue, frame_crops_queue
            )
            crop_processor.start()
            crop_processors.append(crop_processor)

        if verbose:
            print("Launching Classification Engine")
        lcp_queue = multiprocessing.Queue(
            queue_max_size
        )  # (frame_uuid, crops, latents, categories, properties)
        classifiers = []
        for g in range(config.GPUs):
            os.environ["CUDA_VISIBLE_DEVICES"] = str(g)
            classifier = Classy(frame_crops_queue, lcp_queue)
            classifier.start()
            classifiers.append(classifier)

        if verbose:
            print("Launching Particle Commmitter")
        particle_commiter = ParticleCommitter(
            experiment_uuid, lcp_queue, crop_writer_queue, db_writer_queue
        )
        particle_commiter.start()

        processors = [
            frame_getter,
            frame_processor,
            frame_processor_orderer,
            crop_writer,
            *crop_processors,
            *classifiers,
            particle_commiter,
            db_writer,
        ]
        compressors = [compressor_raw, compressor_norm, compressor_mask, crop_writer]

        proc_buffers = [
            frame_queue,
            frame_properties_queue,
            frame_crops_queue,
            lcp_queue,
            db_writer_queue,
            crop_writer_queue,
            frame_processor_mask_queue,
        ]
        frame_buffers = [frame_bytes_norm, frame_bytes_mask]

        all_processors = processors + compressors
        all_buffers = proc_buffers + frame_buffers

        if verbose:
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

        if verbose:
            print("Waiting for all processes to complete.")
        [c.join() for c in all_processors]
        watchdog.stop()
        watchdog.join()

    finally:
        if verbose:
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
            time.sleep(10)

    def stop(self):
        self.stop_event.set()

    def stopped(self):
        return self.stop_event.is_set()


class VideoFrameGetter(multiprocessing.Process):

    def __init__(
        self,
        video_path,
        experiment_uuid,
        db_writer_queue,
        frame_queue,
        frame_bytes_norm,
    ):
        super(VideoFrameGetter, self).__init__()
        print("VideoFrameGetter: path " + video_path)
        self.verbose = False
        self.video_path = video_path
        self.experiment_uuid = experiment_uuid
        self.db_writer_queue = db_writer_queue
        self.frame_queue = frame_queue
        self.frame_bytes_norm = frame_bytes_norm
        self.stop_event = multiprocessing.Event()

    def run(self):
        # video = Video(self.video_path)
        if self.verbose:
            print("Hello, World!")
        # print("TESTING: FFMPEG options for video sample enabled!!")
        w, h = 2336, 1729
        # -ss 00:00:02.00 -t 00:00:00.50
        video_reader = FFmpeg(
            self.video_path, "", (1729, 2336, 1), " -vf scale={}:{}".format(w, h)
        )
        bg_modeler = BG(model="simpleMax", window_size=50, img_shape=(h, w, 1))
        fg_modeler = FG(passThrough=True)

        pipeline = EZ(video_reader, bg_modeler, fg_modeler).items()

        experiment_dir = os.path.join(config.experiment_dir, str(self.experiment_uuid))
        # io.imsave(os.path.join(experiment_dir, "bg.png"), video.extract_background().squeeze())

        magic_pixel = 255
        magic_pixel_delta = 0.1
        segment_number = -1
        i = -1
        for item in pipeline:
            i += 1
            if self.stopped():
                break
            else:
                if self.verbose:
                    print("Processing frame", i)

                # raw_frame = video.frame(i)
                # frame = video.normal_frame(i)
                # print("OLD raw frame stats: shape "+str(raw_frame.shape)+", min/max "+str(np.min(raw_frame))+"/"+str(np.max(raw_frame)))
                # print("OLD frame stats: shape "+str(frame.shape)+", min/max "+str(np.min(frame))+"/"+str(np.max(frame)))

                raw_frame = item["frame"] / 250.
                frame = item["fg"]
                # print("NEW raw frame stats: shape "+str(raw_frame.shape)+", min/max "+str(np.min(raw_frame))+"/"+str(np.max(raw_frame)))
                # print("NEW frame stats: shape "+str(frame.shape)+", min/max "+str(np.min(frame))+"/"+str(np.max(frame)))
                if config.use_magic_pixel_segmentation:
                    this_frame_magic_pixel = raw_frame[0, 4, 0]
                    if abs(this_frame_magic_pixel - magic_pixel) > magic_pixel_delta:
                        if self.verbose:
                            print("Segment Boundry Detected:", i)
                        segment_number += 1
                        segment = (uuid4(), self.experiment_uuid, segment_number)
                        self.db_writer_queue.put(
                            (
                                "execute",
                                """
                            INSERT INTO Segment (segment, experiment, number)
                            VALUES ($1, $2, $3)
                        """,
                                segment,
                            )
                        )
                    magic_pixel = this_frame_magic_pixel

                frame_uuid = uuid4()
                frame_insert = (frame_uuid, self.experiment_uuid, segment[0], i)

                self.db_writer_queue.put(
                    (
                        "execute",
                        """
                    INSERT INTO Frame (frame, experiment, segment, number)
                    VALUES ($1, $2, $3, $4)
                """,
                        frame_insert,
                    )
                )

                # frame = frame[:, crop_side:-crop_side]
                self.frame_bytes_norm.put(frame.tobytes())
                self.frame_queue.put((frame_uuid, i, frame))

        self.frame_bytes_norm.put(None)
        for g in range(config.GPUs):
            self.frame_queue.put(None)

        if self.verbose:
            print("VideoFrameGetter Exiting")

    def stop(self):
        self.stop_event.set()

    def stopped(self):
        return self.stop_event.is_set()


class VideoFrameProcessor(multiprocessing.Process):

    def __init__(self, frame_queue, frame_properties_queue, frame_processor_mask_queue):
        super(VideoFrameProcessor, self).__init__()
        self.verbose = False
        self.frame_queue = frame_queue
        self.frame_properties_queue = frame_properties_queue
        self.frame_processor_mask_queue = frame_processor_mask_queue
        self.stop_event = multiprocessing.Event()

    def gkern(self, l=1, sig=1):
        ax = np.arange(-l // 2 + 1., l // 2 + 1.)
        xx, yy = np.meshgrid(ax, ax)
        kernel = np.exp(-(xx ** 2 + yy ** 2) / (2. * sig ** 2))

        return kernel / np.sum(kernel)

    def viv_richardson_lucy(self, image, psf, iterations=1, clip=True):
        from scipy.signal import convolve

        image = image.astype("float64")

        im_deconv = 0.5 * np.ones(image.shape)
        psf_mirror = psf[::-1, ::-1]

        for _ in range(iterations):
            eps = np.finfo(image.dtype).eps
            x = convolve(im_deconv, psf, "same")
            np.place(x, x == 0, eps)
            relative_blur = image / x + eps
            im_deconv *= convolve(relative_blur, psf_mirror, "same")

        if clip:
            im_deconv[im_deconv > 1] = 255
            im_deconv[im_deconv < -1] = 0
        return im_deconv

    def run(self):

        # Method 1: new line
        #bg_psf1 = Image.open("/home/mot/py/bg.png").convert("L")

        while True:
            if self.stopped():
                break

            frame_data = self.frame_queue.get()
            if frame_data is None:
                break

            frame_uuid, i, frame = frame_data

            sframe = frame.squeeze()

            ############################################################################
            # Method 1: psf from bg
            """bg_psf1 = np.array(bg_psf1)
            x = 1485 #1485(C info lost) #407(D info lost) #change for diff psf 
            y = 952 #952(C info lost) #807(D info lost)
            h = 15
            w = 15
            bg_psf2 = bg_psf1[y:y+h, x:x+w]
            bg_psf2 = ~bg_psf2
            bg_psf2 = bg_psf2.squeeze() #fix to 1x1
            iters = 15
            
            deconv = self.viv_richardson_lucy(sframe, bg_psf2, iters, True)"""

            # Method 2: psf from gauss kernel
            kernel = self.gkern(7.0, 0.85)  # 1.0495833333333333
            iters = 15 #10 #15

            deconv = self.viv_richardson_lucy(sframe, kernel, iters, True)

            from scipy.misc import imsave

            try:
                if not os.path.exists("/home/mot/tmp/deconv"):
                    os.mkdir("/home/mot/tmp/deconv")  # make new dir
                imsave("/home/mot/tmp/deconv/deconv-" + str(i) + ".png", deconv)
                if not os.path.exists("/home/mot/tmp/sframe"):
                    os.mkdir("/home/mot/tmp/sframe")  # make new dir
                imsave("/home/mot/tmp/sframe/sframe-" + str(i) + ".png", sframe)

            except Exception as e:
                print(e)  # pass
            ############################################################################

            # thresh  = threshold(deconv) #sframe
            thresh = 130 #0.5
            binary = binary_opening((deconv < thresh), square(1))  # sframe
            cleared = clear_border(binary)
            labeled = label(cleared)
            # filtered = remove_small_objects(labeled, 64)
            filtered = labeled
            properties = regionprops(filtered, sframe)
            WIDTH_FILTER = 5
            # bbox: (min_row, min_col, max_row, max_col)
            # properties = [i for i in properties if i.bbox[3]-i.bbox[1] > WIDTH_FILTER]

            self.frame_processor_mask_queue.put((i, mask_frame.tobytes()))
            self.frame_properties_queue.put((frame_uuid, i, frame, properties))

        self.frame_processor_mask_queue.put(None)
        self.frame_properties_queue.put(None)
        if self.verbose:
            print("VideoFrameProcessor Exiting")

    def stop(self):
        self.stop_event.set()

    def stopped(self):
        return self.stop_event.is_set()


class FrameCropProcessor(multiprocessing.Process):

    def __init__(self, frame_properties_queue, frame_crops_queue):
        super(FrameCropProcessor, self).__init__()
        self.verbose = False
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

            properties = [p for p in properties if p.area > 100 and p.area < 2000]

            cropper = Crop(frame)

            coords = [(p.centroid[1], p.centroid[0]) for p in properties]
            bboxes = [
                ((p.bbox[1], p.bbox[0]), (p.bbox[3], p.bbox[2])) for p in properties
            ]
            crops = np.array(
                [cropper.crop(int(round(c[0])), int(round(c[1]))) for c in coords]
            )
            pcrops = []
            # pcrops = np.array([Classifier.preproc(None, crop) for crop in crops])

            self.frame_crops_queue.put(
                (frame_uuid, i, frame, crops, pcrops, properties, coords, bboxes)
            )

        self.frame_crops_queue.put(None)

        if self.verbose:
            print("FrameCropProcessor Exiting")

    def stop(self):
        self.stop_event.set()

    def stopped(self):
        return self.stop_event.is_set()


class Classy(multiprocessing.Process):

    def __init__(self, crop_queue, latents_categories_properties_queue):
        super(Classy, self).__init__()
        self.verbose = False
        self.crop_queue = crop_queue
        self.lcp_queue = latents_categories_properties_queue
        self.stop_event = multiprocessing.Event()

    def batch(self, iterable, n=1):
        # https://stackoverflow.com/a/8290508
        l = len(iterable)
        for ndx in range(0, l, n):
            yield iterable[ndx : min(ndx + n, l)]

    def run(self):
        if self.verbose:
            print("Classifier disabled, using this node as a pass-through")
        # classifier = Classifier().load()
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

            # for crop_batch in self.batch(pcrops, batchSize):

            # need to pad the array of crop images into a number divisible by the # of GPUs
            # crop_batch_padded = np.lib.pad(crop_batch, ((0, len(crop_batch) % config.GPUs), (0,0), (0,0), (0,0)), 'constant', constant_values=0)

            # l = classifier.encoder.predict(crop_batch_padded.reshape((len(crop_batch_padded), *(crop_batch_padded[0].shape))))
            # c = [np.argmax(c) for c in classifier.featureclassifier.predict(l.reshape(len(l), *(l[0].shape)))]

            # latents += list(l[0:len(crop_batch)])
            # categories += list(c[0:len(crop_batch)])

            self.lcp_queue.put(
                (frame_uuid, crops, latents, categories, properties, coords, bboxes)
            )

        self.lcp_queue.put(None)
        if self.verbose:
            print("Classy Exiting")

    def stop(self):
        self.stop_event.set()

    def stopped(self):
        return self.stop_event.is_set()


class ParticleCommitter(multiprocessing.Process):

    def __init__(self, experiment_uuid, lcp_queue, crop_writer_queue, db_writer_queue):
        super(ParticleCommitter, self).__init__()
        self.verbose = False
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

            DEFAULT_CATEGORY = 1  # set to unknown for now
            """
            Frame ID, 
            Particle ID, 
            Particle Area, 
            Particle Velocity, 
            Particle Intensity, 
            Particle Perimeter, 
            X Position, 
            Y Position, 
            Major Axis Length, 
            Minor Axis Length, 
            Orientation, 
            Solidity, 
            Eccentricity.
            """
            particles = [
                (
                    uuid4(),
                    self.experiment_uuid,
                    p.area,
                    p.mean_intensity,
                    p.perimeter,
                    p.major_axis_length,
                    p.minor_axis_length,
                    p.orientation,
                    p.solidity,
                    p.eccentricity,
                    DEFAULT_CATEGORY,
                )
                for i, p in enumerate(properties)
            ]

            track_uuids = [uuid4() for i in range(len(properties))]

            tracks = [
                (track_uuids[i], frame_uuid, particles[i][0], coords[i], bboxes[i])
                for i, p in enumerate(properties)
            ]

            self.db_writer_queue.put(
                (
                    "executemany",
                    """
                INSERT INTO Particle (particle, 
                                      experiment, 
                                      area, 
                                      intensity, 
                                      perimeter, 
                                      major,
                                      minor,
                                      orientation,
                                      solidity,
                                      eccentricity,
                                      category)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
                    (particles,),
                )
            )

            self.db_writer_queue.put(
                (
                    "executemany",
                    """
                INSERT INTO Track (track, frame, particle, location, bbox)
                VALUES ($1, $2, $3, $4, $5)
            """,
                    (tracks,),
                )
            )

            self.crop_writer_queue.put((frame_uuid, track_uuids, crops))

        self.db_writer_queue.put(None)
        self.crop_writer_queue.put(None)
        if self.verbose:
            print("ParticleCommitter Exiting")

    def stop(self):
        self.stop_event.set()

    def stopped(self):
        return self.stop_event.is_set()


class VideoFileCompressor(multiprocessing.Process):

    def __init__(
        self,
        video_fpath,
        experiment_dir,
        fname,
        width=2336,
        height=1729,
        fps=300.,
        rate=24.,
    ):
        super(VideoFileCompressor, self).__init__()
        self.verbose = False
        self.edir = experiment_dir
        self.fname = fname
        self.stop_event = multiprocessing.Event()
        self.cmd = "".join(
            (
                'ffmpeg -i "{}"'.format(video_fpath),
                " -c:v libx264 -crf 15 -preset fast",
                " -pix_fmt yuv420p",
                ' -filter:v "setpts={}*PTS'.format(fps / rate),
                ', crop={}:{}:0:0"'.format(width, height - 1) if height % 2 else '"',
                " -r 24",
                " -movflags +faststart",
                ' "{}"'.format(os.path.join(experiment_dir, fname)),
            )
        )

    def run(self):

        proc = subprocess.Popen(
            shlex.split(self.cmd),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        fcntl.fcntl(proc.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        with open(
            "{}.log".format(os.path.join(self.edir, self.fname)), "wb", 0
        ) as log_file:
            while proc.poll() is None:
                try:
                    log_file.write(proc.stdout.read())
                except:
                    time.sleep(0.25)

                time.sleep(0.25)
                if self.stopped():
                    proc.kill()
        if self.verbose:
            print("VideoFileCompressor Exiting")

    def stop(self):
        self.stop_event.set()

    def stopped(self):
        return self.stop_event.is_set()


class VideoStreamCompressor(multiprocessing.Process):

    def __init__(
        self,
        queue,
        experiment_dir,
        fname,
        width=2336,
        height=1729,
        fps=300.,
        rate=24.,
        pix_format="gray",
    ):
        super(VideoStreamCompressor, self).__init__()
        self.verbose = False
        self.queue = queue
        self.edir = experiment_dir
        self.fname = fname
        self.stop_event = multiprocessing.Event()
        self.cmd = "".join(
            (
                "ffmpeg",
                " -f rawvideo -pix_fmt {}".format(pix_format),
                " -video_size {}x{}".format(width, height),
                " -framerate {}".format(fps),
                " -i -",
                " -c:v libx264 -crf 15 -preset fast",
                " -pix_fmt yuv420p",
                ' -filter:v "setpts={}*PTS'.format(fps / rate),
                ', crop={}:{}:0:0"'.format(width, height - 1) if height % 2 else '"',
                " -r 24",
                " -movflags +faststart",
                ' "{}"'.format(os.path.join(experiment_dir, fname)),
            )
        )

    def run(self):
        proc = subprocess.Popen(
            shlex.split(self.cmd),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        fcntl.fcntl(proc.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        with open(
            "{}.log".format(os.path.join(self.edir, self.fname)), "wb", 0
        ) as log_file:
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
        if self.verbose:
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
        self.verbose = False
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
                        with warnings.catch_warnings():  # suppress warnings about low contrast images
                            warnings.simplefilter("ignore")
                            io.imsave(
                                os.path.join(frame_dir, str(track_uuids[i]) + ".jpg"),
                                crop.squeeze(),
                                quality=90,
                            )
        if self.verbose:
            print("CropWriter Exiting")

    def stop(self):
        self.stop_event.set()

    def stopped(self):
        return self.stop_event.is_set()


class DBWriter(multiprocessing.Process):

    def __init__(self, queue):
        super(DBWriter, self).__init__()
        self.verbose = False
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
        if self.verbose:
            print("DBWriter ready.")
        # print("DBWriter is a file-writing pass through!!!.")
        # with open("dbWriteFile.log","w") as f:
        while True:
            if not self.stopped():
                sql_drop = self.queue.get()
                if sql_drop is None:
                    self.commit()
                else:

                    method, query, args = sql_drop
                    # f.write(query)
                    # for a in args:
                    #     if isinstance(a, list):
                    #         f.write(str([str(i) for i in a]))
                    #     else:
                    #         f.write(str(a))

                    await getattr(tx, method)(query, *args)

            else:
                if self.commit_event.is_set():
                    if self.verbose:
                        print("Comitting changes to database.")
                    await transaction.commit()
                else:
                    if self.verbose:
                        print("Rolling back database.")
                    await transaction.rollback()
                break
        if self.verbose:
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
        self.verbose = False
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
        if self.verbose:
            print("OrderProcessor Exiting")

    def stop(self):
        self.stop_event.set()

    def stopped(self):
        return self.stop_event.is_set()
