
from skimage import io
from skimage.transform import downscale_local_mean
from skimage.filters import threshold_sauvola as threshold
from skimage.segmentation import clear_border, random_walker
from skimage.measure import label, regionprops
from skimage.morphology import binary_opening, square, remove_small_objects
from skimage.color import gray2rgb
from skimage.draw import circle

import config

from mpyx.F import EZ, As, By, F, Seq, Data

# from mpyx.F import Serial, Parallel, Broadcast, S, P, B
# from mpyx.F import Iter, Const, Print, Stamp, Map, Filter, Batch, Seq, Zip, Read, Write
# from mpyx.Vid import BG
from mpyx.Vid import FFmpeg

# from mpyx.Compress import VideoFile, VideoStream

from lib.Database import Database, DBWriter
from lib.Crop import Crop

from dateutil.parser import parse as dateparse
from base64 import b64encode
from itertools import repeat
import warnings

# from PIL import Image
from io import BytesIO
from uuid import uuid4

# import matplotlib.pyplot as plt
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

import warnings

# import matplotlib.pyplot as plt


class Datagram(Data):

    def getfname(self, key):
        return self.np_file_store[key]

    def update(self, key, fname):
        if not hasattr(self, "np_file_store"):
            # potential todo: https://stackoverflow.com/questions/394770/override-a-method-at-instance-level?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
            # rewrite this instance's save function to skip this check in the future.
            self.np_file_store = {}

        self.np_file_store[key] = fname

    def pop(self, key):
        self.np_file_store.pop(key)


async def main(args):
    print("Hello World!")
    if len(args) < 2:
        print("""path/to/video/file.avi 2017-10-31 Name-of_video "Notes. Notes." """)
    else:
        print(await detect_video(*args))


async def detect_video(video_file, date, name="", notes=""):

    cpus = multiprocessing.cpu_count()

    experiment_uuid = uuid4()
    experiment_day = dateparse(date)
    experiment_dir = os.path.join(config.experiment_dir, str(experiment_uuid))
    experiment = (experiment_uuid, experiment_day, name, "detection", notes)
    method = "TrackingPrefix DetectionMpyx"

    def e_handler(e, tb):
        print("Exception occured:", e)
        print(tb)

    try:

        # print("Creating data directory", experiment_dir)
        os.mkdir(experiment_dir)

        w, h = 2336, 1729

        # Reads the source video, outputs frames
        # -ss 00:00:02.00 -t 00:00:00.50
        video_reader = FFmpeg(
            video_file,
            "",
            (h, w, 1),
            " -ss 00:00:02.00 -t 00:00:00.50 -vf scale={}:{}".format(w, h),
            [],
            False,
            FrameData,
        )

        # csv_proc = CSVWriter(experiment_uuid, experiment_day, name, method, notes)
        # db_proc = DBProcessor(experiment_uuid, experiment_day, name, method, notes)

        # Computes a background for a frame, outputs {"frame": frame, "bg": bg}
        # bg_proc = BG(model="simpleMax", window_size=20, img_shape=(h, w, 1))

        # fines_proc = BG(
        #     model="rollingMax",
        #     window_size=20,
        #     img_shape=(h, w, 1),
        #     inputProp="div",
        #     saveAs="fines",
        # )

        # Utilities for viewing various stages of processing.
        raw_player = RawPlayer()
        bg_player = BGPlayer()
        fg_player = FGPlayer()
        mask_player = MaskPlayer()
        crop_player = CropPlayer()
        meta_player = MetaPlayer()

        # Number of processes to spawn for particular processors
        n_prop_procs = 5
        n_crop_procs = 2
        n_binary = 2
        n_crop_writer = 5
        n_csv_procs = 5
        n_deblur_procs = 10
        n_tracker = 5
        n_bg_proc = 5
        n_fines_proc = 1

        # Main pipeline
        EZ(
            video_reader,
            Counter(),
            Entry(experiment_uuid),
            MagicPixel(),
            Rescaler(scale=config.ms_rescale),
            # Counter("Rescaled"),
            BG(model="simpleMax", window_size=20, img_shape=(h, w, 1)),
            # Counter("BG"),
            FG(saveAs="div"),
            # Counter("FG1"),
            As(
                n_fines_proc,
                BG,
                model="rollingMax",
                window_size=20,
                img_shape=(h, w, 1),
                inputProp="div",
                saveAs="fines",
            ),
            # Counter("fines"),
            FG("finesDivision", saveAs="fg"),
            # Counter("FG2"),
            Seq(
                # As(n_deblur_procs, Deblur),
                As(n_binary, Binary, "legacyLabeled"),
                # Counter("Binary"),
                As(n_prop_procs, Properties),
                # Counter("props"),
                As(n_crop_procs, Crop_Processor),
                As(n_crop_writer, CropWriter, experiment_dir),
                # Counter("crops"),
            ),
            FrameCSVWriter(),
            # Counter("FrameCSVWriter"),
            FrameSegmentConverter(),
            # Counter("FrameSegmentConverter"),
            As(n_tracker, Tracker),
            # Counter("Tracker"),
            SegmentCSVWriter(),
            # Counter("segmentCSV"),
            DBProcessor(experiment_uuid, experiment_day, name, method, notes),
            # Counter("db"),
            Passthrough(),
            PerformanceMonitor(
                {
                    "Properties": n_prop_procs,
                    "Crop_Processor": n_crop_procs,
                    "Binary": n_binary,
                    "CropWriter": n_crop_writer,
                    "CSVWriter": n_csv_procs,
                    "Deblur": n_deblur_procs,
                    "BG": n_bg_proc,
                    "Tracker": n_tracker,
                }
            ),
            # Counter("performance"),
            Cleaner(),
            # qsize=150,
        ).catch(e_handler).start().join()

    except Exception as e:

        print("Uh oh. Something went wrong")

        traceback.print_exc()

        if os.path.exists(experiment_dir):
            print("Removing files from", experiment_dir)
            shutil.rmtree(experiment_dir)

    else:
        pass

    finally:
        pass
        # print("Fin.")

    return experiment_uuid


