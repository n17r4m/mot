
from skimage import io
from skimage.transform import downscale_local_mean
from skimage.filters import threshold_sauvola as threshold
from skimage.segmentation import clear_border, random_walker
from skimage.measure import label, regionprops
from skimage.morphology import binary_opening, square, remove_small_objects
from skimage.color import gray2rgb
from skimage.draw import circle

import config

from mpyx.F import EZ, As, By, F, Datagram

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

from PIL import Image
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

# import matplotlib.pyplot as plt


async def main(args):
    if len(args) < 2:
        print("""path/to/video/file.avi 2017-10-31 Name-of_video "Notes. Notes." """)
    else:
        print(await detect_video(*args))


async def detect_video(video_file, date, name="Today", notes=""):

    cpus = multiprocessing.cpu_count()

    experiment_uuid = uuid4()
    experiment_day = dateparse(date)
    experiment_dir = os.path.join(config.experiment_dir, str(experiment_uuid))
    experiment = (experiment_uuid, experiment_day, name, "detection", notes)

    try:

        print("Creating data directory", experiment_dir)
        os.mkdir(experiment_dir)

        scaleby = 1
        w, h = int(2336 / scaleby), int(1729 / scaleby)

        # Reads the source video, outputs frames
        print("Launching Video Reader")
        video_reader = FFmpeg(
            video_file,
            "",
            (h, w, 1),
            "-ss 00:00:02.00 -t 00:00:00.50 -vf scale={}:{}".format(w, h),
            [],
            False,
            FrameData,
        )

        print("Launching Database processor")
        db_proc = DB_Processor(experiment_uuid, experiment_day, name, notes)

        print("Launching Entry processor")
        entry_proc = Entry(experiment_uuid)

        print("Launching Magic pixel processor")
        magic_proc = MagicPixel()

        print("Launching Rescale processor")
        rescale_proc = Rescaler()

        # Computes a background for a frame, outputs {"frame": frame, "bg": bg}
        print("Launching Background Modeler")
        bg_proc = BG(model="simpleMax", window_size=50, img_shape=(h, w, 1))

        # Takes a background and a frame, enhances frame to model foreground
        print("Launching Foreground Modeler")
        fg_proc = FG()

        # Takes a foreground frame, binarizes it
        print("Launching Binary Mask Processor")
        mask_proc = Binary("legacyLabeled")

        print("Launching Properties Processor")
        prop_proc = Properties()

        print("Launching Crop Processor")
        crop_proc = Crop_Processor()

        # A utility to view video pipeline output
        raw_player = RawPlayer()
        bg_player = BGPlayer()
        fg_player = FGPlayer()
        mask_player = MaskPlayer()
        crop_player = CropPlayer()
        meta_player = MetaPlayer()

        # A utility to clean up datagram resources
        cleaner = Cleaner()
        # Todo
        # print("Launching Crop Writer")

        # print("Launching Detection Video Writer")
        # print("Launching Particle Commmitter")
        # /todo

        EZ(
            video_reader,
            entry_proc,
            magic_proc,
            meta_player,
            rescale_proc,
            raw_player,
            bg_proc,
            fg_proc,
            mask_proc,
            cleaner,
        ).start().join()

    except Exception as e:

        print("Uh oh. Something went wrong")

        traceback.print_exc()
        # wq.push(None)

        if os.path.exists(experiment_dir):
            print("Removing files from", experiment_dir)
            shutil.rmtree(experiment_dir)

    else:
        pass
        # dbwriter.commit()
        # wq.push(None)

    finally:

        print("Fin.")

    return experiment_uuid


class Cleaner(F):

    def do(self, frame):
        frame.clean()


