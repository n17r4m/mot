
from lib.util.store_args import store_args
from queue import Empty

import multiprocessing as mp
import time
import traceback
import random
import traceback

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
    
    def push(self, data):
        
        if len(self.queues_out) > 0:
            self.queue_out_idx = (1 + self.queue_out_idx) % len(self.queues_out)
            self.queues_out[self.queue_out_idx].put(data)
        

            
    
    def pull(self, force_list = False):
        
        if len(self.queues_in) == 0:
            return None
        
        item = False
        
        
        while item is False and len(self.queues_in) > 0:
            
            rm_list = []
            random.shuffle(self.queues_in)
            
            for i, qi in enumerate(self.queues_in):
                
                try: 
                    item = qi.get_nowait()
                except Empty:
                    continue
                
                if item is None:
                    rm_list.append(i)
                    item = False
                else:
                    break
            
            for index in sorted(rm_list, reverse=True):
                del self.queues_in[index]
            
            self.sleep()

        if item is False:
            return None
        else:
            return item
            
    
    def start(self):
        if not self.started():
            self.start_event.set()
            super(Zueue, self).start()
            [infrom.start() for infrom in self._infrom]
            [into.start() for into in self._into]
            
                
    def execute(self):
        self.start()
        [ep.join() for ep in self.endpoints()]
    
    def endpoints(self):
        if len(self._into) > 0:
            return list(set(flatten([node.endpoints() for node in self._into])))
        else:
            return [self]
    
    def startpoints(self):
        if len(self._infrom) > 0:
            return list(set(flatten([node.startpoints() for node in self._infrom])))
        else:
            return [self]
    
    def started(self):
        return self.start_event.is_set()
    
    def run(self):
        self.setup()
        while True:
            if self.stopped():
                return self.shutdown()
            else:
                try:
                    data_in = self.pull()
                    if data_in is None:
                        self.stop()
                    else:
                        self.do(data_in)
                except Exception as e:
                    traceback.print_exc()
                    return e
            self.sleep()
    
    # Override me
    def do(self, data):
        self.push(data)
    
    # Override me
    def setup(self):
        pass
    
    # Override me
    def teardown(self):
        pass
    
    def sleep(self, wait = 0.01):
        return time.sleep(wait)
    
    def into(self, zueues):
        zueues = listify(zueues)
        if len(self.queues_out) == 0:
            self.queues_out.append(mp.Queue(16))
        [zueue.infrom(self) for zueue in zueues]
        return ZueueList(zueues)
    
    def infrom(self, zueues):
        zueues = listify(zueues)
        self._infrom.extend(zueues)
        [z._into.append(self) for z in zueues]
        for z in zueues:
            if len(z.queues_out) == 0:
                z.queues_out.append(mp.Queue(16))
            self.queues_in.extend(z.queues_out)
        return ZueueList(zueues)
    
    def shutdown(self):
        [self.push(None) for i in range(len(self._into))]
        return self.teardown()
    
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()



class ZueueList(list):
    def into(self, zueues): 
        return ZueueList(flatten([z.into(zueues) for z in self]))
        
    def infrom(self, zueues): 
        return ZueueList(flatten([z.infrom(zueues) for z in self]))
        
    def execute(self):
        self[0].execute()
    def start(self):
        self[0].start()




class Xplitter(Zueue):
    @store_args
    def __init__(self, queue_in = mp.Queue(256), queue_out = mp.Queue(16), n_in = 1, n_out = 1):
        super(Xsplitter, self).__init__(queue_in, queue_out)
    
    def setup(self):
        self.pq = queue.PriorityQueue() 
        self._seq = 0
        self._nones = 0
    
    def do(self, pqdata):
        if pqdata is None:
            noneCount += 1
            if noneCount >= self.n_in:
                self.stop()
            return
        else:
            p, data = pqdata
            if p == seq:
                self.queue_out.put(out)
                seq += 1
            else:
                self.pq.put(pqdata)
                p, data = self.pq.get()
                if p == seq:
                    self.queue_out.put(out)
                    seq += 1
                else:
                    self.pq.put((p, data))
            
    def teardown(self):
        if not self.pq.empty():
            print("Warning: Non empty queue in Xplitter: " + str(self.pq.qsize()))
        for i in range(n_out):
            self.queue_out.put(None)



def flatten(lis):
    """Given a list, possibly nested to any level, return it flattened."""
    # http://code.activestate.com/recipes/578948-flattening-an-arbitrarily-nested-list-in-python/
    new_lis = []
    for item in lis:
        if isinstance(item, list):
            new_lis.extend(flatten(item))
        else:
            new_lis.append(item)
    return new_lis
    
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