class FrameSegmentConverter(F):
    """
    Convert frame data into segment data
    Detection processes by frame
    Global tracking processes by segment
    """

    def setup(self):
        self.segment = None
        self.frames = 0
        self.frames_uuids = []

    def do(self, frame):
        # Detect new segment
        # Assumes ordering of input
        if self.segment is None:
            self.newSegment(frame)
        elif frame.segment_uuid != self.segment.segment_uuid:
            self.put(self.segment)
            self.newSegment(frame)

        self.insertFrame(frame)
        # Discard frames
        frame.clean()

    def teardown(self):
        # Todo: need to send last segment down the pipe?
        self.put(self.segment)

    def newSegment(self, frame):
        self.frames = 0
        self.segment = SegmentData()
        self.segment.experiment_uuid = frame.experiment_uuid
        self.segment.segment_uuid = frame.segment_uuid
        self.segment.segment_number = frame.segment_number

    def insertFrame(self, frame):
        # Preserve desired information
        keyname = "regionprops_{}"
        self.segment.update(keyname.format(self.frames), frame.getfname("regionprops"))
        frame.pop("regionprops")
        self.frames += 1
        self.segment.frames_uuids.append(frame.uuid)
        self.segment.frame_track_uuids.append(frame.track_uuids)
        self.segment.num_frames += 1


class ImageSampleWriter(F):

    def setup(self, experiment_dir, props=[]):
        self.sampleFreq = 100
        self.props = props
        self.count = 0
        self.experiment_dir = experiment_dir
        # self.path = "/home/mot/tmp/samples/" + experiment_uuid + "/"
        # os.makedirs(self.path)
        self.filename = "sample_{}_{}.png"

    def do(self, frame):
        self.count += 1
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if self.count % self.sampleFreq == 0:
                for k in self.props:
                    try:
                        im = frame.load(k)
                    except:
                        continue

                    if im.shape[-1] == 1:
                        im = im.squeeze()
                    if im.dtype == np.bool:
                        im = (im * 255).astype("uint8")

                    # print(k, im.shape, np.max(im))
                    fname = os.path.join(
                        self.experiment_dir, self.filename.format(k, self.count)
                    )
                    io.imsave(fname, im)
        self.put(frame)


class Deblur(F):

    def setup(self):
        self.kernel = self.gkern(7.0, 0.85)  # 1.0495833333333333
        self.iters = 10  # 10 #15

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
            # Todo: REVISIT
            im_deconv[im_deconv > 1.0] = 1
            im_deconv[im_deconv < -1.0] = 0

        return im_deconv

    def do(self, frame):

        """
        Load up the fg image
        """
        fg = frame.load("fg")

        """
        apply deblur
        """
        deconv = self.viv_richardson_lucy(fg.squeeze(), self.kernel, self.iters, True)
        frame.save("fg", deconv)

        self.put(frame)


class Cleaner(F):

    def do(self, frame):
        frame.clean()


class Filter(F):

    def initialize(self, properties):
        self.properties = properties

    def do(self, frame):
        for p in self.properties:
            frame.erase(p)
        self.put(frame)


# class RawPlayer(F):

#     def do(self, frame):
#         cv2.imshow("Raw Display", frame.load("raw"))
#         self.put(frame)
#         cv2.waitKey(1000 // 24)


# class FGPlayer(F):

#     def setup(self, win_name="FG Display"):
#         self.win_name = win_name

#     def do(self, frame):
#         cv2.imshow(self.win_name, frame.load("fg"))
#         self.put(frame)
#         cv2.waitKey(1000 // 24)


# class MaskPlayer(F):

#     def do(self, frame):
#         cv2.imshow("Mask Display", 1.0 * frame.load("mask"))
#         self.put(frame)
#         cv2.waitKey(1000 // 24)


# class BGPlayer(F):

#     def do(self, frame):
#         cv2.imshow("BG Display", frame.load("bg"))
#         self.put(frame)
#         cv2.waitKey(1000 // 24)


# class CropPlayer(F):

#     def do(self, frame):
#         crops = frame.load("crops")

#         crop_h = crops.shape[1]
#         crop_w = crops.shape[2]

#         crops_n = crops.shape[0]

#         disp_w_n = 30
#         disp_h_n = int(np.ceil(crops_n / disp_w_n))
#         disp_w = int(disp_w_n * crop_w)
#         disp_h = int(disp_h_n * crop_h)
#         disp = np.zeros((disp_h, disp_w))

#         # print("------------------")
#         # print("crops:", crops.shape)
#         # print("crop_h", crop_h)
#         # print("crop_w", crop_w)
#         # print("crops_n", crops_n)
#         # print("disp_w", disp_w)
#         # print("disp_h", disp_h)

#         for i in range(disp_h_n):
#             for j in range(disp_w_n):
#                 n = i * disp_h_n + j
#                 if n == crops_n:
#                     break
#                 disp[
#                     i * crop_h : i * crop_h + crop_h, j * crop_w : j * crop_w + crop_w
#                 ] = crops[n].squeeze()

#         cv2.imshow("Crop Display", disp)
#         self.put(frame)
#         cv2.waitKey(1000 // 24)


class MockPerformanceInfo(F):

    def setup(self):
        self.count = 0

    def do(self, frame):
        m, c, n = self.get_stats(self.count / 10.0)
        self.meta["timings"] = {"Memory": m, "CPU": c, "Bandwidth": n}
        self.count += 1
        self.put(frame)

    def get_memory(self, t):
        "Simulate a function that returns system memory"
        return 100 * (0.5 + 0.5 * np.sin(0.5 * np.pi * t))

    def get_cpu(self, t):
        "Simulate a function that returns cpu usage"
        return 100 * (0.5 + 0.5 * np.sin(0.2 * np.pi * (t - 0.25)))

    def get_net(self, t):
        "Simulate a function that returns network bandwidth"
        return 100 * (0.5 + 0.5 * np.sin(0.7 * np.pi * (t - 0.1)))

    def get_stats(self, t):
        return self.get_memory(t), self.get_cpu(t), self.get_net(t)


