"""
Process.py -- An experimental library of python multiprocessing.
"""
from queue import Empty, PriorityQueue
import multiprocessing as mp
import time
import asyncio
import traceback
import random
import os

"""

Synopsis
========

Examples
========

    
>>> import numpy as np
>>> from lib.Process import F, Print
>>> 
>>> class SumAndAdd(F):
>>>     def setup(self, x):
>>>         self.x = x
>>>         self.sum = 0
>>>     def do(self, n):
>>>         self.sum += n
>>>         self.push(self.x + n)
>>>     def teardown(self):
>>>         self.push([self.sum])
>>>
>>> Iter([1,2,3]).into(PointlessAddition(-1)).into(Print()).execute()
0
1
2
[6]


"""


class Zueue(mp.Process):
    """
    A few useful hooks, latches, and queues.
    I am a Process.
    """
    
    
    # Override me
    def setup(self, *args, **kwargs):
        pass
    
    # Override me
    def do(self, data):
        self.push(data)
    
    # Override me
    def teardown(self): 
        pass
    
    
    def __init__(self, *args, **kwargs):
        "I am not yet a Process."
        "I have not started yet."
        super(Zueue, self).__init__()
        "I am now an unstarted Process."
        
        self.queues_in = []
        self.queues_out = []
        
        self.stop_event = mp.Event()
        self.start_event = mp.Event()
        self._into = []
        self._infrom = []
        self.queue_out_idx = 0
        
        self.push_method = "distribute"
        # todo: each queue should know if it should be broadcast or ditributed.
        
        self.args = args
        self.kwargs = kwargs
        if not 'env' in self.kwargs:
            self.env = {}
        else:
            self.env = self.kwargs["env"]
            del self.kwargs["env"]
    
    ##################
    # Input / Output #
    ##################
    
    def push(self, item):
        "Like .put(item), but with behaviour."
        if len(self.queues_out) > 0:
            
            if item is None:
                    data = None
            else:
                data = (self.meta.copy(), item)
            
            if self.push_method == "distribute":
                
                self.queue_out_idx = (1 + self.queue_out_idx) % len(self.queues_out)
                self.queues_out[self.queue_out_idx].put(data)
            
            elif self.push_method == "split":
            
                for qo in self.queues_out:
                    qo.put(data)
            else:
                pass # /dev/null
            
    
    def pull(self):
        "Like .get(), but with conditions."
        "Sets self.meta"
        if len(self.queues_in) == 0:
            "/dev/zero"
            self.meta = {}
            return None
        
        data = False
        while data is False and len(self.queues_in) > 0:
            "This is a rickety engine."
            
            rm_list = [] # Queues evaporate when they push None.
            random.shuffle(self.queues_in) # There is no assumed depenance 
                                           # between queues_(in|out) and _in(from:to)
            
            data = False
            "False is not None"
            
            for i, qi in enumerate(self.queues_in):

                try: 
                    data = qi.get_nowait()
                except Empty:
                    continue
                
                if data is None:
                    rm_list.append(i)
                    data = False
                else:
                    break
            
            for index in sorted(rm_list, reverse=True):
                del self.queues_in[index]
            
            self.sleep()

        if data is False:
            self.meta = {}
            return None
        else:
            self.meta, item = data
            return item
    
    #############
    # Lifecycle #
    #############
    
    def execute(self):
        self.start()
        [ep.join() for ep in self.endpoints()]
    
    # Called after init, before first
    # Creates new process
    def start(self):
        if not self.started():
            self.start_event.set()
            self.beforeStart()
            super(Zueue, self).start()
            [infrom.start() for infrom in self._infrom]
            [into.start() for into in self._into]
            self.afterStart()
    
    
    
    def beforeStart(self):
        self.parent_env = os.environ.copy()
        for k, v in self.env.items():
            os.environ[k] = v
    
    def afterStart(self):
        for k, v in self.env.items():
            if k in self.parent_env:
                os.environ[k] = self.parent_env[k]
            else:
                del os.environ[k]
    
     
    def run(self):
        self.meta = {}
        self.setup(*self.args, **self.kwargs)
        while True:
            if self.stopped():
                return self.shutdown()
            else:
                try:
                    item = self.pull()
                    if item is None:
                        self.stop()
                    else:
                        self.do(item)
                except Exception as e:
                    traceback.print_exc()
                    return e
            self.sleep()
    
    
    def started(self):
        return self.start_event.is_set()
    
    
    # [Lifecycle] setup(self, *args, **kwargs)
    
    # [Lifecycle] do(self, item)
    
        
    def stop(self):
        self.stop_event.set()
        
    # [Lifecycle] teardown(self)
    
    def shutdown(self):
        [self.push(None) for i in range(len(self._into))]
        return self.teardown()

    
    def stopped(self):
        return self.stop_event.is_set()
    
    ################
    # Process Flow #
    ################
    
    def print(self):
        return self.into(Print())
    
    def into(self, zueues):
        
        zueues = ZueueList(listify(zueues))
        self.ensureOutputQueue()
        
        for z in zueues:
            self._into.append(z)
            z._infrom.append(self)
            z.queues_in.extend(self.queues_out)
        
        return zueues
    
    def infrom(self, zueues):
        zueues = ZueueList(listify(zueues))
        self._infrom.extend(zueues)
        
        for z in zueues:
            z.ensureOutputQueue()
            z._into.append(self)
            self.queues_in.extend(z.queues_out)
        return self
    
    
    def sequence(self, key = "seq_id"):
        return self.into(StartSeq(key))
    
    def order(self, key = "seq_id"):
        return self.into(EndSeq(key))
    
    def split(self, zueues):
        
        self.push_method = "split"
        
        zueues = ZueueList(listify(zueues))
        
        for z in zueues.entrypoints():
            q = mp.Queue(16)
            self._into.append(z)
            self.queues_out.append(q)
            z._infrom.append(self)
            z.queues_in.append(q)
        return zueues
    
    def merge(self, key = "seq_id", n = None):
        n = len(set(self._infrom)) if n is None else n
        return self.into(MergeSeq(key, n))
    
    
    ###########
    # Helpers #
    ###########
    
    def entrypoints(self):
        if len(self._infrom) > 0:
            return list(set(flatten([node.entrypoints() for node in self._infrom])))
        else:
            return [self]
    
    def endpoints(self):
        if len(self._into) > 0:
            return list(set(flatten([node.endpoints() for node in self._into])))
        else:
            return [self]
    

    def sleep(self, wait = 0.01):
        return time.sleep(wait)
    
    def ensureOutputQueue(self):
        if len(self.queues_out) == 0:
                self.queues_out.append(mp.Queue(16))
    


