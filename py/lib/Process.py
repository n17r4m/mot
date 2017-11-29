

from queue import Empty, PriorityQueue

import multiprocessing as mp
import time
import traceback
import random
import traceback
import types


class Zueue(mp.Process):
    
    def __init__(self, queues_in = None, queues_out = None):
        super(Zueue, self).__init__()
        
        self.queues_in = listify(queues_in)
        self.queues_out = listify(queues_out)
        
        self.stop_event = mp.Event()
        self.start_event = mp.Event()
        self._into = []
        self._infrom = []
        self.queue_out_idx = 0
        
        self.push_method = "distribute"
    
    def push(self, item):
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
            
    
    def pull(self):
        
        if len(self.queues_in) == 0:
            self.meta = {}
            return None
        
        data = False
        
        
        while data is False and len(self.queues_in) > 0:
            
            rm_list = []
            random.shuffle(self.queues_in)
            data = False
            
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
            
    # Called after init, before first
    # Creates new process
    def start(self):
        if not self.started():
            self.start_event.set()
            self.first()
            super(Zueue, self).start()
            [infrom.start() for infrom in self._infrom]
            [into.start() for into in self._into]
    
    
        
    def execute(self):
        self.start()
        [ep.join() for ep in self.endpoints()]
    
    
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
    
    
    
    def starting(self):
        self.setup()
    
    def started(self):
        return self.start_event.is_set()
    
    def run(self):
        self.meta = {}
        self.starting()
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
    
    
    # Override me
    # Called after start/execute, before setup
    def first(self):
        pass
    
    # Override me
    # Called after first, before do
    def setup(self, *args, **kwargs):
        pass
    
    # Override me
    # Called after setup, until teardown
    def do(self, data):
        self.push(data)
    
    # Override me
    # Called after do completes
    def teardown(self): 
        pass
    
    def sleep(self, wait = 0.01):
        return time.sleep(wait)
    
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
    
    def sequence(self, key = "seq_id"):
        return self.into(StartSeq(key))
    
    def order(self, key = "seq_id"):
        return self.into(EndSeq(key))
    
    def ensureOutputQueue(self):
        if len(self.queues_out) == 0:
                self.queues_out.append(mp.Queue(16))
    
    def shutdown(self):
        [self.push(None) for i in range(len(self._into))]
        return self.teardown()
    
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()


class ZueueList(list):
    
    def print(self):
        return self.into(Print())
    
    def into(self, zueues): 
        return ZueueList(flatten([z.into(zueues) for z in self]))
        
    def infrom(self, zueues): 
        return ZueueList(flatten([z.infrom(zueues) for z in self]))
    
    def split(self, zueues): 
        return ZueueList(flatten([z.split(zueues) for z in self]))
    
    def merge(self, key = "seq_id", n = None):
        return self.into(MergeSeq(key, n))
    
    def sequence(self, key = "seq_id"):
        return self.into(StartSeq(key))
    
    def order(self, key = "seq_id"):
        return self.into(EndSeq(key))
    
    def entrypoints(self):
        return list(set(flatten([z.entrypoints() for z in self])))
        
    def endpoints(self):
        return list(set(flatten([z.endpoints() for z in self])))
    
    def execute(self):
        [z.execute() for z in self]

    def start(self):
        [z.start() for z in self]
    
    





def flatten(to_flatten):
    """Given a list, possibly nested to any level, return it flattened."""
    # modified from http://code.activestate.com/recipes/578948-flattening-an-arbitrarily-nested-list-in-python/
    
    new_lis = []
    for item in to_flatten:
        if isinstance(item, list):
            new_lis.extend(flatten(item))
        else:
            new_lis.append(item)
    return new_lis
    
    # return  [*(flatten(item) if isinstance(item, list) else item) for item in to_flatten]
    
    
    
def listify(item = None):
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
        
        



class F(Zueue):
    
    def __init__(self, *args, **kwargs):
        super(F, self).__init__()
        self.args = args
        self.kwargs = kwargs
        pass
    
    def starting(self):
        self.setup(*self.args, **self.kwargs)



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