class Passthrough(F):

    def setup(self):
        self.start = time.time()

    def do(self, frame):
        # print("PASSTHROUGH DO")
        self.meta["timings"]["Time per item"] = time.time() - self.start
        self.start = time.time()
        self.put(frame)


import matplotlib.pyplot as plt
import numpy as np
import re


class PerformanceMonitor(F):

    def setup(self, parallelisms={}, visualize=True, log=False, verbose=False):
        self.visualize = visualize
        self.log = log
        self.fig = None
        self.ax = None
        self._visBars = None
        self.parallelisms = parallelisms
        self.verbose = verbose
        self.total_times = {}

    def do(self, frame):
        # print("PERFORMANCE DO")
        # print("Meta", self.meta["timings"])
        self.timings = []
        self.labels = []

        for k, v in self.meta["timings"].items():
            # Processes are labelled eg. "MyProc-6"
            label = re.split("-\d+", k)[0]
            self.labels.append(label)
            if not label in self.total_times:
                self.total_times[label] = 0.0
            self.total_times[label] += v
            if label in self.parallelisms:
                timing = v / self.parallelisms[label]
            else:
                timing = v
            self.timings.append(timing)

        if self.verbose:
            # Todo: does this work?
            print("Completed frame", frame.number)
        if self.visualize:
            self._visualize()
        self.put(frame)

    def teardown(self):
        print("PerformanceMonitor Total / Node Total Times")
        for label, total_time in self.total_times.items():
            if label in self.parallelisms:
                avg_time = total_time / self.parallelisms[label]
                print(" `-> {} {:.2f} s / {:.2f} s".format(label, total_time, avg_time))
            else:
                print(" `-> {} {:.2f} s".format(label, total_time))

    def _visualize(self):

        if self.fig is None:
            self.fig, self.ax = plt.subplots()
            plt.show(block=False)
            ind = np.arange(1, len(self.labels) + 1)

            bars = plt.bar(ind, self.timings)
            self._visBars = {}
            for i in range(len(self.labels)):
                self._visBars[self.labels[i]] = bars[i]

            self.ax.set_title("Node Processing Time")
            self.ax.set_ylabel("Seconds")
            self.ax.set_xticks(ind)
            self.ax.set_xticklabels(self.labels)
            self.ax.tick_params("x", labelrotation=45)
        else:
            for i in range(len(self.labels)):
                bar = self._visBars[self.labels[i]]
                bar.set_height(self.timings[i])
            # ask the canvas to re-draw itself the next time it
            # has a chance.
            # For most of the GUI backends this adds an event to the queue
            # of the GUI frameworks event loop.
            self.fig.canvas.draw_idle()
            self.ax.set_xticklabels(self.labels)
            try:
                # make sure that the GUI framework has a chance to run its event loop
                # and clear any GUI events.  This needs to be in a try/except block
                # because the default implementation of this method is to raise
                # NotImplementedError
                self.fig.canvas.flush_events()
            except NotImplementedError:
                pass

    def _log(self):
        pass


class MetaPlayer(F):
    """
    Print data related to the frame at current node.
    """

    def setup(self,):
        self.last_segment = None

    def do(self, frame):
        print(" Number:", frame.number)
        self.put(frame)


class Counter(F):
    """
    Count the number of items that passed through this node.
    """

    def setup(self, name="Dracula"):
        self.name = name
        self.count = 0

    def do(self, frame):
        self.count += 1
        self.put(frame)

    def teardown(self):
        print("Counter {} counted {}".format(self.name, self.count))


class Entry(F):
    """
    The first node after frame emitter.
    We use this node to stamp the frames with some meta data
    and convert the uint8 [0,255] frame to float64 [0,1]
    """

    def initialize(self, experiment_uuid):
        self.experiment_uuid = experiment_uuid
        self.count = 0

    def do(self, frame):
        frame.experiment_uuid = self.experiment_uuid
        frame.number = self.count
        frame.uuid = uuid4()
        self.count += 1
        frame.save("raw", frame.load("raw") / 255)
        # print("Frame", self.count, "entering...")
        self.put(frame)


class MagicPixel(F):
    """
    Detect segment boundaries using the Megaspeed camera
    pixel encoded information. The first row contains no image information, but
    does contain metadata.
    We use this meta data to detect when a "burst" starts/stops.
    """

    def setup(self):
        self.segment_number = 0
        self.magic_pixel = None
        self.segment_uuid = None

    def do(self, frame):
        magic_pixel_delta = 0.1
        raw = frame.load("raw")

        if config.use_magic_pixel_segmentation:
            this_frame_magic_pixel = raw[0, 4, 0]
            if (
                self.magic_pixel is None
                or abs(this_frame_magic_pixel - self.magic_pixel) > magic_pixel_delta
            ):
                # print("Segment Boundry Detected")
                self.segment_uuid = uuid4()
                self.segment_number += 1

            self.magic_pixel = this_frame_magic_pixel
        frame.segment_uuid = self.segment_uuid
        frame.segment_number = self.segment_number
        self.put(frame)


from skimage.transform import rescale


class Rescaler(F):
    """
    Rescale the frame by the desired scale factor.
    Currently rescales the "raw" frame.
    """

    def setup(self, scale):
        self.scale = scale

    def do(self, frame):
        # the following error from skimage rescale on the frame.load return
        # - ValueError: buffer source array is read-only
        # frame.save("raw", rescale(frame.load("raw"), self.scale))
        if self.scale != 1:
            frame.save("raw", rescale(np.copy(frame.load("raw")), self.scale))

        self.put(frame)


import math
from collections import deque


