"""
Compute a background image from a video sequence.


Author: Martin Humphreys / Kevin Gordon
"""

import numpy as np
import sys
import multiprocessing
from itertools import repeat
from lib.Video import Video


def extractor_worker(video_file, n):
    video = Video(video_file)
    max_bg = np.zeros(video.shape)
    for i in range(n, n+20):
        frame  =  video.frame(i)
        max_bg =  np.maximum(frame, max_bg)
    return max_bg


class Background(object):

    def __init__(self, video):
        self.video = Video(video)
        self.bg = None
        self.e = sys.float_info.min
        
        
    def extract(self, n = 100):  
        if self.bg is None:
            print("Extracting Background...")
            max_bg = np.zeros(self.video.shape)
            
            with multiprocessing.Pool(processes=5) as pool:
                max_bgs = pool.starmap(extractor_worker, zip(
                    repeat(self.video.file), 
                    range(0, n, 20)))
                    
            for bg in max_bgs:
                max_bg = np.maximum(bg, max_bg)
                
            self.bg = max_bg + self.e
        return self.bg
    
    def normalize(self, frame):
        if self.bg is None:
            self.extract()
        return frame / self.bg

    def frame(self, frame_number):
        return (255.0 * np.clip(self.normalize(self.video.frame(frame_number)), 0, 1)).astype("uint8")
        