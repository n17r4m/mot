#!/usr/bin/python

import os
import sys
import time
from pathlib import Path
import multiprocessing as mp
import subprocess as sp
from uuid import uuid4


sys.path.append("/home/mot/py/")


from mpyx import EZ, F, Stamp, Sink, As, By
from mpyx.Vid import FFmpeg
import numpy as np

import fcntl
import shlex


from skvideo.io import FFmpegReader, FFmpegWriter
from functools import reduce


def main():
    target_vid_path = (
        "/home/mot/data/source/Glass.Bead.Tests/300.to.335.um/MSBOT-010360000023.avi"
    )
    target_vid_shape = (1729, 2336, 1)

    start = time.time()

    # print("Loading file (so that it is buffered)")
    # contents = Path(target_vid_path).read_bytes()
    # print("Took", time.time() - start, "seconds")

    # pickled = FFmpeg(target_vid_path, "", target_vid_shape, "", [], False)
    # ramdisk = FFmpegRD(target_vid_path, "", target_vid_shape, "", [], False)

    n_frames = 1000
    tests = [t(n_frames) for t in [pipe, ramdisk1, ramdisk2]]
    print("Returns:", tests)


def pipe(n_frames):
    pickled = RandomFrameEmitterPipe(n_frames)

    print("-------------")

    print("Timing decode time with multiprocess pipes")
    start = time.time()

    EZ(pickled, As(1, Sink)).start().join()

    print("Took", time.time() - start, "seconds")


def ramdisk1(n_frames):
    ramdisk = RandomFrameEmitterRamdisk(n_frames)
    print("-------------")

    print("Timing decode time with ramdisk + numpy.tobytes")

    start = time.time()

    EZ(ramdisk, As(1, RDRead)).start().join()
    print("Took", time.time() - start, "seconds")


def ramdisk2(n_frames):
    ramdisk2 = RandomFrameEmitterRamdisk2(n_frames)
    print("-------------")

    print("Timing decode time with ramdisk + numpy.save")

    start = time.time()

    EZ(ramdisk2, As(1, RDRead2)).start().join()
    print("Took", time.time() - start, "seconds")


def arg_exists(arg, args):
    return any([a.find(arg) + 1 for a in args])


class FFmpegRD(F):

    def initialize(
        self,
        input_url,
        input_opts,
        output_url,
        output_opts,
        global_opts=[],
        verbose=False,
    ):
        if isinstance(input_opts, str):
            input_opts = [input_opts]
        if isinstance(output_opts, str):
            output_opts = [output_opts]
        if isinstance(global_opts, str):
            global_opts = [global_opts]
        if isinstance(input_url, tuple):
            if len(input_url) != 3:
                raise ValueError("Input tuple shape must be (H,W,C)")

            self.input_shape = input_url
            self.input_frame_size = reduce(lambda n, x: n * x, self.input_shape)
            input_url = "-"

            if not arg_exists("-f", input_opts):
                input_opts.append("-f rawvideo")

            if not arg_exists("video_size", input_opts):
                input_opts.append(
                    "-video_size {}x{}".format(self.input_shape[1], self.input_shape[0])
                )

            if not arg_exists("pix_fmt", input_opts):
                if self.input_shape[2] == 1:
                    input_opts.append("-pix_fmt gray")
                if self.input_shape[2] == 3:
                    input_opts.append("-pix_fmt rgb24")

        if isinstance(output_url, tuple):
            if len(output_url) != 3:
                raise ValueError("Output tuple shape must be (H,W,C)")

            self.output_shape = output_url
            self.output_frame_size = reduce(lambda n, x: n * x, self.output_shape)
            output_url = "-"

            if not arg_exists("-f", output_opts):
                output_opts.append("-f rawvideo")

            if not arg_exists("video_size", output_opts):
                output_opts.append("-video_size {}x{}".format(*self.output_shape))

            if not arg_exists("pix_fmt", output_opts):
                if self.output_shape[2] == 1:
                    output_opts.append("-pix_fmt gray")
                if self.output_shape[2] == 3:
                    output_opts.append("-pix_fmt rgb24")

        self.command = " ".join(
            ["ffmpeg"]
            + global_opts
            + input_opts
            + ["-i", input_url]
            + output_opts
            + [output_url]
        )
        self.is_input_stream = input_url == "-"
        self.is_output_stream = output_url == "-"
        self.verbose = verbose

    def setup(self, *init_args):
        if self.verbose:
            print(self.command)

        self.proc = sp.Popen(
            shlex.split(self.command), stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE
        )
        # fcntl.fcntl(self.proc.stdin.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        # fcntl.fcntl(self.proc.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(self.proc.stderr.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

        if not self.is_input_stream and self.is_output_stream:
            frame_buf = None
            needed_bytes = self.output_frame_size

            while self.proc.poll() is None:
                frame_bytes = self.proc.stdout.read(self.output_frame_size)

                if len(frame_bytes) == self.output_frame_size:

                    uuid = uuid4()

                    with open("/tmp/frame_" + str(uuid), "wb") as f:
                        f.write(frame_bytes)

                    self.put(str(uuid))

                err = self.proc.stderr.read()
                if self.verbose and err != "" and err is not None:
                    print("FFmpeg:", str(err))

            self.stop()