class BG(F):
    """
    Compute a background.
    """

    def setup(
        self,
        model="median",
        window_size=50,
        inputProp="raw",
        saveAs="bg",
        *args,
        env=None,
        **kwArgs
    ):
        self.frame_que = deque()
        self.window_size = window_size
        # self.q_len = math.ceil(window_size / 2)
        # self.q_count = 0
        self.saveAs = saveAs
        self.inputProp = inputProp
        self.model = getattr(self, model)(window_size=window_size, *args, **kwArgs)

    def do(self, frame):
        # import cv2
        # from uuid import uuid4
        self.frame_que.append(frame)
        # self.q_count += 1
        self.bg = self.model.process(frame.load(self.inputProp))
        # cv2.imwrite('/home/mot/tmp/bg_'+str(uuid4())+'.png', self.bg)

        if len(self.frame_que) > self.window_size:
            # bg = self.que.popleft()
            frame = self.frame_que.popleft()
            frame.save(self.saveAs, self.bg)
            self.put(frame)

    def teardown(self):
        while len(self.frame_que) > 0:
            # self.q_count -= 1
            frame = self.frame_que.popleft()
            frame.save(self.saveAs, self.bg)
            self.put(frame)

    class simpleMax:
        """
        Computes the max over the first window_size frames.
        Good for approximating the lighting in a backlit scene.
        """

        def __init__(self, window_size=20, img_shape=None):

            # print("simpleMax maxlen: "+str(math.ceil(window_size / 2)-5))
            self.window_size = window_size
            self.que = deque()
            self.bg = None

        def process(self, frame):
            from skimage.morphology import erosion

            # parameter: minimum lighting (dynamic range), threshold below
            min_range = 20 / 255.0

            if len(self.que) < self.window_size:
                self.que.append(frame)
            elif len(self.que) == self.window_size:
                # print("computing bg...")
                if self.bg is None:
                    bg = np.max(self.que, axis=0)
                    bg[bg < min_range] = 0
                    bg = bg.squeeze()
                    # bg = erosion(bg, square(8))
                    bg = np.expand_dims(bg, axis=-1)
                    self.bg = bg
            return self.bg

    class rollingMax:
        """
        Computes the max over the first window_size frames.
        Good for approximating the lighting in a backlit scene.
        """

        def __init__(self, window_size=20, img_shape=None):

            # print("simpleMax maxlen: "+str(math.ceil(window_size / 2)-5))
            self.window_size = window_size
            self.que = deque(maxlen=window_size)
            self.bg = None

        def process(self, frame):
            from skimage.morphology import erosion

            # parameter: minimum lighting (dynamic range), threshold below
            min_range = 20 / 255.0

            self.que.append(frame)
            if len(self.que) == self.window_size:
                # print("computing bg...")
                bg = np.max(self.que, axis=0)
                bg[bg < min_range] = 0
                bg = bg.squeeze()
                # bg = erosion(bg, square(8))
                bg = np.expand_dims(bg, axis=-1)
                self.bg = bg
            return self.bg


class FG(F):
    """
    Process the image to yield the scene foreground.
    """

    def setup(self, model="bgDivision", saveAs="fg", *args, **kwargs):
        # If your process needs to do any kind of setup once it has been forked,
        # or if it the first process in a workflow and expected to generate
        # values for the rest of the pipeline, that code should go here.
        self.saveAs = saveAs
        self.model = getattr(self, model)()

    def do(self, frame):
        # The main workhorse of a process. Items will flow in here, potentially
        # be modified, mapped, reduced, or otherwise morgified, and output can
        # be then pushed downstream using the self.put() method.
        # Here, for example, any items are simply passed along.
        frame.save(self.saveAs, self.model.process(frame))

        self.put(frame)

    class bgDivision:
        """
        In a backlit scene that roughly obeys Beer-Lambert laws, dividing the
        raw image by the background (backlit scene lighting) yields the 
        transmittance, which for our application is useful.
        """

        def __init__(self):
            pass

        def process(self, frame):
            eps = 0.0001
            raw = frame.load("raw")
            bg = frame.load("bg")
            div = raw / (bg + eps)
            # div[np.isnan(div)] = 1.0  # get rid of nan's from 0/0
            return np.clip(div, 0, 1)

    class finesDivision:
        """
        In a backlit scene that roughly obeys Beer-Lambert laws, dividing the
        raw image by the background (backlit scene lighting) yields the 
        transmittance, which for our application is useful.
        """

        def __init__(self):
            pass

        def process(self, frame):
            eps = 0.0001
            fg = frame.load("div")
            fines = frame.load("fines")
            div = fg / (fines + eps)
            # div[np.isnan(div)] = 1.0  # get rid of nan's from 0/0
            return np.clip(div, 0, 1)


from skimage.filters import threshold_sauvola
from skimage.morphology import (
    binary_opening,
    binary_erosion,
    remove_small_objects,
    square,
    disk,
    erosion,
)
from skimage.segmentation import clear_border


class Binary(F):
    """
    Performs thresholding on the foreground image.
    """

    def setup(self, model="simple", *args, **kwargs):
        # If your process needs to do any kind of setup once it has been forked,
        # or if it the first process in a workflow and expected to generate
        # values for the rest of the pipeline, that code should go here.
        self.model = getattr(self, model)(*args, **kwargs)

    def do(self, frame):
        # print("BINARY DO")
        # The main workhorse of a process. Items will flow in here, potentially
        # be modified, mapped, reduced, or otherwise morgified, and output can
        # be then pushed downstream using the self.put() method.
        # Here, for example, any items are simply passed along.
        frame.save("mask", self.model.process(frame))
        self.put(frame)

    class legacyLabeled:

        def __init__(self, threshold=0.4):
            self.threshold = threshold

        def process(self, frame):

            # Take the center, removing edge artifacts
            # frame = frame[200:-200, 200:-200]
            sframe = frame.load("fg").squeeze()
            binary = sframe < self.threshold
            # binary = binary_erosion(binary, disk(6))
            binary = clear_border(binary)

            config_small_object_diameter = 100  # microns diameter
            # Area of equivalent circle
            small_threshold = (
                np.pi
                * (
                    (config_small_object_diameter / 2)
                    / config.ms_metric_cal
                    * config.ms_rescale
                )
                ** 2
            )

            binary = remove_small_objects(binary, small_threshold)
            # opened = binary_opening(binary, square(3))
            # cleared = clear_border(opened)
            return binary


from skimage.measure import label, regionprops


class Properties(F):

    def setup(self, filter_area=False, filter_area_low=100, filter_area_high=2000):
        pass

    def do(self, frame):
        # print("PROPS DO")
        labelled = label(frame.load("mask"))
        properties = regionprops(labelled, frame.load("fg").squeeze())
        frame.save("regionprops", properties)
        frame.track_uuids = [uuid4() for i in range(len(properties))]
        self.put(frame)


