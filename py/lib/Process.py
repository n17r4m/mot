# Deprecrated. delete me soon.

from lib.util.store_args import store_args

import multiprocessing as mp
import time
import traceback

class Zueue(mp.Process):
    @store_args
    def __init__(self, queue_in = mp.Queue(), queue_out = mp.Queue()):
        super(Z, self).__init__()
        self.stop_event = mp.Event()

    def run(self):
        self.setup()
        while True:
            if self.stopped():
                return self.close()
            else:
                try:
                    data_in = self.queue_in.get()
                    if data_in is None:
                        self.stop()
                    else:
                        
                        data_out = self.action(data_in)
                        self.queue_out.put(data_out)
                except Exception as e:
                    traceback.print_exc()
                    return e
            self.pause()
    
    def setup(self):
        pass
    
    def pause(self):
        return time.sleep(0.001)

    def close(self):
        self.proc.stdin.close()
        self.proc.wait()
        self.queue_out.put(None)
        
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()


class Xplitter(Zueue):
    @store_args
    def __init__(self, queue_in, queue_out, n_in = 1, n_out = 1):
        super(Ysplitter, self).__init__(queue_in, queue_out)
        self.pq = queue.PriorityQueue()
    
    def run(self):
        self.setup()
        seq = 0
        noneCount = 0
        while True:
            if self.stopped():
                return self.close()
            data = self.input_queue.get()
            if data is None:
                noneCount += 1
                if noneCount >= self.n_in:
                    self.stop()
                continue
            
            self.pq.put(data)
            p, out = self.pq.get()
            
            if p == seq:
                self.queue_out.put(out)
                seq += 1
            else:
                self.pq.put((p, out))
                
    def close(self):
        if not self.pq.empty():
            print("Warning: Non empty Y queue", self.pq.qsize())
        for i in range(n_out):
            self.queue_out.put(None)