class RawPlayer(F):

    def do(self, frame):
        cv2.imshow("Raw Display", frame.raw)
        self.put(frame)
        cv2.waitKey(1000 // 24)


class FGPlayer(F):

    def do(self, frame):
        cv2.imshow("FG Display", frame.fg)
        self.put(frame)
        cv2.waitKey(1000 // 24)


class MaskPlayer(F):

    def do(self, frame):
        cv2.imshow("Mask Display", 1.0 * frame.mask)
        self.put(frame)
        cv2.waitKey(1000 // 24)


class BGPlayer(F):

    def do(self, frame):
        cv2.imshow("BG Display", frame.bg)
        self.put(frame)
        cv2.waitKey(1000 // 24)


class CropPlayer(F):

    def do(self, frame):
        crops = frame.crops

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


class MetaPlayer(F):

    def do(self, frame):
        print(
            "Experiment:",
            frame.experiment_uuid,
            ", Segment:",
            frame.segment_uuid,
            " Number:",
            frame.number,
            " Segment Number:",
            frame.segment_number,
        )
        self.put(frame)


class Entry(F):

    def initialize(self, experiment_uuid):
        self.experiment_uuid = experiment_uuid
        self.count = 0

    def do(self, frame):
        frame.experiment_uuid = self.experiment_uuid
        frame.number = self.count
        frame.uuid = uuid4()
        self.count = +1
        frame.raw = frame.raw / 255
        self.put(frame)


class MagicPixel(F):
    # Not sure this works currently...
    def do(self, frame):
        magic_pixel = 255
        magic_pixel_delta = 0.1
        segment_number = -1
        raw = frame.raw

        if config.use_magic_pixel_segmentation:
            this_frame_magic_pixel = raw[0, 4, 0]
            if abs(this_frame_magic_pixel - magic_pixel) > magic_pixel_delta:
                print("Segment Boundry Detected")
                segment_number += 1
                segment = (uuid4(), frame.experiment_uuid, segment_number)

            magic_pixel = this_frame_magic_pixel
        frame.segment_uuid = segment[0]
        frame.segment_number = segment[2]
        self.put(frame)


from skimage.transform import rescale


class Rescaler(F):

    def do(self, frame):
        frame.raw = rescale(frame.raw, 0.5)
        self.put(frame)


import math
from collections import deque


class BG(F):

    def setup(self, model="median", window_size=20, *args, env=None, **kwArgs):
        self.frame_que = deque(maxlen=window_size)
        self.window_size = window_size
        # self.q_len = math.ceil(window_size / 2)
        # self.q_count = 0
        self.model = getattr(self, model)(window_size=window_size, *args, **kwArgs)

    def do(self, frame):
        # import cv2
        # from uuid import uuid4
        self.frame_que.append(frame)
        # self.q_count += 1
        self.bg = self.model.process(frame.raw)
        # cv2.imwrite('/home/mot/tmp/bg_'+str(uuid4())+'.png', self.bg)

        if len(self.frame_que) > self.window_size:
            # bg = self.que.popleft()
            frame = self.frame_que.popleft()
            frame.bg = self.bg
            self.put(frame)

    def teardown(self):
        while len(self.frame_que) > 0:
            # self.q_count -= 1
            frame = self.frame_que.popleft()
            frame.bg = self.bg
            self.put(frame)

    class simpleMax:

        def __init__(self, window_size=20, img_shape=None):

            # print("simpleMax maxlen: "+str(math.ceil(window_size / 2)-5))
            self.window_size = window_size
            self.que = deque(maxlen=window_size)
            self.bg = None

        def process(self, frame):
            # like erosion, but faster
            from skimage.filters.rank import minimum

            # parameter: minimum lighting (dynamic range), threshold below
            min_range = 20

            if len(self.que) < self.window_size:
                self.que.append(frame)
            elif len(self.que) == self.window_size:
                # print("computing bg...")
                if self.bg is None:
                    bg = np.max(self.que, axis=0)
                    bg[bg < min_range] = 0
                    bg = minimum(bg.squeeze(), square(8))
                    bg = np.expand_dims(bg, axis=-1)
                    self.bg = bg
            return self.bg


class FG(F):

    def setup(self, model="division", *args, **kwargs):
        # If your process needs to do any kind of setup once it has been forked,
        # or if it the first process in a workflow and expected to generate
        # values for the rest of the pipeline, that code should go here.
        self.model = getattr(self, model)()

    def do(self, frame):
        # The main workhorse of a process. Items will flow in here, potentially
        # be modified, mapped, reduced, or otherwise morgified, and output can
        # be then pushed downstream using the self.put() method.
        # Here, for example, any items are simply passed along.
        frame.fg = self.model.process(frame)

        self.put(frame)

    class division:

        def __init__(self):
            pass

        def process(self, frame):
            """
            Expects a dict with bg, frame
            """
            eps = 0.0001
            div = frame.raw / (frame.bg + eps)
            # div[np.isnan(div)] = 1.0  # get rid of nan's from 0/0
            return np.clip(div, 0, 1)


from skimage.filters import threshold_sauvola
from skimage.morphology import binary_opening, remove_small_objects, square, erosion
from skimage.segmentation import clear_border


class Binary(F):

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
        frame.mask = self.model.process(frame)
        self.put(frame)

    class legacyLabeled:

        def __init__(self, threshold=0.5):
            self.threshold = threshold

        def process(self, frame):
            # Take the center, removing edge artifacts
            # frame = frame[200:-200, 200:-200]
            sframe = frame.fg.squeeze()
            binary = sframe < self.threshold
            binary = binary_opening(binary, square(3))
            binary = clear_border(binary)
            # opened = binary_opening(binary, square(3))
            # cleared = clear_border(opened)
            return binary


from skimage.measure import label, regionprops


class Properties(F):

    def do(self, frame):
        labelled = label(frame.mask)
        frame.regionprops = regionprops(labelled, frame.fg.squeeze())
        frame.track_uuids = [uuid4() for i in range(len(properties))]
        self.put(frame)


from lib.Crop import Crop


class Crop_Processor(F):

    def do(self, frame):
        regionprops = frame.regionprops
        cropper = Crop(frame.fg)

        coords = [(p.centroid[1], p.centroid[0]) for p in regionprops]
        bboxes = [((p.bbox[1], p.bbox[0]), (p.bbox[3], p.bbox[2])) for p in regionprops]
        crops = np.array(
            [cropper.crop(int(round(c[0])), int(round(c[1]))) for c in coords]
        )
        frame.crops = crops
        self.put(frame)


class Crop_writer(F):

    def do(self, frame):
        crops = frame.crops


class FrameData(Datagram):

    def initialize(self):
        self.experiment_uuid = None
        self.segment_uuid = None
        self.segment_number = None
        self.uuid = None
        self.number = None


class DB_Processor(F):

    async def initialize(
        self, experiment_uuid, experiment_day, name, notes, verbose=False
    ):
        self.verbose = verbose
        self.experiment_uuid = experiment_uuid
        self.experiment_day = experiment_day
        self.name = name
        self.notes = notes
        self.tx, self.transaction = await Database().transaction()
        self.csv_files = [
            "/tmp/{}_segment.csv",
            "/tmp/{}_frame.csv",
            "/tmp/{}_track.csv",
            "/tmp/{}_particle.csv",
        ]

    def add_segment(self, frame):
        data = (frame.segment_uuid, frame.experiment_uuid, frame.segment_number)
        s = "{}\t{}\t{}\n"
        with open("/tmp/{}_segment.csv".format(self.experiment_uuid), "a") as f:
            for g in [data]:
                f.write(s.format(segment[0], segment[1], segment[2]))

    def add_frame(self, frame):

        data = (frame.uuid, frame.experiment_uuid, frame.segment_uuid, frame.number)

        s = "{}\t{}\t{}\t{}\n"
        with open("/tmp/{}_frame.csv".format(self.experiment_uuid), "a") as f:
            for g in [data]:
                f.write(s.format(g[0], g[1], g[2], g[3]))

    def add_detections(self, frame):
        regionprops = frame.regionprops
        DEFAULT_CATEGORY = 1  # set to unknown for now
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
            for i, p in enumerate(regionprops)
        ]

        coords = [(p.centroid[1], p.centroid[0]) for p in regionprops]
        bboxes = [((p.bbox[1], p.bbox[0]), (p.bbox[3], p.bbox[2])) for p in regionprops]

        track_uuids = frame.track_uuids

        tracks = [
            (track_uuids[i], frame_uuid, p[0], coords[i], bboxes[i])
            for i, p in enumerate(regionprops)
        ]
        s = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n"
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
                    )
                )

            s = "{}\t{}\t{}\t{}\t{}\n"
            with open("/tmp/{}_track.csv".format(self.experiment_uuid), "a") as f:
                for t in tracks:
                    f.write(s.format(t[0], t[1], t[2], t[3], t[4]))

    def do(self, sql_drop):
        method, query, args = sql_drop

        if self.verbose:
            print("DBWriter Exiting")

    async def teardown(self):
        if self.verbose:
            print("Inserting experiment into database.")
        await tx.execute(
            """
            INSERT INTO Experiment (experiment, day, name, method, notes) 
            VALUES ($1, $2, $3, $4, $5)
            """,
            self.experiment_uuid,
            self.experiment_day,
            self.name,
            "DetectionMpyxDatagram",
            self.notes,
        )

        if self.verbose:
            print("Inserting segments into database.")
        await self.tx.execute(
            """
            COPY segment FROM '/tmp/{}_segment.csv' DELIMITER '\t' CSV;
            """.format(
                self.experiment_uuid
            )
        )
        if self.verbose:
            print("Inserting frames into database.")
        await self.tx.execute(
            """
            COPY frame FROM '/tmp/{}_frame.csv' DELIMITER '\t' CSV;
            """.format(
                self.experiment_uuid
            )
        )
        if self.verbose:
            print("Inserting particles into database.")
        await self.tx.execute(
            """
            COPY particle (particle, experiment, area, intensity, perimeter, major, minor, orientation, solidity, eccentricity, category\n)FROM '/tmp/{}_particle.csv' DELIMITER '\t' CSV;
            """.format(
                self.experiment_uuid
            )
        )
        if self.verbose:
            print("Inserting tracks into database.")
        await tx.execute(
            """
            COPY track (track, frame, particle, location, bbox\n) FROM '/tmp/{}_track.csv' DELIMITER '\t' CSV;
            """.format(
                experiment_uuid
            )
        )

        await self.transaction.commit()

        for f in csv_files:
            if os.path.isfile(f.format(self.experiment_uuid)):
                os.remove(f.format(self.experiment_uuid))
