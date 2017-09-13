#! /usr/bin/env python
"""
Given a databag and a video, generate crops of interesting particles.

CropX: Does not perform resize. Simply takes a 6x6x crop of original frame
    

USING:

    As a command line utility:
    
        $ Cropper.py input_video input_bag output_dir [-p particle_id -pad padding]
        
        
    
    As a module:
    
        import Cropper from Cropper
        cropper = Cropper(input_video, aDataBagObjectOrFilename)
        crop = cropper.isolate(frame_id, particle_id)
        

Author: Martin Humphreys
"""



import cv2

from argparse import ArgumentParser
from math import floor, ceil
import os
import uuid

from DataBag import DataBag
from Query import Query
import numpy as np
from functions.to_precision import to_precision
from functions.dotdict import dotdict

from BackgroundExtractor import SimpleExtractor as BackgroundExtractor
from Normalizer import Normalizer
from FrameGrabber import FrameGrabber
import base64
import sqlite3


SIZE = 64


class Crop(object):
    
    
    def __init__(self, video, bag, opts):
        
        self.bag = DataBag.fromArg(bag)
        self.query = Query(self.bag)
        self.grabber = FrameGrabber(video)
        self.normalizer = Normalizer()
        
        if isinstance(opts, dict):
            self.opts = dotdict(opts)
        else:
            self.opts = opts
        
        
        if self.opts.background is not None:
            
            if isinstance(self.opts.background, (str, unicode)):
                self.bg = cv2.imread(self.opts.background, 0)
            elif isinstance(self.opts.background, np.ndarray):
                self.bg = self.opts.background
            
            
        if not hasattr(self, "bg"):
            extractor = BackgroundExtractor(self.grabber.vc, self.opts)
            if self.opts.verbose:
                print "Extracting background for normalization..."
            self.bg = extractor.extract()
            if self.opts.verbose:
                print "Background extraction complete."
            
        
            
        # caching
        self.isolate_last_frame = None
        self.isolate_last_frame_id = -1
    
    def crop(self, img, top_left_x, top_left_y, width, height):
        """
        Crops a ROI from an image, handling OOB issues correctly.
        https://stackoverflow.com/a/42032814
        """
        bottom_right_x = top_left_x + width;
        bottom_right_y = top_left_y + height;
        
        if (top_left_x < 0 or top_left_y < 0 or bottom_right_x > img.shape[1] or bottom_right_y > img.shape[0]):
            # border padding will be required
            border_left, border_right, border_top, border_bottom = 0, 0, 0, 0
            if (top_left_x < 0):
                width = width + top_left_x
                border_left = -1 * top_left_x
                top_left_x = 0
            if (top_left_y < 0):
                height = height + top_left_y
                border_top = -1 * top_left_y
                top_left_y = 0
            if (bottom_right_x > img.shape[1]):
                width = width - (bottom_right_x - img.shape[1])
                border_right = bottom_right_x - img.shape[1]
            if (bottom_right_y > img.shape[0]):
                height = height - (bottom_right_y - img.shape[0])
                border_bottom = bottom_right_y - img.shape[0]
            crop = img[top_left_y:top_left_y+height, top_left_x:top_left_x+width]
            crop = cv2.copyMakeBorder(crop, border_top, border_bottom, border_left, border_right, cv2.BORDER_REPLICATE)
        else:
            # no border padding required
            crop = img[top_left_y:top_left_y+height, top_left_x:top_left_x+width]
        return crop;


    def isolate(self, frame_no, particle_id):
        props = self.query.particle_properties(frame_no, particle_id)
        if props is None:
            print frame_no, particle_id
        x, y, a, r = int(round(props.x)), int(round(props.y)), float(props.area), float(props.radius)
        
        r = SIZE / 2
        x1, y1, d = x - r, y - r, (r*2)
        
        if frame_no == self.isolate_last_frame_id:
            ret, frame = True, self.isolate_last_frame
        else:
            frame = self.normalizer.normalizeFrame(self.bg, self.grabber.frame(frame_no, True))
            self.isolate_last_frame = frame
            self.isolate_last_frame_id = frame_no

        return self.crop(frame, x1, y1, d, d)
        
        
    def get(self, frame_no, particle_id):
        return self.isolate(frame_no, particle_id)
    
    def update(self, frame_no, particle_id):
        crop = self.get(frame_no, particle_id)
        crop = sqlite3.Binary(crop.tobytes())
        s = 1.0
        c = self.bag.cursor()
        c.execute("UPDATE assoc SET crop = ?, scale = ? WHERE frame = ? AND particle = ?", (crop, s, frame_no, particle_id))

    

def build_parser():
    parser = ArgumentParser()
    
    parser.add_argument('input_video', help='The video file to use')
    parser.add_argument('bag', help='The databag file with stored detection or tracking results')
    parser.add_argument("-b", "--background", help="Normalize with given background")
    parser.add_argument('-v', "--verbose", help='print verbose statements while executing', action = 'store_true')    
    

    return parser


def main(opts):
    
    if not os.path.isfile(opts.input_video):
        parser.error("Input video file %s does not exist." % opts.bg)
        
    if not os.path.isfile(opts.bag):
        parser.error("DataBag file %s does not exist." % opts.bag)
    
    cropper = Crop(opts.input_video, opts.bag, opts)
    
    for f in cropper.query.frame_list():
        if opts.verbose:
            print "Extracting crops from frame", f.frame
        for p in cropper.query.particles_in_frame(f.frame):
            cropper.update(p.frame, p.id)
    cropper.bag.commit()
    
if __name__ == '__main__':
    main(build_parser().parse_args())
 