from lib.Crop import Crop


class Crop_Processor(F):

    def do(self, frame):
        regionprops = frame.load("regionprops")
        cropper = Crop(frame.load("fg"))

        coords = [(p.centroid[1], p.centroid[0]) for p in regionprops]
        bboxes = [((p.bbox[1], p.bbox[0]), (p.bbox[3], p.bbox[2])) for p in regionprops]
        crops = np.array(
            [cropper.crop(int(round(c[0])), int(round(c[1]))) for c in coords]
        )
        frame.save("crops", crops)
        self.put(frame)


class CropWriter(F):

    def initialize(self, experiment_dir):
        self.experiment_dir = experiment_dir

    def do(self, frame):
        crops = frame.load("crops")
        track_uuids = frame.track_uuids
        frame_uuid = str(frame.uuid)
        frame_dir = os.path.join(self.experiment_dir, frame_uuid)

        os.makedirs(frame_dir, exist_ok=True)

        for i, crop in enumerate(crops):
            with warnings.catch_warnings():  # suppress warnings about low contrast images
                warnings.simplefilter("ignore")
                # print(crop.shape, np.min(crop), np.mean(crop), np.max(crop), crop.dtype)
                crop2 = (crop.squeeze() * 255).astype(np.uint8)
                # print(
                #     crop2.shape,
                #     np.min(crop2),
                #     np.mean(crop2),
                #     np.max(crop2),
                #     crop2.dtype,
                # )
                io.imsave(
                    os.path.join(frame_dir, str(track_uuids[i]) + ".jpg"),
                    (crop.squeeze() * 255).astype(np.uint8),
                    quality=90,
                )
        self.put(frame)


class FrameData(Datagram):

    def __init__(self):
        self.experiment_uuid = None
        self.segment_uuid = None
        self.segment_number = None
        self.uuid = None
        self.number = None
        # self.metric_cal = metric_cal
        # self.scale = scale
        self.track_uuids = None


class SegmentData(Datagram):

    def __init__(self):
        # Todo: realize this
        self.experiment_uuid = None
        self.segment_uuid = None
        self.segment_number = None
        self.num_frames = 0

        self.frames_uuids = []
        self.frame_track_uuids = []


class FrameCSVWriter(F):

    def initialize(self, verbose=False):
        self.verbose = verbose
        if self.verbose:
            print("Launching CSV processor")

        self.csv_files = [
            "/tmp/{}_segment.csv",
            "/tmp/{}_frame.csv",
            "/tmp/{}_track.csv",
            "/tmp/{}_particle.csv",
        ]

        self.prev_segment_uuid = None

    def do(self, frame):

        # Add frame
        self.add_frame(frame)
        # Add segment
        if config.use_magic_pixel_segmentation:
            if frame.segment_uuid != self.prev_segment_uuid:
                self.prev_segment_uuid = frame.segment_uuid
                self.add_segment(frame)

        self.put(frame)

    def add_segment(self, frame):
        data = (frame.segment_uuid, frame.experiment_uuid, frame.segment_number)
        s = "{}\t{}\t{}\n"
        with open("/tmp/{}_segment.csv".format(frame.experiment_uuid), "a") as f:
            f.write(s.format(data[0], data[1], data[2]))

    def add_frame(self, frame):
        if config.use_magic_pixel_segmentation:
            data = (frame.uuid, frame.experiment_uuid, frame.segment_uuid, frame.number)
            s = "{}\t{}\t{}\t{}\n"
            with open("/tmp/{}_frame.csv".format(frame.experiment_uuid), "a") as f:
                f.write(s.format(data[0], data[1], data[2], data[3]))
        else:
            data = (frame.uuid, frame.experiment_uuid, frame.number)
            s = "{}\t{}\t{}\n"
            with open("/tmp/{}_frame.csv".format(frame.experiment_uuid), "a") as f:
                f.write(s.format(data[0], data[1], data[2]))

    def add_detections(self, frame):
        regionprops = frame.load("regionprops")
        metric_cal = config.ms_metric_cal
        scale = config.ms_rescale
        DEFAULT_CATEGORY = 0  # set to unknown for now

        equivCircleRadius = lambda area: np.sqrt(area / np.pi)

        radius_function = lambda x: cal * equivCircleRadius(x) * metric_cal / scale
        linear_function = lambda x: cal * x * metric_cal / scale
        area_function = lambda x: cal ** 2 * x * metric_cal ** 2 / scale ** 2

        particles = [
            (
                uuid4(),
                self.experiment_uuid,
                area_function(p.filled_area),
                radius_function(p.filled_area),
                p.mean_intensity,
                linear_function(p.perimeter),
                linear_function(p.major_axis_length),
                linear_function(p.minor_axis_length),
                p.orientation,
                p.solidity,
                p.eccentricity,
                DEFAULT_CATEGORY,
            )
            for i, p in enumerate(regionprops)
        ]

        coords = [(p.centroid[1], p.centroid[0]) for p in regionprops]
        bboxes = [((p.bbox[1], p.bbox[0]), (p.bbox[3], p.bbox[2])) for p in regionprops]

        track_uuids = frame.track_uuids

        tracks = [
            (track_uuids[i], frame.uuid, particles[i][0], coords[i], bboxes[i])
            for i, p in enumerate(regionprops)
        ]
        s = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n"
        with open("/tmp/{}_particle.csv".format(self.experiment_uuid), "a") as f:
            for p in particles:
                f.write(
                    s.format(
                        p[0],
                        p[1],
                        p[2],
                        p[3],
                        p[4],
                        p[5],
                        p[6],
                        p[7],
                        p[8],
                        p[9],
                        p[10],
                        p[11],
                    )
                )

        s = "{}\t{}\t{}\t{}\t{}\n"
        with open("/tmp/{}_track.csv".format(self.experiment_uuid), "a") as f:
            for t in tracks:
                f.write(s.format(t[0], t[1], t[2], t[3], t[4]))


