

import time
from lib.Process import F, Iter, Print, Delay, By
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
    


async def main(args):
    
    
    
    (   Iter(range(1, 11))
        .sequence()
        .split([Mul(i) for i in range(1, 11)])
        .merge()
        .print()
        .execute())
    
    """
    (
        Iter([2,3, 4])
        .sequence()
        .split([
            F().into(By(3, Delay)).into(EndSeq()),
            Square().into(Delay()).into(EndSeq()),
            Square().into(By(2, Square)).into(By(5, Delay)).into(EndSeq())
        ])
        .merge(n=3)
        .into(Print())
        .execute()
    )
    """
    """
    print(
        Iter(range(2,3))
        .into(StartSeq())
        .split([
            Print("Original").into(By(5, Delay)).into(EndSeq()), 
            Square().into(Print("Squared")).into(By(5, Delay)).into(EndSeq())
        ]).endpoints())
    """
    
    
    """
    (   Iter(range(6, 8))
        .into(StartSeq()).into(PrintMeta("Source"))
        .split([
            
            By(5, Delay).into(EndSeq()), 
            
            Square()
                .into(By(5, Delay))
                .into(PrintMeta("Squared"))
                .into(EndSeq())
                .into(PrintMeta("PostSeq"))
                
        ])
        .into(MergeSeq(n=2)).into(PrintMeta("After"))
    ).execute()
    """
    
    """
    f = (
            Iter(range(10)) # A pachinko machine
            .into(StartSeq())
            .into(By(10, Delay))
            .into(By(10, Delay))
            .into(By(3, Square))
            .into(By(10, Delay))
            # .into(Print())
            # .into(By(7, Delay, 1))
            # .into([Delay(1, 2), Delay(0.1), Delay(0.1), Delay(0.1)])
            # .into(By(3, Delay, 0.5, b=10.))
            .into(EndSeq())
            .into(Print())
        )
        
    f.execute()
    """
   