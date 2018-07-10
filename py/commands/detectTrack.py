# STABLE before chagng :)
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

import matplotlib.pyplot as plt


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

    def save_gen_fname(self, key):
        return os.path.join(config.tmp_dir, "mpyx_datagram_{}_{}.npy").format(
            key, str(uuid4())
        )


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
    method = "DetectTrack"

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
            " -vf scale={}:{}".format(w, h),
            [],
            False,
            FrameData,
        )

        # Utilities for viewing various stages of processing.
        raw_player = ImagePlayer("raw")
        crop_player = CropPlayer("crops")

        # Number of processes to spawn for particular processors
        n_prop_procs = 3
        n_crop_procs = 2
        n_binary = 1
        n_crop_writer = 2
        n_csv_procs = 2
        n_deblur_procs = 5
        n_tracker = 15
        n_fines_proc = 1

        startTime = time.time()
        # Main pipeline
        EZ(
            video_reader,
            Entry(experiment_uuid, startTime=startTime),
            MagicPixel(),
            ImageSlice("raw", ((950, 1450), (650, 1150))),
            Rescaler(scale=config.ms_rescale),
            BG(model="simpleMax", window_size=20, img_shape=(h, w, 1)),
            FG(saveAs="fg_light", name="FG_light"),
            BG(
                model="rollingMax",
                window_size=20,
                img_shape=(h, w, 1),
                inputProp="fg_light",
                saveAs="bg_fines",
                name="BG_Fines",
            ),
            FG(
                "propDivision",
                num="fg_light",
                den="bg_fines",
                saveAs="fg",
                name="FG_fines",
            ),
            Seq(
                As(n_binary, Binary, "legacyLabeled"),
                As(n_prop_procs, Properties),
                As(n_crop_procs, Crop_Processor),
                As(n_crop_writer, CropWriter, experiment_dir),
            ),
            MockClassifier(),
            VideoStreamCompressor(experiment_dir=experiment_dir, prop="raw"),
            VideoStreamCompressor(experiment_dir=experiment_dir, prop="bg"),
            VideoStreamCompressor(experiment_dir=experiment_dir, prop="fg_light"),
            VideoStreamCompressor(experiment_dir=experiment_dir, prop="bg_fines"),
            VideoStreamCompressor(experiment_dir=experiment_dir, prop="fg"),
            VideoStreamCompressor(experiment_dir=experiment_dir, prop="mask"),
            ImageSampleWriter(
                experiment_dir=experiment_dir,
                props=["raw", "bg", "fg_light", "bg_fines", "fg", "mask"],
            ),
            Passthrough(item="Frame"),
            FrameSegmentConverter(),
            As(n_tracker, Tracker),
            SegmentCSVWriter(),
            DBProcessor(experiment_uuid, experiment_day, name, method, notes),
            Passthrough(item="Segment"),
            PerformanceMonitor(
                {
                    "Properties": n_prop_procs,
                    "Crop_Processor": n_crop_procs,
                    "Binary": n_binary,
                    "CropWriter": n_crop_writer,
                    "CSVWriter": n_csv_procs,
                    "Deblur": n_deblur_procs,
                    "Fines": n_fines_proc,
                    "Tracker": n_tracker,
                }
            ),
            Cleaner(),
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


class ImageSlice(F):

    def setup(self, prop, regionOfInterest):
        self.prop = prop
        self.roi = [slice(i, j) for i, j in regionOfInterest]

    def do(self, frame):
        image = frame.load(self.prop)
        buf = image[self.roi].copy()
        frame.save(self.prop, buf)
        self.put(frame)


class VideoStreamCompressor(F):

    def setup(self, experiment_dir, prop="raw", ext=".mp4"):
        self.verbose = False
        self.queue = queue
        self.edir = experiment_dir
        self.ext = ext
        self.stop_event = multiprocessing.Event()

        self.prop = prop
        self.proc = None

    def setupStream(self, frame):
        fname = self.prop + self.ext
        array = frame.load(self.prop).squeeze()
        shape = array.shape
        width = shape[1]
        height = shape[0]
        c_width = width
        c_height = height

        if self.verbose:
            print("w:", width, "h:", height, "ndim:", array.ndim)

        if array.ndim == 2:
            pix_format = "gray"
        elif array.ndim == 3:
            pix_format = "rgb24"

        if height % 2:
            c_height = height - 1
        if width % 2:
            c_width = width - 1

        if not c_height == height or not c_width == width:
            crop_line = ', crop={}:{}:0:0"'.format(c_width, c_height)
        else:
            crop_line = '"'

        fps = config.ms_fps
        rate = 24

        # Todo: commission gpu
        gpu = -1
        if gpu < 0:
            s = " -c:v libx264 -crf 15 -preset fast"
        else:
            s = " -c:v h264_nvenc -gpu {} -preset slow".format(gpu)

        cmd = "".join(
            (
                "ffmpeg",
                " -f rawvideo -pix_fmt {}".format(pix_format),
                " -video_size {}x{}".format(width, height),
                " -framerate {}".format(fps),
                " -i -",
                s,
                " -pix_fmt yuv420p",
                ' -filter:v "setpts={}*PTS'.format(fps / rate),
                crop_line,
                " -r 24",
                " -movflags +faststart",
                ' "{}"'.format(os.path.join(self.edir, fname)),
            )
        )

        self.proc = subprocess.Popen(
            shlex.split(cmd),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        fcntl.fcntl(self.proc.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        self.log_file = open("{}.log".format(os.path.join(self.edir, fname)), "wb", 0)

    def do(self, frame):

        if self.proc is None:
            self.setupStream(frame)

        try:
            self.log_file.write(self.proc.stdout.read())
        except:
            pass

        frame_bytes = (255 * frame.load(self.prop).squeeze()).astype("uint8")

        # print(np.min(frame_bytes), np.max(frame_bytes), frame_bytes.shape)

        try:
            self.proc.stdin.write(frame_bytes)
        except:
            print("VideoStreamCompressor is borked")
            self.log_file.write(self.proc.stdout.read())

        self.put(frame)

    def teardown(self):
        self.proc.stdin.close()
        self.proc.wait()
        if self.verbose:
            print("VideoStreamCompressor Exiting")


class TimingsPrinter(F):

    def setup(self, prop=None):
        self.flag = True
        self.prop = prop

    def do(self, item):
        found = False
        if self.flag:
            if self.prop is None:
                print(self.meta["timings"])
            else:
                for k, v in self.meta["timings"].items():
                    if self.prop in k:
                        print(self.prop + " Found", k, v)
                        found = True
            if found:
                self.flag = False
        self.put(item)


class FrameSegmentConverter(F):
    """
    Convert frame data into segment data
    Detection processes by frame
    Global tracking processes by segment
    """

    def setup(self):
        self.segment = None
        self.prevTimings = None
        self.timings = {}

    def do(self, frame):
        # Detect new segment
        # Assumes ordering of input
        if self.segment is None:
            self.newSegment(frame)
        elif frame.segment_uuid != self.segment.segment_uuid:
            self.setMetaTimings()
            self.put(self.segment)
            self.newSegment(frame)

        self.insertFrame(frame)

    def insertFrame(self, frame):
        self.segment.insertFrame(frame)
        self.accountTime()

    def newSegment(self, frame):
        self.timings = {}
        self.segment = SegmentData()
        self.segment.experiment_uuid = frame.experiment_uuid
        self.segment.segment_uuid = frame.segment_uuid
        self.segment.segment_number = frame.segment_number

    def setMetaTimings(self):
        self.prevTimings = {}
        for k, v in self.meta["timings"].items():
            self.prevTimings[k] = v

        self.meta["timings"] = {}
        for k, v in self.timings.items():
            self.meta["timings"][k] = v

    def accountTime(self):
        if self.prevTimings is not None:
            self.timings = self.prevTimings.copy()
            self.prevTimings = None
        else:
            for k, v in self.meta["timings"].items():
                if "Overhead" in k:
                    pass
                    # print("FOUND OVERHEAD")
                if not k in self.timings:
                    self.timings[k] = 0.0

                self.timings[k] += self.meta["timings"][k]

    def teardown(self):
        # Todo: need to send last segment down the pipe?
        self.put(self.segment)


class ImageSampleWriter(F):

    def setup(self, experiment_dir, props=[]):
        self.sampleFreq = 100
        self.props = props
        self.count = 0
        self.experiment_dir = experiment_dir
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

    def do(self, data):
        data.clean()


class Filter(F):

    def initialize(self, properties):
        self.properties = properties

    def do(self, frame):
        for p in self.properties:
            frame.erase(p)
        self.put(frame)


class ImagePlayer(F):

    def setup(self, prop_name):
        self.freq = 30  # fps
        self.prop_name = prop_name
        self.name = self.prop_name + " Image Player"
        self.disp = None

    def do(self, frame):
        img = frame.load(self.prop_name)
        self.show(img)
        self.put(frame)

    def show(self, img):
        cmap = None
        if img is None:
            return
        if len(img.shape) == 3:
            if img.shape[-1] == 1:
                img = img.squeeze()
                cmap = "gray"
        elif len(img.shape) == 2:
            cmap = "gray"

        if self.disp is None:
            self.disp = plt.imshow(img, cmap=cmap)
        else:
            self.disp.set_data(img)
        plt.pause(1 / self.freq)
        plt.draw()


class CropPlayer(ImagePlayer):

    def cropsToImg(self, crops):
        crop_h = crops.shape[1]
        crop_w = crops.shape[2]

        crops_n = crops.shape[0]

        disp_w_n = 30
        disp_h_n = int(np.ceil(crops_n / disp_w_n))
        disp_w = int(disp_w_n * crop_w)
        disp_h = int(disp_h_n * crop_h)
        img = np.zeros((disp_h, disp_w))

        for i in range(disp_h_n):
            for j in range(disp_w_n):
                n = i * disp_h_n + j
                if n == crops_n:
                    break
                img[
                    i * crop_h : i * crop_h + crop_h, j * crop_w : j * crop_w + crop_w
                ] = crops[n].squeeze()

        return img

    def do(self, frame):
        crops = frame.load(self.prop_name)
        img = self.cropsToImg(crops)
        self.show(img)
        self.put(frame)


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


from functools import reduce


class Passthrough(F):

    def setup(self, item="item"):
        self.item = item
        self.start = None
        self.times = []

    def do(self, frame):
        if self.start is None:
            pass
        else:
            elapsed = time.time() - self.start
            self.times.append(elapsed)
            self.meta["timings"][self.item + " Passthrough"] = elapsed
        self.start = time.time()
        self.put(frame)

    def teardown(self):
        pass
        # print(self.item + " Passthrough ", reduce(lambda x, s: x + s, self.times))


# import matplotlib.pyplot as plt
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
        self.total_times_array = {}

    def do(self, frame):
        self.timings = []
        self.labels = []

        for k, v in self.meta["timings"].items():
            # Processes are labelled eg. "MyProc-6"
            label = re.split("-\d+", k)[0]

            if label == "Passthrough":
                continue
            if label == "Overhead":
                self.total_times[label] = v
                continue

            self.labels.append(label)

            if label in self.parallelisms:
                timing = v / self.parallelisms[label]
            else:
                timing = v
            self.timings.append(timing)

            if not label in self.total_times:
                self.total_times[label] = 0.0
                self.total_times_array[label] = []
            self.total_times[label] += v
            self.total_times_array[label].append(v)

        if self.verbose:
            # Todo: does this work?
            print("Completed frame", frame.number)
        if self.visualize:
            pass
            # self._visualize()
        self.put(frame)

    def teardown(self):
        # print(self.total_times)
        # print(self.total_times_array)
        print()
        print("  ----------------------  PerformanceMonitor  ----------------------  ")
        print()
        print("                     Node Name          Total / Node Times")
        print()
        for label, total_time in self.total_times.items():
            if "Passthrough" in label:
                continue

            if label in self.parallelisms:
                avg_time = total_time / self.parallelisms[label]
                print(
                    "{:>30} {:>12.2f} s / {:.2f} s".format(label, total_time, avg_time)
                )
            else:
                print("{:>30} {:>12.2f} s".format(label, total_time))
        print()

        for label, total_time in self.total_times.items():
            if not "Overhead" in label:
                continue
            print("{:>30} {:>12.2f} s".format(label, total_time))

        print()

        for label, total_time in self.total_times.items():
            if not "Passthrough" in label:
                continue

            print("{:>30} {:>12.2f} s".format(label, total_time))
        print()
        print("  ------------------------------------------------------------------  ")
        print()

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
        self.name = "Count " + name
        self.count = 0

    def do(self, frame):
        self.count += 1
        self.put(frame)

    def teardown(self):
        print("{} counted {}".format(self.name, self.count))


class Entry(F):
    """
    The first node after frame emitter.
    We use this node to stamp the frames with some meta data
    and convert the uint8 [0,255] frame to float64 [0,1]
    """

    def initialize(self, experiment_uuid, startTime=None):
        self.experiment_uuid = experiment_uuid
        self.startTime = startTime
        self.overhead = None
        self.count = 0

    def do(self, frame):
        frame.experiment_uuid = self.experiment_uuid
        frame.number = self.count
        frame.uuid = uuid4()
        self.count += 1
        frame.save("raw", frame.load("raw") / 255)
        # print("Frame", self.count, "entering...")
        self.put(frame)

        if self.startTime is not None:
            self.overhead = time.time() - self.startTime
            self.startTime = None
        if self.overhead is not None:
            self.meta["timings"]["Overhead"] = self.overhead


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
        name="BG",
        *args,
        env=None,
        **kwArgs
    ):
        self.frame_que = deque()
        self.name = name
        self.window_size = window_size
        # self.q_len = math.ceil(window_size / 2)
        # self.q_count = 0
        self.saveAs = saveAs
        self.inputProp = inputProp
        self.model = getattr(self, model)(window_size=window_size, *args, **kwArgs)

    def do(self, frame):
        # from uuid import uuid4
        self.frame_que.append(frame)
        # self.q_count += 1
        self.bg = self.model.process(frame.load(self.inputProp))

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

    def setup(self, model="bgDivision", saveAs="fg", name="FG", *args, **kwargs):
        # If your process needs to do any kind of setup once it has been forked,
        # or if it the first process in a workflow and expected to generate
        # values for the rest of the pipeline, that code should go here.
        self.saveAs = saveAs
        self.name = name
        self.model = getattr(self, model)(*args, **kwargs)

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

    class propDivision:
        """
        In a backlit scene that roughly obeys Beer-Lambert laws, dividing the
        raw image by the background (backlit scene lighting) yields the 
        transmittance, which for our application is useful.
        """

        def __init__(self, num="raw", den="bg"):
            self.numerator = num
            self.denominator = den

        def process(self, frame):
            eps = 0.0001
            numerator = frame.load(self.numerator)
            denominator = frame.load(self.denominator)
            div = numerator / (denominator + eps)
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

        def __init__(self,):
            self.threshold = config.ms_detection_threshold

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
        frame.turbidity = np.mean(frame.load("bg_fines"))
        frame.save("regionprops", properties)
        frame.track_uuids = [uuid4() for i in range(len(properties))]
        self.put(frame)


from lib.Crop import Crop


class MockClassifier(F):

    def do(self, frame):
        for p in frame.load("regionprops"):
            frame.classes.append(np.random.randint(0, 5))
        self.put(frame)


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
        self.turbidity = None
        self.classes = []


class SegmentData(Datagram):

    def __init__(self):
        # Todo: realize this
        self.experiment_uuid = None
        self.segment_uuid = None
        self.segment_number = None
        self.frames = []

    def insertFrame(self, frame):
        self.frames.append(frame)

    def numFrames(self):
        return len(self.frames)

    def clean(self):
        for frame in self.frames:
            frame.clean()
        super().clean()


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

        self.segmentFilename = "{}/{}_segment.csv".format(
            config.tmp_dir, self.experiment_uuid
        )
        self.frameFilename = "{}/{}_frame.csv".format(
            config.tmp_dir, self.experiment_uuid
        )
        self.trackFilename = "{}/{}_track.csv".format(
            config.tmp_dir, self.experiment_uuid
        )
        self.particleFilename = "{}/{}_particle.csv".format(
            config.tmp_dir, self.experiment_uuid
        )

        self.csv_files = [
            self.segmentFilename,
            self.frameFilename,
            self.trackFilename,
            self.particleFilename,
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

        if self.verbose:
            print("Inserting segments into database.")
        await self.tx.execute(
            """
            COPY segment FROM '{}' DELIMITER '\t' CSV;
            """.format(
                self.segmentFilename
            )
        )

        if self.verbose:
            print("Inserting frames into database.")
        await self.tx.execute(
            """
            COPY frame FROM '{}' DELIMITER '\t' CSV;
            """.format(
                self.frameFilename
            )
        )

        if self.verbose:
            print("Inserting particles into database.")
        await self.tx.execute(
            """
            COPY particle (particle, experiment, area, radius, intensity, perimeter, major, minor, orientation, solidity, eccentricity, category, velocity\n) FROM '{}' DELIMITER '\t' CSV;
            """.format(
                self.particleFilename
            )
        )
        if self.verbose:
            print("Inserting tracks into database.")
        await self.tx.execute(
            """
            COPY track (track, frame, particle, location, bbox) FROM '{}' DELIMITER '\t' CSV;
            """.format(
                self.trackFilename
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
        # self.cleanupFS()

    def cleanupFS(self):
        for f in self.csv_files:
            if os.path.isfile(f):
                os.remove(f)


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
        self.buildTime = 0
        self.solveTime = 0
        self.averageTime = 0
        self.rps = []

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
        for i, frame in enumerate(segment.frames):
            r = self.rps[i]
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
        for i in range(len(segment.frames) - 1):
            r1 = self.rps[i]
            coords1 = [(p.centroid[1], p.centroid[0]) for p in r1]

            r2 = self.rps[i + 1]
            coords2 = [(p.centroid[1], p.centroid[0]) for p in r2]

            neighbors = 5
            if len(coords2) <= neighbors:
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
        cal = config.ms_metric_cal
        scale = config.ms_rescale

        linear_function = lambda x: x * cal / scale
        square_function = lambda x: x * cal ** 2 / scale ** 2

        DEFAULT_CATEGORY = 0  # set to unknown for now
        equivCircleRadius = lambda area: np.sqrt(area / np.pi)

        self.particle_inserts = []
        self.track_inserts = []

        coords = [[(p.centroid[1], p.centroid[0]) for p in rp] for rp in self.rps]

        bboxes = [
            [((p.bbox[1], p.bbox[0]), (p.bbox[3], p.bbox[2])) for p in rp]
            for rp in self.rps
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
            mean_velocity = np.array([0.0, 0.0])
            prev_pos = None

            category = []
            for t in track:
                i, j = int(t.split("_")[0]), int(t.split("_")[1])
                p = self.rps[i][j]

                mean_area += p.filled_area / len(track)
                mean_intensity += p.mean_intensity / len(track)
                mean_perimeter += p.perimeter / len(track)
                mean_radius += equivCircleRadius(p.filled_area) / len(track)
                mean_major += p.major_axis_length / len(track)
                mean_minor += p.minor_axis_length / len(track)
                mean_orientation += p.orientation / len(track)
                mean_solidity += p.solidity / len(track)
                mean_eccentricity += p.eccentricity / len(track)

                if prev_pos is not None:
                    mean_velocity += (np.array(p.centroid) - prev_pos) / (
                        len(track) - 1
                    )
                prev_pos = np.array(p.centroid)

                cat = segment.frames[i].classes[j]
                category.append(cat)

                loc = coords[i][j]
                bbox = bboxes[i][j]
                new_track_uuid = segment.frames[i].track_uuids[j]
                new_frame_uuid = segment.frames[i].uuid
                self.track_inserts.append(
                    (new_track_uuid, new_frame_uuid, new_particle_uuid, loc, bbox)
                )

            category = np.argmax(np.bincount(category))

            self.particle_inserts.append(
                (
                    new_particle_uuid,
                    segment.experiment_uuid,
                    square_function(mean_area),
                    linear_function(mean_radius),
                    mean_intensity,
                    linear_function(mean_perimeter),
                    linear_function(mean_major),
                    linear_function(mean_minor),
                    mean_orientation,
                    mean_solidity,
                    mean_eccentricity,
                    category,
                    tuple(
                        linear_function(mean_velocity[::-1]) * config.ms_fps / 1000000
                    ),
                )
            )

    def do(self, segment):
        self.rps = []
        for frame in segment.frames:
            self.rps.append(frame.load("regionprops"))

        start = time.time()
        self.buildGraph(segment)
        self.buildTime += time.time() - start

        start = time.time()
        self.solve()
        self.solveTime += time.time() - start

        if self.verbose:
            print("Tracks reconstructed", len(self.tracks))

        start = time.time()
        try:
            self.computeAverages(segment)
        except Exception as e:
            print("Problem in averages", e)
            raise e

        self.averageTime += time.time() - start

        segment.save("particles", self.particle_inserts)
        segment.save("tracks", self.track_inserts)

        self.put(segment)

    def teardown(self,):
        pass
        # print("Building graph", self.buildTime)
        # print("Solving", self.solveTime)
        # print("Averages", self.averageTime)


class SegmentCSVWriter(F):

    def initialize(self):
        self.verbose = False
        if self.verbose:
            print("Launching CSV processor")

        self.trackFilename = os.path.join(config.tmp_dir, "{}_track.csv")
        self.particleFilename = os.path.join(config.tmp_dir, "{}_particle.csv")
        self.segmentFilename = os.path.join(config.tmp_dir, "{}_segment.csv")
        self.frameFilename = os.path.join(config.tmp_dir, "{}_frame.csv")
        self.experiment_uuid = None

    def do(self, segment):
        try:
            if self.experiment_uuid is None:
                self.experiment_uuid = segment.experiment_uuid
                self.openFiles()

            self.addSegmentData(segment)
            self.put(segment)
        except Exception as e:
            print(e)

    def openFiles(self):
        self.trackFilename = self.trackFilename.format(self.experiment_uuid)
        self.particleFilename = self.particleFilename.format(self.experiment_uuid)
        self.segmentFilename = self.segmentFilename.format(self.experiment_uuid)
        self.frameFilename = self.frameFilename.format(self.experiment_uuid)

        self.trackFile = open(self.trackFilename, "a")
        self.particleFile = open(self.particleFilename, "a")
        self.segmentFile = open(self.segmentFilename, "a")
        self.frameFile = open(self.frameFilename, "a")

    def closeFiles(self):
        self.trackFile.close()
        self.particleFile.close()
        self.segmentFile.close()
        self.frameFile.close()

    def addSegmentData(self, segment):

        particles = segment.load("particles")
        tracks = segment.load("tracks")

        data = (segment.segment_uuid, segment.experiment_uuid, segment.segment_number)
        self.segmentFile.write("\t".join(map(str, data)) + "\n")

        for frame in segment.frames:
            self.addFrameData(frame)

        for p in particles:
            self.particleFile.write("\t".join(map(str, p)) + "\n")

        for t in tracks:
            self.trackFile.write("\t".join(map(str, t)) + "\n")

    def addFrameData(self, frame):
        data = (
            frame.uuid,
            frame.experiment_uuid,
            frame.segment_uuid,
            frame.number,
            frame.turbidity,
        )
        self.frameFile.write("\t".join(map(str, data)) + "\n")

    def teardown(self,):
        self.closeFiles()


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