class DBProcessor(F):

    def initialize(
        self, experiment_uuid, experiment_day, name, method, notes, verbose=False
    ):
        self.verbose = verbose
        if self.verbose:
            print("Launching DB processor")
        self.experiment_uuid = experiment_uuid
        self.experiment_day = experiment_day
        self.exp_name = name
        self.method = method
        self.notes = notes

        self.csv_files = [
            "/tmp/{}_segment.csv",
            "/tmp/{}_frame.csv",
            "/tmp/{}_track.csv",
            "/tmp/{}_particle.csv",
        ]

    def do(self, frame):
        self.put(frame)

    async def copy_to_database(self):
        if self.verbose:
            print("Copying to database.")
        await self.tx.execute(
            """
            INSERT INTO Experiment (experiment, day, name, method, notes)
            VALUES ($1, $2, $3, $4, $5)
            """,
            self.experiment_uuid,
            self.experiment_day,
            self.exp_name,
            self.method,
            self.notes,
        )

        if config.use_magic_pixel_segmentation:
            if self.verbose:
                print("Inserting segments into database.")
            await self.tx.execute(
                """
                COPY segment FROM '/tmp/{}_segment.csv' DELIMITER '\t' CSV;
                """.format(
                    self.experiment_uuid
                )
            )

        if config.use_magic_pixel_segmentation:
            if self.verbose:
                print("Inserting frames into database.")
            await self.tx.execute(
                """
                COPY frame FROM '/tmp/{}_frame.csv' DELIMITER '\t' CSV;
                """.format(
                    self.experiment_uuid
                )
            )
        else:
            if self.verbose:
                print("Inserting frames into database.")
            await self.tx.execute(
                """
                COPY frame (frame, experiment, number) FROM '/tmp/{}_frame.csv' DELIMITER '\t' CSV;
                """.format(
                    self.experiment_uuid
                )
            )

        if self.verbose:
            print("Inserting particles into database.")
        await self.tx.execute(
            """
            COPY particle (particle, experiment, area, radius, intensity, perimeter, major, minor, orientation, solidity, eccentricity, category\n)FROM '/tmp/{}_particle.csv' DELIMITER '\t' CSV;
            """.format(
                self.experiment_uuid
            )
        )
        if self.verbose:
            print("Inserting tracks into database.")
        await self.tx.execute(
            """
            COPY track (track, frame, particle, location, bbox\n) FROM '/tmp/{}_track.csv' DELIMITER '\t' CSV;
            """.format(
                self.experiment_uuid
            )
        )

    def teardown(self):
        start = time.time()
        self.tx, self.transaction = self.async(Database().transaction())
        try:
            self.async(self.copy_to_database())
        except Exception as e:
            print(e)
            print("rolling back database")
            self.async(self.transaction.rollback())
        else:
            self.async(self.transaction.commit())
        self.cleanupFS()

    def cleanupFS(self):
        for f in self.csv_files:
            if os.path.isfile(f.format(self.experiment_uuid)):
                os.remove(f.format(self.experiment_uuid))


"""
A network flow multiple object tracker

    Zhang et al. 2008 Section 3
    This formulation can be mapped into a cost-flow network
    G(X ) with source s and sink t. Given an observation set
    X : for every observation xi ∈ X , create two nodes ui, vi,
    create an arc (ui, vi) with cost c(ui, vi) = Ci and flow
    f(ui, vi) = fi, an arc (s, ui) with cost c(s, ui) = Cen,i
    and flow f(s, ui) = fen,i, and an arc (vi, t) with cost
    c(vi, t) = Cex,i and flow f(vi, t) = fex,i. For every transition
    Plink(xj |xi) = 0, create an arc (vi, uj ) with cost
    c(vi, uj ) = Ci,j and flow f(vi, uj ) = fi,j . An example
    of such a graph is shown in Figure 2. Eqn.10 is equivalent
    to the flow conservation constraint and Eqn.11 to the cost
    of flow in G. Finding optimal association hypothesis T ∗ is
    equivalent to sending the flow from source s to sink t that
    minimizes the cost.
    
    Cen = -log(Pentr(xi))
    Cex = -log(Pexit(xi))
    Cij = -Log(Plink(xi|xj))
    Ci = log(Bi/(1-Bi)
    
    Bi := miss detection rate of detector
    Pentr = Pexit 
          = #traj / #hyp
    Plink = Psize*Pposiiton*Pappearance*Ptime
    
    

Cost Strategies:
- Try dot product on the encoded state (Nilanjan)
   - allows for computation of all forward passes before graph time
- Aggregate all the node pairs with edges between them,
  then forward pass, the set cost
- Use engineered cost
- Use engineered + network cost
   
"""

import config


from lib.Database import Database

import numpy as np

import os
from os.path import isdir, isfile, join
import shutil
import traceback
import multiprocessing
import subprocess
import threading
import concurrent.futures
import tempfile
import queue
import asyncio
from scipy.optimize import golden

from skimage import io
import time

import pyMCFSimplex


