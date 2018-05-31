"""
Test the performance of several inter-process transfer methods on a large dictionary.


"""
#!/usr/bin/python

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


from mpyx import EZ, F, Stamp, Sink, As, By
from mpyx.Vid import FFmpeg
import numpy as np

import fcntl
import shlex


from skvideo.io import FFmpegReader, FFmpegWriter
from functools import reduce

dictionary = None


def main():

    n_frames = 1000
    frames_s = (1729, 2336, 1)

    # print("Making 'dictionary' with {} frames".format(n_frames))
    Timeit.start()
    global dictionary
    dictionary = makeDict(n_frames)
    print("Loaded 'dictionaries' for {} frames".format(len(dictionary)))
    Timeit.end()

    foos = [pipe, ramdisk1]
    a = np.array(range(len(foos)))
    np.random.shuffle(a)
    for i in a:
        # dashit(time.time())
        foos[i](n_frames)


def makeDict(n_frames):
    dictionary = []

    if False:
        n_keys = 100
        len_values = 333333
        d = dict()
        # Keys
        for j in range(n_keys):
            d[j] = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=len_values)
            )
        dictionary = [d] * n_frames

    if True:
        import os, pickle

        for name in os.listdir("/home/mot/tmp/props"):
            d = None
            with open("/home/mot/tmp/props/" + name, "rb") as f:
                d = pickle.load(f)
            dictionary.append(d)
        # dictionary = dictionary * (n_frames // len(dictionary))

    return dictionary


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
    """
    Use normal python provided queues.
    """
    pickled = RandomFrameEmitterPipe(n_frames)
    print("Timing decode time with multiprocess pipes")
    Timeit.start()
    EZ(pickled, As(1, Sink)).start().join()
    Timeit.end()


def ramdisk1(n_frames):
    ramdisk = RandomFrameEmitterRamdisk1(n_frames)
    print("Timing decode time with ramdisk + numpy.save")
    Timeit.start()
    EZ(ramdisk, As(1, RDRead)).start().join()
    Timeit.end()


class RandomFrameEmitterPipe(F):

    def setup(self, n_frames):
        global dictionary
        for d in dictionary:
            self.put(d)


class RandomFrameEmitterRamdisk1(F):

    def setup(self, n_frames):
        global dictionary
        for d in dictionary:
            uuid = uuid4()
            np.save("/tmp/dict_" + str(uuid), d)
            self.put(str(uuid))


class RDRead(F):

    def initialize(self):
        self.output_shape = (1729, 2336, 1)

    def do(self, uuid):
        frame = np.load("/tmp/dict_" + uuid + ".npy")
        os.unlink("/tmp/dict_" + uuid + ".npy")


if __name__ == "__main__":
    main()


"""
Making 'dictionary' with 100 frames
 `-> Took 11.112484455108643 seconds.
Timing decode time with ramdisk + numpy.save
 `-> Took 2.551436185836792 seconds.
Timing decode time with multiprocess pipes
 `-> Took 18.7547709941864 seconds.
 
Making 'dictionary' with 100 frames
 `-> Took 10.370168685913086 seconds.
Timing decode time with multiprocess pipes
 `-> Took 32.50079917907715 seconds.
Timing decode time with ramdisk + numpy.save
 `-> Took 2.5101637840270996 seconds.

Making 'dictionary' with 100 frames
 `-> Took 10.932108402252197 seconds.
Timing decode time with ramdisk + numpy.save
 `-> Took 2.5503485202789307 seconds.
Timing decode time with multiprocess pipes
 `-> Took 22.54086184501648 seconds.

#### With real data from region props dictionary
Loaded 'dictionaries' for 118 frames
 `-> Took 1.8345472812652588 seconds.
Timing decode time with ramdisk + numpy.save
 `-> Took 5.29124903678894 seconds.
Timing decode time with multiprocess pipes
 `-> Took 6.852595567703247 seconds.
 
Loaded 'dictionaries' for 118 frames
 `-> Took 2.042605400085449 seconds.
Timing decode time with multiprocess pipes
 `-> Took 8.970940351486206 seconds.
Timing decode time with ramdisk + numpy.save
 `-> Took 4.542385578155518 seconds.

Loaded 'dictionaries' for 118 frames
 `-> Took 1.2862184047698975 seconds.
Timing decode time with ramdisk + numpy.save
 `-> Took 4.43463659286499 seconds.
Timing decode time with multiprocess pipes
 `-> Took 6.31967568397522 seconds.

Loaded 'dictionaries' for 118 frames
 `-> Took 1.285156488418579 seconds.
Timing decode time with ramdisk + numpy.save
 `-> Took 4.323694944381714 seconds.
Timing decode time with multiprocess pipes
 `-> Took 6.647335529327393 seconds.
 
Loaded 'dictionaries' for 118 frames
 `-> Took 2.031873941421509 seconds.
Timing decode time with multiprocess pipes
 `-> Took 8.146191835403442 seconds.
Timing decode time with ramdisk + numpy.save
 `-> Took 4.400641679763794 seconds.

"""