class ZueueList(list):
    "A collection of Process"
    
    # Lifecycle
    
    def execute(self):
        [z.execute() for z in self]

    def start(self):
        [z.start() for z in self]
    
    # Process Flow

    def print(self, pre = None, post = None):
        return self.into(Print(pre, post))
    
    def into(self, zueues): 
        return ZueueList(flatten([z.into(zueues) for z in self]))
        
    def infrom(self, zueues): 
        return ZueueList(flatten([z.infrom(zueues) for z in self]))

    def sequence(self, key = "seq_id"):
        return self.into(StartSeq(key))
    
    def order(self, key = "seq_id"):
        return self.into(EndSeq(key))
    
    def split(self, zueues): 
        return ZueueList(flatten([z.split(zueues) for z in self]))
    
    def merge(self, key = "seq_id", n = None):
        return self.into(MergeSeq(key, n))

    # Helpers
    
    def entrypoints(self):
        return list(set(flatten([z.entrypoints() for z in self])))
        
    def endpoints(self):
        return list(set(flatten([z.endpoints() for z in self])))
    

class IncomingQueueList():
    def __init__(self):
        self.queues = []
        
    def append(self, q):
        self.queues.append(q)
        
    def extend(self, qs):
        self.queues.extend(qs)
        
    def get(self):
        if len(self.queues) == 0:
            "/dev/zero"
            return None
        
        data = False
        while data is False and len(self.queues_in) > 0:
            "This is a rickety engine."
            
            rm_list = [] # Queues evaporate when they push None.
            random.shuffle(self.queues) # There is no assumed depenance 
                                        # between queues_(in|out) and _in(from:to)
            data = False # False is not None
            
            for i, qi in enumerate(self.queues):

                try: 
                    data = qi.get_nowait()
                except Empty:
                    continue
                
                if data is None:
                    rm_list.append(i)
                    data = False
                else:
                    break
            
            for index in sorted(rm_list, reverse=True):
                del self.queues[index]
            
            time.sleep(0.1)

        if data is False:
            return None
        else:
            return data
        
