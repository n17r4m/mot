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
from models.ClassyVCoderX import ClassyVCoder
from FrameGrabber import FrameGrabber
from Crop import Crop

from models.make_parallel import make_parallel

SIZE = 64
GPUS = 1

class Strider(object):
    def __init__(self, opts):
        
        self.cropper = Crop(opts.video, ":memory:", {"verbose": True})
        
        self.frame = FrameGrabber(opts.video).frame(opts.frame)
        self.frame = self.cropper.normalizer.normalizeFrame(self.cropper.bg, self.frame)
        self.CC = ClassyVCoder()
        self.CC.load(os.path.join(self.CC.path(), opts.weights))
        #self.CC.imageclassifier = make_parallel(self.CC.imageclassifier, GPUS)
        
    def run(self):
        
        print "Generating Crops"
        acc = []
        for y, row in enumerate(self.frame):
            
            crops = []
            
            for x, point in enumerate(row):
                tlx = x - (SIZE // 2)
                tly = y - (SIZE // 2)
                crop = self.cropper.crop(self.frame, tlx, tly, SIZE, SIZE)
                crop = self.CC.preproc(crop)
                crops.append(crop)
            
            crops = np.reshape(crops, (len(crops), SIZE,  SIZE, 1))
            
            acc = np.append(acc, self.CC.imageclassifier.predict(crops, batch_size=584*GPUS/2, verbose=True))
            print "line", y, "/", len(self.frame), " ",  y / len(self.frame), "%"
    
        
        print "accumulator", acc.shape
        
        clas = np.reshape(acc, (self.frame.shape[0], self.frame.shape[1], 5))
        
        print "shaped", clas.shape
        
        return clas

                
    
def build_parser():
    parser = ArgumentParser()
    
    parser.add_argument('video', help='video file')
    parser.add_argument('frame', help='frame number', type=int)
    
    parser.add_argument('-w', "--weights", help='use custom weights file for model', default="ClassyVCoderX.1.h5")
    parser.add_argument('-v', "--verbose", help='print verbose statements while executing', action = 'store_true')    

    return parser


def main(opts):
    
    s = Strider(opts)
    clas = s.run()
    for i in range(clas.shape[2]):
        cv2.imwrite("saliance" + str(i) + ".png", clas[:,:,i] * 255.0)
        #cv2.imshow(str(i), clas[:,:,i])
        cv2.waitKey(0)
    
        
if __name__ == '__main__':
    main(build_parser().parse_args())
 


    
        
        