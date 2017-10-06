#! /usr/bin/env python
"""
Given a databag, generate and store feature maps for deep learning.


CHANGELOG:
    
    
Author: Kevin Gordon
"""
from DataBag import DataBag
from Query import Query
from FrameGrabber import FrameGrabber
import os
import numpy as np
from argparse import ArgumentParser

import sqlite3


class ScreenFeatures(object):

    def __init__(self, bag, video, output_shape=(64,64)):
        '''
        Output shape (height, width)
        '''
        if os.path.exists(video):
            self.video = FrameGrabber(video)
        else:
            class foo():
                def __init__(self, video):
                    self.shape = tuple(int(i) for i in video[1:-1].split(','))
            self.video = foo(video)
        self.bag = DataBag.fromArg(bag)
        self.query = Query(self.bag)
        self.output_shape = output_shape

        scale = np.float64(self.output_shape) / self.video.shape
        self.sx = scale[1]
        self.sy = scale[0]

    def get(self, frame_no, N=150):
        '''
        Return a feature map for the specified frame

        Current feature map: detections
        N: top N largest detections to include
        '''
        frame = np.zeros(self.output_shape, dtype=np.uint8)
        results = self.query.top_particles_by_area(frame_no, N)
        
        for particle in results:
            x = int(particle.x * self.sx)
            y = int(particle.y * self.sy)
            frame[y, x] = 255
        return frame
    
    def update(self, frame_no, N=None):
        if N is None:
            frame = self.get(frame_no)
        else:
            frame = self.get(frame_no, N)
        frame = sqlite3.Binary(frame.tobytes())
        c = self.bag.cursor()
        c.execute("UPDATE frames SET bitmap = ? WHERE frame = ?", (frame, frame_no))

    

def build_parser():
    parser = ArgumentParser()
    
    parser.add_argument('input_video', help='The video file to use, over-ride with a (height, width) tuple')
    parser.add_argument('bag', help='The databag file with stored detection or tracking results')
    parser.add_argument('-v', "--verbose", help='print verbose statements while executing', action = 'store_true')    
    

    return parser


def main(opts):
    
    sfeatures = ScreenFeatures(opts.bag, opts.input_video)
    
    for f in sfeatures.query.frame_list():
        if opts.verbose:
            print("Extracting crops from frame"), f.frame
        ### Do frame stuff ###
        sfeatures.update(f.frame)

    sfeatures.bag.commit()
    
if __name__ == '__main__':
    main(build_parser().parse_args())
 









