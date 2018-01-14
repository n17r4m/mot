from mpyx.Process import F
import numpy as np

class SimpleVideoIter(F):
    def setup(self, fname):
        from mpyx.Video import Video
        self.video = Video(fname)
        for frame in self.video:
            self.push(frame)
        self.stop()

#todo: pipe all videos.

class MagicPixels(F):
    def setup(self, fname, num_magic = 8):
        self.valuesOf = [[]] * num_magic
        self.num = num
    def do(self, frame):
        
        [self.valuesOf[:] #some magic enumeration]


success = []
failure = []


try: # .results()
    
    test = ["Hello!", "World!"]
    x = list(Iter(test).items())
    assert(x == test)
    
except Exception as e: failure.append((test, e))
else:                  success.append(test)

