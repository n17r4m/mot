#!/usr/bin/python

"""
Test the performance of several inter-process transfer methods on a large dictionary.


"""

import os
import sys
import time
import socket
import random
import string
from pathlib import Path
import multiprocessing as mp
import subprocess as sp
from uuid import uuid4


sys.path.append("/home/mot/py/")


from mpyx import EZ, F, Stamp, Sink, As, By, Datagram
from mpyx.Vid import FFmpeg
import numpy as np

import fcntl
import shlex


from skvideo.io import FFmpegReader, FFmpegWriter
from functools import reduce

dictionary = None


class FrameData(Datagram):

    def initialize(self, experiment_uuid, segment_uuid, number):
        self.experiment_uuid = experiment_uuid
        self.segment_uuid = segment_uuid
        self.number = number


def main():

    n_frames = 100
    pipe(n_frames)


def make_frame(number):
    return FrameData(uuid4(), uuid4(), number)


class Timeit(object):
    import time

    startTime = time.time()

    @staticmethod
    def start():
        Timeit.startTime = time.time()

    @staticmethod
    def end():
        print(" `-> Took {} seconds.".format(time.time() - Timeit.startTime))


class RandomFrameEmitterPipe(F):

    def setup(self, n_frames):
        for i in range(n_frames):
            frame = make_frame(i)
            self.put(frame)


class SetAProp1(F):

    def do(self, frame):
        frame.raw = np.random.random((1729, 2336))
        self.put(frame)


class SetAProp2(F):

    def do(self, frame):
        raw = frame.raw
        proc = raw / 2
        frame.processed = proc
        self.put(frame)


class Cleaner(F):

    def do(self, frame):
        frame.clean()


def pipe(n_frames):
    """
    Use normal python provided queues.
    """
    ez = EZ(
        RandomFrameEmitterPipe(n_frames),
        SetAProp1(),
        SetAProp2(),
        Cleaner(),
        As(1, Sink),
    )
    print("Timing multiprocess pipes with Datagram")
    Timeit.start()
    ez.start().join()
    Timeit.end()


if __name__ == "__main__":
    main()