class RandomFrameEmitterPipe(F):

    def initialize(self, n_frames=1400):
        self.n_frames = n_frames

    def setup(self, n_frames):

        video = np.random.randint(
            low=0, high=255, size=(self.n_frames, 1729, 2336, 1), dtype=np.uint8
        )
        for frame in video:
            self.put(frame)


class RandomFrameEmitterRamdisk(F):

    def initialize(self, n_frames=1400):
        self.n_frames = n_frames

    def setup(self, n_frames):

        video = np.random.randint(
            low=0, high=255, size=(self.n_frames, 1729, 2336, 1), dtype=np.uint8
        )
        for frame in video:
            uuid = uuid4()

            with open("/tmp/frame_" + str(uuid), "wb") as f:
                f.write(frame.tobytes())

            self.put(str(uuid))


class RandomFrameEmitterRamdisk2(F):

    def initialize(self, n_frames=1400):
        self.n_frames = n_frames

    def setup(self, n_frames):

        video = np.random.randint(
            low=0, high=255, size=(self.n_frames, 1729, 2336, 1), dtype=np.uint8
        )
        for frame in video:
            uuid = uuid4()
            np.save("/tmp/frame_" + str(uuid), frame)
            # with open("/tmp/frame_" + str(uuid), "wb") as f:
            # f.write(frame.tobytes())

            self.put(str(uuid))


import cv2


class RDRead(F):

    def initialize(self):
        self.output_shape = (1729, 2336, 1)

    def do(self, uuid):
        with open("/tmp/frame_" + uuid, "rb") as f:
            frame = np.fromstring(f.read(), dtype="uint8").reshape(self.output_shape)
        os.unlink("/tmp/frame_" + uuid)
        # cv2.imshow("frame", frame)
        # cv2.waitKey(100)


class RDRead2(F):

    def initialize(self):
        self.output_shape = (1729, 2336, 1)

    def do(self, uuid):
        frame = np.load("/tmp/frame_" + uuid + ".npy", "r")
        os.unlink("/tmp/frame_" + uuid + ".npy")
        # cv2.imshow("frame", frame)
        # cv2.waitKey(100)


# class RDRead2(F):

#     def initialize(self):
#         self.output_shape = (1729, 2336, 1)

#     def do(self, uuid):
#         os.unlink("/tmp/frame_" + uuid)
#         pass


if __name__ == "__main__":
    main()


# Results:
"""


Loading file (so that it is buffered)
Took 4.408074617385864 seconds
-------------
Timing decode time with ramdisk + numpy.tobytes
Took 123.58086562156677 seconds
-------------
Timing decode time with multiprocess pipes
FFmpeg Teardown
Took 52.66813945770264 seconds




Loading file (so that it is buffered)
Took 2.1704494953155518 seconds
-------------
Timing decode time with multiprocess pipes
FFmpeg Teardown
Took 42.71708011627197 seconds
-------------
Timing decode time with ramdisk + numpy.tobytes
Took 39.39739203453064 seconds



"""
