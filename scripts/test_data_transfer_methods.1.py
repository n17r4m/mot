#!/usr/bin/python

"""
Test the performance of several inter-process transfer methods on a large "video".


"""

import os
import sys
import time
import socket
import array
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

video = None

n_frames = 100
frames_s = (1729, 2336, 1)
fbytes_s = 1729 * 2336 * 8  # float64
f_dtype = "float64"


def main():

    print("Making 'video' with {} frames".format(n_frames))
    Timeit.start()
    global video
    video = np.random.random(size=(n_frames, *frames_s))

    Timeit.end()

    foos = [pipe, ramdisk1, ramdisk2, ramdisk3, posixsocket]
    a = np.array(range(len(foos)))
    np.random.shuffle(a)

    print("Running tests...")
    print("----------------")

    for i in a:
        # dashit(time.time())
        foos[i](n_frames)


# Preamble
def dashit(it, *args):
    print("---{}---".format(it))


class Timeit(object):
    import time

    startTime = time.time()

    @staticmethod
    def start():
        Timeit.startTime = time.time()

    @staticmethod
    def end():
        print(" `-> Took {} seconds.".format(time.time() - Timeit.startTime))


def pipe(n_frames):
    ez = EZ(RandomFrameEmitterPipe(n_frames), As(1, Sink))
    print("Timing decode time with multiprocess pipes")
    Timeit.start()
    ez.start().join()
    Timeit.end()


def ramdisk1(n_frames):
    ez = EZ(RandomFrameEmitterRamdisk(n_frames), As(1, RDRead))
    print("Timing decode time with ramdisk + numpy.tobytes")
    Timeit.start()
    ez.start().join()
    Timeit.end()


def ramdisk2(n_frames):
    ez = EZ(RandomFrameEmitterRamdisk2(n_frames), As(1, RDRead2))
    print("Timing decode time with ramdisk + numpy.save")
    Timeit.start()
    ez.start().join()
    Timeit.end()


def ramdisk3(n_frames):
    ez = EZ(RandomFrameEmitterRamdisk3(n_frames), As(1, RDRead3))
    print("Timing decode time with ghosted file descriptor passing")
    Timeit.start()
    ez.start().join()
    Timeit.end()


def posixsocket(n_frames):
    ez = EZ(PosixSocketEmitter(n_frames), As(1, SXRead))
    print("Timing decode time over unix domain sockets")
    Timeit.start()
    ez.start().join()
    Timeit.end()


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


class RandomFrameEmitterRamdisk3(F):

    def setup(self, n_frames):
        global video
        for frame in video:
            uuid = uuid4()
            fname = "/tmp/frame_" + str(uuid) + ".npy"
            np.save(fname, frame)
            f = open(fname, "rb")
            self.put(f)
            f.close()
            os.remove(fname)


class PosixSocketEmitter(F):

    def setup(self, n_frames):
        global video
        global fbytes_s
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock_id = uuid4()
        self.sock_file = "/tmp/pysocket-{}".format(self.sock_id)

        self.sock.bind(self.sock_file)

        print("waiting for a connection")
        self.sock.listen(1)
        self.put(self.sock_file)
        self.connection, self.client_address = self.sock.accept()
        print("connection from", self.client_address, self.connection)

        for frame in video:
            self.connection.sendall(frame.tobytes())

        self.connection.close()


import cv2


class RDRead(F):

    def initialize(self):
        global frames_s
        self.output_shape = frames_s

    def do(self, uuid):
        with open("/tmp/frame_" + uuid, "rb") as f:
            frame = np.fromstring(f.read(), dtype="float64").reshape(self.output_shape)
        os.unlink("/tmp/frame_" + uuid)
        # cv2.imshow("frame", frame)
        # cv2.waitKey(100)


class RDRead2(F):

    def initialize(self):
        global frames_s
        self.output_shape = frames_s

    def do(self, uuid):
        frame = np.load("/tmp/frame_" + uuid + ".npy", "r")
        os.unlink("/tmp/frame_" + uuid + ".npy")
        # cv2.imshow("frame", frame)
        # cv2.waitKey(100)


class RDRead3(F):

    def initialize(self):
        global frames_s
        global f_dtype
        self.output_shape = frames_s
        self.data_type = f_dtype

    def do(self, f):

        frame = np.frombuffer(f.read(), dtype=self.data_type)
        print("got", len(frame))
        # cv2.imshow("frame", frame)
        # cv2.waitKey(100)


class SXRead(F):

    def initialize(self):
        global frames_s
        global fbytes_s
        global n_frames
        global f_dtype
        self.output_shape = frames_s
        self.frame_bytes = fbytes_s
        self.num_frames = n_frames
        self.data_type = f_dtype

    def do(self, sock_file):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        print("connecting to {}".format(sock_file))
        self.sock.connect(sock_file)

        for f in range(self.num_frames):
            want = self.frame_bytes
            frame_bytes = b""
            while want > 0:
                new_bytes = self.sock.recv(want)
                frame_bytes += new_bytes
                want -= len(new_bytes)

            frame = np.frombuffer(frame_bytes, dtype=self.data_type)

        self.sock.close()
        os.remove(sock_file)


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
