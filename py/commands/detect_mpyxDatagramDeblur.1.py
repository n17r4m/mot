
from skimage import io
from skimage.transform import downscale_local_mean
from skimage.filters import threshold_sauvola as threshold
from skimage.segmentation import clear_border, random_walker
from skimage.measure import label, regionprops
from skimage.morphology import binary_opening, square, remove_small_objects
from skimage.color import gray2rgb
from skimage.draw import circle

import config

from mpyx.F import EZ, As, By, F, Seq, Data as Datagram

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
import cv2

import warnings

# import matplotlib.pyplot as plt


async def main(args):
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
        ms_metric_cal = 13.94736842

        # Reads the source video, outputs frames
        # -ss 00:00:02.00 -t 00:00:00.50
        video_reader = FFmpeg(
            video_file,
            "",
            (h, w, 1),
            "-vf scale={}:{}".format(w, h),
            [],
            False,
            FrameData,
        )

        csv_proc = CSVWriter(experiment_uuid, experiment_day, name, method, notes)
        db_proc = DBProcessor(experiment_uuid, experiment_day, name, method, notes)

        # Computes a background for a frame, outputs {"frame": frame, "bg": bg}
        bg_proc = BG(model="simpleMax", window_size=20, img_shape=(h, w, 1))

        fines_proc = BG(
            model="rollingMax",
            window_size=20,
            img_shape=(h, w, 1),
            inputProp="div",
            saveAs="fines",
        )

        # Utilities for viewing various stages of processing.
        raw_player = RawPlayer()
        bg_player = BGPlayer()
        fg_player = FGPlayer()
        mask_player = MaskPlayer()
        crop_player = CropPlayer()
        meta_player = MetaPlayer()

        # Number of processes to spawn for particular processors
        n_prop_procs = 10
        n_crop_procs = 4
        n_binary = 5
        n_crop_writer = 10
        n_csv_procs = 10
        n_deblur_procs = 20

        # Main pipeline
        EZ(
            video_reader,
            Counter(),
            Entry(experiment_uuid, ms_metric_cal),
            MagicPixel(),
            Rescaler(scale=1 / 4),
            Counter("Rescaled"),
            bg_proc,
            FG(saveAs="div"),
            fines_proc,
            Counter("fines"),
            FG("finesDivision", saveAs="fg"),
            Seq(
                # As(n_deblur_procs, Deblur),
                As(n_binary, Binary, "legacyLabeled"),
                As(n_prop_procs, Properties),
                As(n_crop_procs, Crop_Processor),
                As(n_crop_writer, CropWriter, experiment_dir),
                Counter("crops"),
                As(
                    n_csv_procs,
                    CSVWriter,
                    experiment_uuid,
                    experiment_day,
                    name,
                    method,
                    notes,
                ),
                Counter("csv"),
            ),
            db_proc,
            Counter("db"),
            Passthrough(),
            PerformanceMonitor(
                {
                    "Properties": n_prop_procs,
                    "Crop_Processor": n_crop_procs,
                    "Binary": n_binary,
                    "CropWriter": n_crop_writer,
                    "CSVWriter": n_csv_procs,
                    "Deblur": n_deblur_procs,
                }
            ),
            Counter("performance"),
            # raw_player,
            # bg_player,
            # fg_player,
            # mask_player,
            # MetaPlayer(),
            ImageSampleWriter(
                str(experiment_dir), ["bg", "div", "fg", "raw", "mask", "fines"]
            ),
            Counter("samplewriter"),
            Cleaner(),
            # qsize=10,
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


class RawPlayer(F):

    def do(self, frame):
        cv2.imshow("Raw Display", frame.load("raw"))
        self.put(frame)
        cv2.waitKey(1000 // 24)


class FGPlayer(F):

    def setup(self, win_name="FG Display"):
        self.win_name = win_name

    def do(self, frame):
        cv2.imshow(self.win_name, frame.load("fg"))
        self.put(frame)
        cv2.waitKey(1000 // 24)


class MaskPlayer(F):

    def do(self, frame):
        cv2.imshow("Mask Display", 1.0 * frame.load("mask"))
        self.put(frame)
        cv2.waitKey(1000 // 24)


class BGPlayer(F):

    def do(self, frame):
        cv2.imshow("BG Display", frame.load("bg"))
        self.put(frame)
        cv2.waitKey(1000 // 24)


class CropPlayer(F):

    def do(self, frame):
        crops = frame.load("crops")

        crop_h = crops.shape[1]
        crop_w = crops.shape[2]

        crops_n = crops.shape[0]

        disp_w_n = 30
        disp_h_n = int(np.ceil(crops_n / disp_w_n))
        disp_w = int(disp_w_n * crop_w)
        disp_h = int(disp_h_n * crop_h)
        disp = np.zeros((disp_h, disp_w))

        # print("------------------")
        # print("crops:", crops.shape)
        # print("crop_h", crop_h)
        # print("crop_w", crop_w)
        # print("crops_n", crops_n)
        # print("disp_w", disp_w)
        # print("disp_h", disp_h)

        for i in range(disp_h_n):
            for j in range(disp_w_n):
                n = i * disp_h_n + j
                if n == crops_n:
                    break
                disp[
                    i * crop_h : i * crop_h + crop_h, j * crop_w : j * crop_w + crop_w
                ] = crops[n].squeeze()

        cv2.imshow("Crop Display", disp)
        self.put(frame)
        cv2.waitKey(1000 // 24)


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
        self.meta["timings"]["Time per item"] = time.time() - self.start
        self.start = time.time()
        self.put(frame)


import matplotlib.pyplot as plt
import numpy as np
import re


class PerformanceMonitor(F):

    def setup(self, parallelisms={}, visualize=False, log=False, verbose=False):
        self.visualize = visualize
        self.log = log
        self.fig = None
        self.ax = None
        self._visBars = None
        self.parallelisms = parallelisms
        self.verbose = verbose
        self.total_times = {}

    def do(self, frame):
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

    def initialize(self, experiment_uuid, metric_cal=None):
        self.experiment_uuid = experiment_uuid
        self.count = 0
        self.metric_cal = metric_cal

    def do(self, frame):
        frame.experiment_uuid = self.experiment_uuid
        frame.number = self.count
        frame.uuid = uuid4()
        frame.metric_cal = self.metric_cal
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
        frame.scale = self.scale
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

            if frame.metric_cal is not None:
                config_small_object_diameter = 100  # microns diameter
                # Area of equivalent circle
                small_threshold = (
                    np.pi
                    * (
                        (config_small_object_diameter / 2)
                        / frame.metric_cal
                        * frame.scale
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
        self.filter_area = filter_area
        self.filter_area_low = 100
        self.filter_area_high = 2000

    def do(self, frame):
        labelled = label(frame.load("mask"))
        properties = regionprops(labelled, frame.load("fg").squeeze())
        if self.filter_area:
            properties = [
                p
                for p in properties
                if p.area > self.filter_area_low and p.area < self.filter_area_high
            ]
        frame.save("regionprops", properties)
        frame.save("track_uuids", [uuid4() for i in range(len(properties))])
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
        track_uuids = frame.load("track_uuids")
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

    def initialize(self, metric_cal=None, scale=1 / 1):
        self.experiment_uuid = None
        self.segment_uuid = None
        self.segment_number = None
        self.uuid = None
        self.number = None
        self.metric_cal = metric_cal
        self.scale = scale


class CSVWriter(F):

    def initialize(
        self, experiment_uuid, experiment_day, name, method, notes, verbose=False
    ):
        self.verbose = verbose
        if self.verbose:
            print("Launching CSV processor")
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

        # Add frame
        self.add_frame(frame)

        # Add detections
        self.add_detections(frame)

        self.put(frame)

    def add_frame(self, frame):
        if config.use_magic_pixel_segmentation:
            data = (frame.uuid, frame.experiment_uuid, frame.segment_uuid, frame.number)
            s = "{}\t{}\t{}\t{}\n"
            with open("/tmp/{}_frame.csv".format(self.experiment_uuid), "a") as f:
                f.write(s.format(data[0], data[1], data[2], data[3]))
        else:
            data = (frame.uuid, frame.experiment_uuid, frame.number)
            s = "{}\t{}\t{}\n"
            with open("/tmp/{}_frame.csv".format(self.experiment_uuid), "a") as f:
                f.write(s.format(data[0], data[1], data[2]))

    def add_detections(self, frame):
        regionprops = frame.load("regionprops")
        metric_cal = frame.metric_cal
        scale = frame.scale
        DEFAULT_CATEGORY = 0  # set to unknown for now

        equivCircleRadius = lambda area: np.sqrt(area / np.pi)

        if False:
            # A failed attempt to adjust the metric properties to
            # glass beads physical ground truth
            cal = 0.7638888888888888
        else:
            cal = 1.0

        if metric_cal is not None:
            radius_function = lambda x: cal * equivCircleRadius(x) * metric_cal / scale
            linear_function = lambda x: cal * x * metric_cal / scale
            area_function = lambda x: cal ** 2 * x * metric_cal ** 2 / scale ** 2
        else:
            radius_function = equivalentCircleRadius
            linear_function = lambda x: x
            area_function = lambda x: x

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

        track_uuids = frame.load("track_uuids")

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

        self.prev_segment_uuid = None

    def do(self, frame):
        # Add segment
        if config.use_magic_pixel_segmentation:
            if frame.segment_uuid != self.prev_segment_uuid:
                self.prev_segment_uuid = frame.segment_uuid
                self.add_segment(frame)

        self.put(frame)

    def add_segment(self, frame):
        data = (frame.segment_uuid, frame.experiment_uuid, frame.segment_number)
        s = "{}\t{}\t{}\n"
        with open("/tmp/{}_segment.csv".format(self.experiment_uuid), "a") as f:
            f.write(s.format(data[0], data[1], data[2]))

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
