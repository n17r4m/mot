
import numpy as np
import time
from lib.Process import F, Xplitter, Split, Merge, By



class Delay(F):
    def setup(self, c = None, b = None):
        self.c = 1. if c is None else c
        self.b = 0. if b is None else 1
    def do(self, data):
        time.sleep(self.c * np.random.uniform() + self.b)
        self.push(data)


class Ten(F):
    def setup(self):
        for i in range(10):
            self.push(i)
        self.stop()

class Times2(F):
    def do(self, n):
        self.push(n*n)
    
class Print(F):
    def do(self, data):
        print(data)
        self.push(data)

    


async def main(args):
    
    f = (
            Ten() # A temporal pachinko machine
            .into(Split())
            .into(By(2, Delay, 2))
            .into(By(2, Delay, 2))
            #.into(Merge())
            .into(Print())
            #.into(Split())
            .into([Delay(1, 2), Delay(0.1), Delay(0.1), Delay(0.1)])
            .into(By(3, Delay, 0.5, b=10.))
            .into(Merge())
            .into(Print())
        )
        
    f.execute()