class Tracker(F):

    def setup(self):
        self.verbose = False
        self.tracks = None

    def buildGraph(self, segment):
        from sklearn.neighbors import KDTree

        Ci = -200
        Cen = 150
        Cex = 150

        self.mcf_graph = MCF_GRAPH_HELPER()
        self.mcf_graph.add_node("START")
        self.mcf_graph.add_node("END")

        # TODO: FIND NEAREST NEIGHBOUR FOR LOCAL CONNECTIVITY
        # O(N), where N is the number of detections in segment
        for i in range(len(self.regionprops)):
            keyname = "regionprops_{}".format(i)
            r = self.regionprops[i]
            coords = [(p.centroid[1], p.centroid[0]) for p in r]

            for j, p in enumerate(r):
                u = "u_" + str(i) + "_" + str(j)
                v = "v_" + str(i) + "_" + str(j)
                self.mcf_graph.add_node(u)
                self.mcf_graph.add_node(v)

                self.mcf_graph.add_edge(u, v, capacity=1, weight=int(Ci))
                self.mcf_graph.add_edge("START", u, capacity=1, weight=Cen)
                self.mcf_graph.add_edge(v, "END", capacity=1, weight=Cex)

        # O(M*(N*LogN + LogN)), where M is number of frames and N 
        # is the number of detections in a frame
        for i in range(segment.num_frames - 1):
            r1 = self.regionprops[i]
            coords1 = [(p.centroid[1], p.centroid[0]) for p in r1]

            r2 = self.regionprops[i + 1]
            coords2 = [(p.centroid[1], p.centroid[0]) for p in r2]

            neighbors = 5
            if len(coords1) <= neighbors:
                indices = [
                    [i for i in range(len(coords2))] for i in range(len(coords1))
                ]
            else:
                tree = KDTree(coords2, leaf_size=2)
                distances, indices = tree.query(coords1, k=neighbors)

            for j, ind in enumerate(indices):
                for k in ind:

                    v = "v_" + str(i) + "_" + str(j)
                    u = "u_" + str(i + 1) + "_" + str(k)

                    Cij = 10 * int(self.euclidD(coords1[j], coords2[k]))

                    self.mcf_graph.add_edge(v, u, weight=Cij, capacity=1)

    def euclidD(self, point1, point2):
        """
        Computes the euclidean distance between two points and 
        returns this distance.
        """
        sum = 0
        for index in range(len(point1)):
            diff = (point1[index] - point2[index]) ** 2
            sum = sum + diff

        return np.sqrt(sum)

    def solve(self,):
        self.tracks = dict()

        if not self.mcf_graph.num_nodes():  # only START and END nodes present (empty)
            if self.verbose:
                print("Nothing in segment")
            return

        # if self.verbose:
        # print("cost", np.min(self.costs), np.mean(self.costs), np.max(self.costs))

        if self.verbose:
            print("Solving min-cost-flow for segment")
        # print("Solving", self.mcf_graph.n_nodes, "detections")
        demand = goldenSectionSearch(
            self.mcf_graph.solve,
            0,
            self.mcf_graph.n_nodes // 4,
            self.mcf_graph.n_nodes // 2,
            10,
            memo=None,
        )

        if self.verbose:
            print("Optimal number of tracks", demand)

        if demand:
            min_cost = self.mcf_graph.solve(demand)
            mcf_flow_dict = self.mcf_graph.flowdict()
            for dest in mcf_flow_dict["START"]:
                new_particle_uuid = uuid4()
                track = []
                curr = dest
                while curr != "END":
                    if curr[0] == "u":
                        # Everything after prefix u_
                        old_particle_id = curr[2:]
                        track.append(old_particle_id)
                    curr = mcf_flow_dict[curr][0]

                self.tracks[new_particle_uuid] = track
        else:
            min_cost = float("+inf")

        self.mcf_graph = None

        if self.verbose:
            print("Min cost", min_cost)

    def computeAverages(self, segment):
        """
        Headers for Syncrude 2018
        
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
        DEFAULT_CATEGORY = 0  # set to unknown for now
        equivCircleRadius = lambda area: np.sqrt(area / np.pi)
        start = time.time()
        self.particle_inserts = []
        self.track_inserts = []

        coords = [[(p.centroid[1], p.centroid[0]) for p in r] for r in self.regionprops]
        bboxes = [
            [((p.bbox[1], p.bbox[0]), (p.bbox[3], p.bbox[2])) for p in r]
            for r in self.regionprops
        ]

        for new_particle_uuid, track in self.tracks.items():
            mean_area = 0.0
            mean_intensity = 0.0
            mean_perimeter = 0.0
            mean_radius = 0.0
            mean_major = 0.0
            mean_minor = 0.0
            mean_orientation = 0.0
            mean_solidity = 0.0
            mean_eccentricity = 0.0
            category = []

            for t in track:
                i, j = int(t.split("_")[0]), int(t.split("_")[1])
                p = self.regionprops[i][j]

                mean_area += p.filled_area / len(track)
                mean_intensity += p.mean_intensity / len(track)
                mean_perimeter += p.perimeter / len(track)
                mean_radius += equivCircleRadius(p.filled_area) / len(track)
                mean_major += p.major_axis_length / len(track)
                mean_minor += p.minor_axis_length / len(track)
                mean_orientation += p.orientation / len(track)
                mean_solidity += p.solidity / len(track)
                mean_eccentricity += p.eccentricity / len(track)
                category.append(DEFAULT_CATEGORY)

                loc = coords[i][j]
                bbox = bboxes[i][j]
                new_track_uuid = segment.frame_track_uuids[i][j]
                new_frame_uuid = segment.frames_uuids[i]
                self.track_inserts.append(
                    (new_track_uuid, new_frame_uuid, new_particle_uuid, loc, bbox)
                )

            category = np.argmax(np.bincount(category))

            self.particle_inserts.append(
                (
                    new_particle_uuid,
                    segment.experiment_uuid,
                    mean_area,
                    mean_radius,
                    mean_intensity,
                    mean_perimeter,
                    mean_major,
                    mean_minor,
                    mean_orientation,
                    mean_solidity,
                    mean_eccentricity,
                    category,
                )
            )

    def do(self, segment):
        start = time.time()
        
        
        self.regionprops = []
        for i in range(segment.num_frames):
            keyname = "regionprops_{}".format(i)
            self.regionprops.append(segment.load(keyname))
        print("Getting rp", time.time()-start)
        start = time.time()
        self.buildGraph(segment)
        print("Building graph", time.time()-start)
        start = time.time()
        self.solve()
        print("solving", time.time()-start)
        start = time.time()
        if self.verbose:
            print("Tracks reconstructed", len(self.tracks))

    
        self.computeAverages(segment)
        print("Averages", time.time()-start)
        segment.save("particles", self.particle_inserts)
        segment.save("tracks", self.track_inserts)

        self.put(segment)

    def teardown(self,):
        pass


class SegmentCSVWriter(F):

    def initialize(self):
        self.verbose = True
        if self.verbose:
            print("Launching CSV processor")

        self.csv_files = ["/tmp/{}_track.csv", "/tmp/{}_particle.csv"]

    def do(self, segment):
        # Add detections
        self.add_segment_data(segment)
        self.put(segment)

    def add_segment_data(self, segment):
        cal = config.ms_metric_cal
        scale = config.ms_rescale

        linear_function = lambda x: x * cal / scale
        square_function = lambda x: x * cal ** 2 / scale ** 2

        particles = list(segment.load("particles"))
        tracks = segment.load("tracks")

        s = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n"
        with open("/tmp/{}_particle.csv".format(segment.experiment_uuid), "a") as f:
            for p in particles:
                f.write(
                    s.format(
                        p[0],
                        p[1],
                        square_function(p[2]),
                        linear_function(p[3]),
                        p[4],
                        linear_function(p[5]),
                        linear_function(p[6]),
                        linear_function(p[7]),
                        p[8],
                        p[9],
                        p[10],
                        p[11],
                    )
                )

        s = "{}\t{}\t{}\t{}\t{}\n"
        with open("/tmp/{}_track.csv".format(segment.experiment_uuid), "a") as f:
            for t in tracks:
                f.write(s.format(t[0], t[1], t[2], t[3], t[4]))


class MCF_GRAPH_HELPER:
    """
    Add nodes with UUID substrings to this helper,
    will manage the mapping between nodes and an integer
    name.
    
    Simplified for our purposes, the graph will always have a
    super-source/super-sink 'START'/'END', 
    and will be assigned demand and -demand respectively.
    
    Simplified for our purposes, the capacity will always have
    a lower bound zero, and can not be set explicitly.
    """

    def __init__(self, verbose=False):
        self.nodes = dict()
        self.edges = []
        self.n_nodes = 0
        self.n_edges = 0
        self.demand = 0
        self.verbose = verbose

    def add_node(self, k):
        """
        expects uuid
        pyMCFSimplex node names {1,2,...,n}
        returns true if the node was added, false
        if the node was added prior.
        """
        if not k in self.nodes:
            self.nodes[k] = self.n_nodes + 1
            self.nodes[self.n_nodes + 1] = k
            self.n_nodes += 1
            return True
        else:
            return False

    def add_edge(self, start, end, capacity, weight):
        """
        expects uuid start/end nodes
        """
        self.edges.append((self.nodes[start], self.nodes[end], 0, capacity, weight))
        self.n_edges += 1

    def remove(self, k):
        self.d.pop(self.d.pop(k))

    def num_nodes(self):
        # Do not count source/sink
        return len(self.nodes) - 2

    def get_node(self, k):
        """
        given an integer returns {'u_', 'v_'}+str(UUID)
        given {'u_', 'v_'}+str(UUID) returns integer
        """

        if isinstance(k, int):
            return self.nodes[k]
        else:
            return self.nodes[k]

    def write(self, file):
        """
        writes graph to file for input to pyMCFSimplex
        """
        file.write("p min %s %s\n" % (self.n_nodes, self.n_edges))
        file.write("n %s %s\n" % (self.nodes["START"], self.demand))
        file.write("n %s %s\n" % (self.nodes["END"], -self.demand))

        for (start, end, low, high, weight) in self.edges:
            file.write("a %s %s %s %s %s\n" % (start, end, low, high, weight))

    def solve(self, demand):
        self.demand = demand
        self.mcf = pyMCFSimplex.MCFSimplex()
        fp = tempfile.TemporaryFile("w+")
        self.write(fp)
        fp.seek(0)
        inputStr = fp.read()
        fp.close()
        self.mcf.LoadDMX(inputStr)
        # solve graph
        self.mcf.SetMCFTime()
        self.mcf.SolveMCF()
        if self.mcf.MCFGetStatus() == 0:
            min_cost = self.mcf.MCFGetFO()
            if self.verbose:
                print("Optimal solution: %s" % self.mcf.MCFGetFO())
                print("Time elapsed: %s sec " % (self.mcf.TimeMCF()))
            return min_cost
        else:
            if self.verbose:
                print("Problem unfeasible!")
                print("Time elapsed: %s sec " % (self.mcf.TimeMCF()))
            return float("inf")

    def flowdict(self):
        mcf_flow_dict = dict()
        # Build flowdict
        # BEGIN FROM EXAMPLE
        mmx = self.mcf.MCFmmax()
        pSn = []
        pEn = []
        startNodes = pyMCFSimplex.new_uiarray(mmx)
        endNodes = pyMCFSimplex.new_uiarray(mmx)
        self.mcf.MCFArcs(startNodes, endNodes)

        for i in range(0, mmx):
            pSn.append(pyMCFSimplex.uiarray_get(startNodes, i) + 1)
            pEn.append(pyMCFSimplex.uiarray_get(endNodes, i) + 1)

        length = self.mcf.MCFm()

        cost_flow = pyMCFSimplex.new_darray(length)
        self.mcf.MCFGetX(cost_flow)
        # END FROM EXAMPLE

        for i in range(0, length):
            startNode = pSn[i]
            endNode = pEn[i]
            flow = pyMCFSimplex.darray_get(cost_flow, i)

            if flow > 0:
                if not self.get_node(startNode) in mcf_flow_dict:
                    mcf_flow_dict[self.get_node(startNode)] = []
                mcf_flow_dict[self.get_node(startNode)].append(self.get_node(endNode))
                # print("Flow on arc %s from node %s to node %s: %s " %(i,startNode,endNode,flow,))
        return mcf_flow_dict


phi = (1 + np.sqrt(5)) / 2
resphi = 2 - phi
# a and b are the current bounds; the minimum is between them.
# c is the center pointer pushed slightly left towards a
def goldenSectionSearch(f, a, c, b, absolutePrecision, memo=None):
    if memo is None:
        memo = dict()

    if abs(a - b) < absolutePrecision:
        return int((a + b) / 2)
    # Create a new possible center, in the area between c and b, pushed against c
    d = int(c + resphi * (b - c))

    if d in memo:
        f_d = memo[d]
    else:
        f_d = f(d)
        memo[d] = f_d
        # print(d, f_d)

    if c in memo:
        f_c = memo[c]
    else:
        f_c = f(c)
        memo[c] = f_c
        # print(c, f_c)

    if f_d < f_c:
        return goldenSectionSearch(f, c, d, b, absolutePrecision, memo)
    else:
        return goldenSectionSearch(f, d, c, a, absolutePrecision, memo)
