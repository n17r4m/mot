# Deprecrated. delete me soon.

import time
import multiprocessing as mp

class Plug(mp.Process):
    def __init__(self, inputs = mp.Queue(), outputs = mp.Queue()):
        super(Plug, self).__init__()
        self.inputs, self.outputs = inputs, outputs
        self.stop_event = mp.Event()
    
    def run(self):
        while True:
            if self.stopped()
                self.outputs.put(None)
                break
            self.action()
        
    # Override me!
    def action(self):
        self.outputs.put(self.inputs.get())
        
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()


class Sequencer(Plug):
    def __init__(self, inputs = mp.Queue(), outputs = mp.Queue(), 
                     n_inputs = 1,        n_outputs = 1,          start_at = 0):
        # expects (sequence_info, payload) as inputs, sends payload as outputs.
        super(Sequencer, self).__init__(inputs, outputs)
        self.n_inputs = n_inputs
        self.start_at = start_at
        
    def run(self):
        pq = queue.PriorityQueue()
        current_seq = self.start_at
        noneCount = 0
        while True:
            if self.stopped():
                break
            packet = self.inputs.get()
            if packet is None:
                noneCount += 1
                if noneCount >= self.n_inputs:
                    break
                continue
            pq.put(packet);
            packet_seq, payload = pq.get()
            if packet_seq == current_seq:
                self.outputs.put(payload)
                current_seq += 1
            else:
                pq.put(packet)
        
        for _ in range(self.n_outputs):
            self.output_queue.put(None)
            

class Transaction(Plug):
    def __init__(self, inputs= mp.Queue(), exceptions = mp.Queue()):
        super(Transaction, self).__init__(inputs, exceptions)
        self.commit_event = multiprocessing.Event()
        
    def run(self):
        return asyncio.new_event_loop().run_until_complete(self.tx_loop())
        
    # dun know if this works or not.. todo: test.
    async def tx_loop(self, queue):
        from lib.Database import Database
        tx, transaction = await Database().transaction()
        while True:
            if not self.stopped():
                sql_drop = self.inputs.get()
                if sql_drop is None:
                    self.commit()
                else:
                    method, query, args = sql_drop
                    try:
                        await getattr(tx, method)(query, *args)
                    except Exception as e:
                        self.outputs.put(e)
            else:
                if self.commit_event.is_set():
                    await transaction.commit()
                else:
                    await transaction.rollback()
                break
    
    def commit(self):
        self.commit_event.set()
        self.stop()
