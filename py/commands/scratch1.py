

import time
from lib.Process import F, Iter, Print, Delay, By
from lib.Database import DBReader, DBWriter
from multiprocessing import Queue
import numpy as np



class Mul(F):
    def setup(self, m = 2):
        self.m = m
    def do(self, n):
        self.push(n * self.m)

class Pow(F):
    def setup(self, e = 2):
        self.e = e
    def do(self, n):
        self.push(n ** self.e)
    

class PrintMeta(F):
    def setup(self, pre = ""):
        self.pre = pre
    def do(self, n):
        print(self.pre, n, self.meta)
        self.push(n)
    
class TestWriter(F):
    def setup(self, wq):
        self.wq = wq
        self.count = 0
    def do(self, item):
        self.wq.push(("execute", """
            INSERT INTO Test (name, value) VALUES ($1, $2)
        """, (str(self.count), item)))
        self.push(item)
        self.count += 1

async def main(args):
    
    test = 1
    
    

    if test == -1:
        
        writer = DBWriter()
        wq = writer.input()
        writer.start()
        
        
        print("db started")
        
        (   Iter(["one", "two", "three"])
            .into(TestWriter(wq))
            .print()
            .into(Mul(10))
            .into(TestWriter(wq))
            .print()
            .execute())
        
        print("proc finished")
        
        writer.commit()
        wq.push(None)
        
        print("done")
        
    
    if test == 0:
        
        (   DBReader("SELECT * FROM Experiment")
            .map(lambda x: [str(x["experiment"]), x["name"]])
            .print()
            .execute())
        
    if test == 1:
    
        (   Iter(range(1, 11))
            .sequence()
            .split([Mul(i) for i in range(1, 11)])
            .merge()
            .print()
            .execute())
        
        
    if test == 2:
        
        (   Iter([2,3,4])
            .sequence()
            .split([
                F().into(By(3, Delay)).order(),
                Pow().into(Delay()).order(),
                Pow().into(By(2, Pow)).into(By(5, Delay)).order()
            ])
            .merge()
            .print()
            .execute())
            
    if test == 3:
        
        (   Iter(range(10)) # A pachinko machine
            .sequence()
            .into(By(10, Delay))
            .into(By(10, Delay))
            .into(By(10, Pow))
            .into(By(10, Delay))
            .order()
            .print()
            .execute())
        
    
   