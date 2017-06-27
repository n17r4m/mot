#! /usr/bin/env python
"""
Stitches videos of the same size/properties together

USING:

    As a command line utility: (scale 50% and output at 24fps)
    
        $ VideoConcatanate.py new_video video1 video2 ... 
    
    As a module:
    
        vc = VideoConcatanate(*vids)
        stream = vc.process()
    
    Optional args:
        -v for verbose output

Author: Martin Humphreys
"""

from argparse import ArgumentParser
from io import BytesIO
import numpy as np
import os
import cv2
import imutils


class VideoConcatanate(object):

    def __init__(self, out, *vids):
        
        print vids # BytesIO
        
        
        
        
        self.vw = cv2.VideoWriter(outfile, cv2.VideoWriter_fourcc(*'XVID'), self.fps, (self.width_out, self.height_out))
        
        """
        self.vc        = cv2.VideoCapture(infile)
        self.width_in  = int(self.vc.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height_in = int(self.vc.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        self.scale      = scale
        self.fps        = fps
        self.width_out  = int(self.width_in  * scale)
        self.height_out = int(self.height_in * scale)
        self.vw = cv2.VideoWriter(outfile, cv2.VideoWriter_fourcc(*'XVID'), self.fps, (self.width_out, self.height_out))
        """
    def reset(self):
        self.vc        = cv2.VideoCapture(vids[0])
        self.width_in  = int(self.vc.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height_in = int(self.vc.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = 

    def process(self, verbose=False):  
        pass
        """
        ret, frame = self.vc.read()
        bg = np.float32(frame)
        f = 0
        while(True):
            f += 1
            ret, frame = self.vc.read()
            if not ret:
                break;
            frame = imutils.resize(frame, width = self.width_out)
            if verbose:
                print("Frame", f)
            self.vw.write(frame)
        """
        
def build_parser():
    parser = ArgumentParser()
    """
    parser.add_argument('input_video', help='Original video')
    parser.add_argument('output_video', help='Video file to save compessed version to')
    parser.add_argument('-s', help='video scale factor', default="0.25", type=float)
    parser.add_argument('-f', help='frames per second', default="300", type=float)
    parser.add_argument('-v', help='print verbose statements while executing', action = 'store_true')
    """
    return parser

def main():
    parser = build_parser()
    opts = parser.parse_args()
    """
    if not os.path.isfile(opts.input_video):
        parser.error("Video file %s does not exist." % opts.input_video)
    
    vc = VideoCompressor(opts.input_video, opts.output_video, opts.s)
    vc.process(opts.v)
    """
    

if __name__ == '__main__':
    main()

