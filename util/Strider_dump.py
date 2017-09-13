#! /usr/bin/env python
"""
Stride a video frame through the classifier

WIP.

Author: Martin Humphreys
"""


import os
import cv2
import numpy as np
from argparse import ArgumentParser
from models.ClassyVCoder import ClassyVCoder
from FrameGrabber import FrameGrabber
from Crop import Crop

from models.make_parallel import make_parallel
import uuid
import random



SIZE = 64

class Strider(object):
    def __init__(self, opts):
        
        self.verbose = opts.verbose
        self.cropper = Crop(opts.video, ":memory:", {"verbose": opts.verbose})
        
        self.frame = FrameGrabber(opts.video).frame(opts.frame)
        self.frame = self.cropper.normalizer.normalizeFrame(self.cropper.bg, self.frame)
        
        
    def run(self):
        
        if self.verbose:
            print "Generating Crops"
        acc = []
        for y, row in enumerate(self.frame):
            
            for x, point in enumerate(row):
                
                if random.random() < 0.001:
                    
                    tlx = x - (SIZE // 2)
                    tly = y - (SIZE // 2)
                    crop = self.cropper.crop(self.frame, tlx, tly, SIZE, SIZE)
                    if self.verbose:
                        print tlx, tly
                    cv2.imwrite(str(uuid.uuid4()) + ".png", crop)
            
                
    
def build_parser():
    parser = ArgumentParser()
    
    parser.add_argument('video', help='video file')
    parser.add_argument('frame', help='frame number', type=int)
    
    parser.add_argument('-w', "--weights", help='use custom weights file for model', default="ClassyVCoder.h5")
    parser.add_argument('-v', "--verbose", help='print verbose statements while executing', action = 'store_true')    

    return parser


def main(opts):
    Strider(opts).run()
    
if __name__ == '__main__':
    main(build_parser().parse_args())
 


    
        
        