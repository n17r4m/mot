#!/usr/bin/python

import os
import sys
import time
import socket
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

    n_frames = 1000
    frames_s = (1729, 2336, 1)

    print("Making 'video'")
    start = time.time()
    video = np.random.randint(
        low=0, high=255, size=(n_frames, *frames_s), dtype=np.uint8
    )

    print("Took {}".format(time.time() - start), "seconds")

    start = time.time()

    foos = [pipe, ramdisk1, ramdisk2]

    for i in a:
        dashit(time.time())
        foos[i](n_frames)


# Preamble
def dashit(it, *args):
    print("---{}---".format(it))


def timeit(then):
    print("Took {} seconds.".format(time.time() - then))


def pipe(n_frames):
    """
    Use normal python provided queues.
    """
    pickled = RandomFrameEmitterPipe(n_frames)
    print("Timing decode time with multiprocess pipes")
    start = time.time()
    EZ(pickled, As(1, Sink)).start().join()
    timeit(start)


def ramdisk1(n_frames):
    ramdisk = RandomFrameEmitterRamdisk(n_frames)
    print("Timing decode time with ramdisk + numpy.tobytes")
    start = time.time()
    EZ(ramdisk, As(1, RDRead)).start().join()
    timeit(start)


def ramdisk2(n_frames):
    ramdisk2 = RandomFrameEmitterRamdisk2(n_frames)
    print("Timing decode time with ramdisk + numpy.save")
    start = time.time()
    EZ(ramdisk2, As(1, RDRead2)).start().join()
    timeit(start)


def posixsocket(n_frames):
    sock = PosixSocketEmitter(n_frames)
    print("Timing decode time over unix domain sockets")
    start = time.time()
    EZ(sock, As(1, SXRead)).start().join()
    timeit(start)


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

    def setup(self, n_frames):
        global video
        for frame in video:
            self.put(frame)


class RandomFrameEmitterRamdisk(F):

    def setup(self, n_frames):
        global video
        for frame in video:
            uuid = uuid4()
            with open("/tmp/frame_" + str(uuid), "wb") as f:
                f.write(frame.tobytes())
            self.put(str(uuid))


class RandomFrameEmitterRamdisk2(F):

    def setup(self, n_frames):
        global video
        for frame in video:
            uuid = uuid4()
            np.save("/tmp/frame_" + str(uuid), frame)
            self.put(str(uuid))


class PosixSocketEmitter(F):

    def setup(self, n_frames):
        global video
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock_id = uuid4()
        self.sock_file = "/tmp/pysocket-{}".format(self.sock_id)

        self.sock.bind(sock_file)

        print("waiting for a connection")
        self.sock.listen(1)
        self.put(self.sock_file)
        self.connection, self.client_address = self.sock.accept()
        print("connection from", self.client_address)

        for frame in video:
            self.sock.send(frame)  # naive.

        connection.close()


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


class SXRead(F):

    def initialize(self):
        self.output_shape = (1729, 2336, 1)

    def do(self, sock_file):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        print("connecting to {}".format(sock_file))
        sock.connect(sock_file)


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
