from mpyx import EZ, As, By, F
from mpyx import Serial, Parallel, Broadcast, S, P, B
from mpyx import Iter, Const, Print, Stamp, Map, Filter, Batch, Seq, Zip, Read, Write
from mpyx import Datagram

from uuid import uuid4
import numpy as np
import pickle
import os


class Data:

    def save_gen_fname(self, key):
        return "/tmp/mpyx_datagram_{}_{}.npy".format(key, str(uuid4()))

    def save(self, key, data):

        if not hasattr(self, "np_file_store"):
            # potential todo: https://stackoverflow.com/questions/394770/override-a-method-at-instance-level
            # rewrite this instance's save function to skip this check in the future.
            self.np_file_store = {}

        if key in self.np_file_store:
            fname = self.np_file_store[key]
        else:
            fname = self.save_gen_fname(key)
        np.save(fname, data)
        self.np_file_store[key] = fname

    def load(self, key):
        try:
            return np.load(self.np_file_store[key], "r")
        except ValueError as e:
            return np.load(self.np_file_store[key])

    def furcate(self):
        clone = pickle.loads(pickle.dumps(self))
        if hasattr(clone, "np_file_store"):
            for key, fname in clone.np_file_store.items():
                new_fname = self.save_gen_fname(key)
                os.link(fname, new_fname)
                clone.np_file_store[key] = new_fname
        return clone
    
    
    def delete(self, key):
        os.remove(self.np_file_store[key])
        del self.np_file_store[key]
    
    def clean(self):
        if hasattr(self, "np_file_store"):
            for key, fname in self.np_file_store.items():
                os.remove(fname)


class D(Data):

    def __init__(self):
        self.a = None


async def main(args):

    d = D()
    print(d.a, "Should be None")

    d.a = 4
    print(d.a, "Should be 4")

    d.save("data1", np.random.random((1, 2, 2, 1)))

    e = d.furcate()

    e.save("data2", np.random.random((100, 100, 100, 3)))

    try:
        print("d", d.a)
        print("d", d.load("data1"))
    except Exception as x:
        print(x)

    try:
        print("e", e.a)
        print("e", e.load("data1"))
    except Exception as x:
        print(x)

    d.clean()
    e.clean()

    # todo: test with multiprocessing.
    class Mp(Data):
        def __init__(self, aloha = 2)
            self.aloha = None
            
    class Gen(F):
        def none():
            pass
    
        