class OutgoingQueueList():
    def __init__(self):
        self.queues = {
            "distributed": [],
            "broadcasted": []
        }
        self.current_idx = 0
        
    def append(self, q = None, kind = "distributed"):
        q = mp.Queue(16) if q is None else q
        self.queues[kind].append(q)

    def extend(self, qs = [], kind = "distributed"):
        self.queues[kind].extend(qs)
    
    def put(self, data = None):
        
        if len(self.queues["distributed"]) > 0:
            self.queues["distributed"][self.current_idx].put(data)
            self.current_idx = (1 + self.current_idx) % len(self.queues["distributed"])
        
        for queue_out in self.queues["broadcasted"]:
                qo.put(data)
            
        
        
        


class F(Zueue):
    "Experimental"
    def async(self, coroutine):
        return asyncio.new_event_loop().run_until_complete(coroutine)
    

def By(n, f, *args, **kwargs):
    return ZueueList([f(*args, **kwargs) for _ in range(n)])



class Iter(F):
    
    def setup(self, iterable):
        for x in iterable:
            self.push(x)
        self.stop()


class Print(F):
    
    def setup(self, pre = "", post = ""):
        self.pre, self.post, = pre, post
        
    def do(self, item):
        if self.pre and self.post:
            print(self.pre, item, self.post)
        elif self.pre:
            print(self.pre, item)
        elif self.post:
            print(item, self.post)
        else:
            print(item)
        self.push(item)


class Delay(F):
    
    def setup(self, c = None, b = None):
        self.c = 1. if c is None else c
        self.b = 0. if b is None else 1
        
    def do(self, item):
        time.sleep(self.c * random.random() + self.b)
        self.push(item)


class StartSeq(F):
    
    def setup(self, key = "seq_id"):
        self.key = key
        self.seq_id = 0
        
    def do(self, item):
        self.meta[self.key] = self.seq_id
        self.push(item)
        self.seq_id += 1
        
        
    
class EndSeq(F):
    
    def setup(self, key = "seq_id"):
        self.pq = PriorityQueue() 
        self.key = key
        self.seq_id = 0
        
    def do(self, item):
        self.pq.put((self.meta[self.key], item))
        for _ in range(self.pq.qsize()): # todo: optimize
            p, item = self.pq.get()
            if p == self.seq_id:
                self.meta[self.key] = self.seq_id
                self.push(item)
                self.seq_id = self.seq_id + 1
            else:
                self.pq.put((p, item))
        

class MergeSeq(F):
    def setup(self, key = "seq_id", n = None):
        self.pq = PriorityQueue() 
        self.key = key
        self.seq_id = 0
        self.n = len(set(self._infrom)) if n is None else n
        
    def do(self, item):
        self.pq.put((self.meta[self.key], item))
        
        if self.pq.qsize() >= self.n:
            for _ in range(self.pq.qsize()): # todo: optimize
                if self.pq.qsize() >= self.n:
                    keep = []
                    back = []
                    for i in range(self.n):
                        p, item = self.pq.get()
                        
                        if p == self.seq_id:
                            keep.append(item)
                        else:
                            back.append((p, item))
                    
                    if len(keep) == self.n:
                        self.meta[self.key] = self.seq_id
                        self.push(keep)
                        self.seq_id += 1
                    else:
                        for item in keep:
                            self.pq.put((self.seq_id, item))
                            
                    for data in back:
                        self.pq.put(data)



def flatten(to_flatten):
    """Given a list, possibly nested to any level, return it flattened."""
    # modified from http://code.activestate.com/recipes/578948-flattening-an-arbitrarily-nested-list-in-python/
    flattened = []
    for item in to_flatten:
        if isinstance(item, list):
            flattened.extend(flatten(item))
        else:
            flattened.append(item)
    return flattened
    
    
    
def listify(item = None):
    "Returns pretty much anything thrown at this as a list"
    if item is None:
        return []
    elif isinstance(item, list):
        return item
    elif isinstance(item, (set, tuple)):
        return list(item)
    elif isinstance(item, dict):
        return list(item.values())
    else:
        return [item]
        
        