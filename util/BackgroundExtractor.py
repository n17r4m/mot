#! /usr/bin/env python
"""
Compute a background image from a video sequence.

Choose between running average, global average, or global maximum.

USING:

    As a command line utility:
    
        $ BackgroundExtractor.py input_video output_image background_type
    
    As a module:
    
        import BackgroundExtractor
        extractor = BackgroundExtractor("input_video.avi")
        bg = extractor.extract()

    Optional args:
        -v for verbose output

Author: Martin Humphreys
"""

from argparse import ArgumentParser
import numpy as np
import os
import cv2
from FrameGrabber import FrameGrabber

class BackgroundExtractor(object):

    def __init__(self, video, opts):
        
        self.grabber = FrameGrabber(video)
        self.opts = opts
        
        if self.opts.verbose:
            print "Extracting from", self.grabber.frames, "frames"
            print "size:", (self.width, self.height)
        
    def extract(self):  
        pass
  

class AverageExtractor(BackgroundExtractor):

    def extract(self):
        avg_bg = np.zeros(self.grabber.shape)
        N = self.grabber.frames
        count = 0
        for i in range(N):
                       
            frame = self.grabber.frame(i)
            
            if len(frame):
                avg_bg += frame * 1.0 / N
            else:
                count +=1
                print "Error reading video frame " + str(i) + " ..."

            if i%100==0 and self.opts.verbose:
                print 'processed frame ' + str(i) + ' of ' + str(N-1)
        print "error reading", count, 'frames'
        return np.uint8(avg_bg)

class MaximumExtractor(BackgroundExtractor):
    def extract(self):

        max_bg = np.zeros(self.grabber.shape)
        N = self.grabber.frames
        
        for i in range(N):
            
            frame = self.grabber.frame(i)

            if len(frame):
                max_bg = self.maximum(max_bg, frame)
            else:
                print "Error reading video frame " + str(i) + " ..."
            if i%100==0 and self.opts.verbose:
                print 'processed frame ' + str(i) + ' of ' + str(N-1)

        return np.uint8(max_bg)

    def maximum (self, A, B):
        BisBigger = A-B
        BisBigger = np.where(BisBigger < 0, 1, 0)
        return A - A * BisBigger + B * BisBigger


class MixedExtractor(BackgroundExtractor):
    
    def extract(self, ratio=0.5):
        avg_ex = AverageExtractor(self.vc, self.opts)
        max_ex = MaximumExtractor(self.vc, self.opts)
        return (avg_ex.extract() * ratio) + (max_ex.extract() * (1-ratio))



class SimpleExtractor(BackgroundExtractor):
    def extract(self):

        max_bg = np.zeros(self.grabber.shape)

        N = 101
        
        for i in range(N):
            
            frame = self.grabber.frame(i)

            if len(frame):
                max_bg = self.maximum(max_bg, frame)
            else:
                print "Error reading video frame " + str(i) + " ..."

            if i%20==0 and self.opts.verbose:
                print 'processed frame ' + str(i) + ' of ' + str(N-1)

        return np.uint8(max_bg)

    def maximum (self, A, B):
        BisBigger = A-B
        BisBigger = np.where(BisBigger < 0, 1, 0)
        return A - A * BisBigger + B * BisBigger        

def build_parser():
    parser = ArgumentParser()
    parser.add_argument('input_video', help='video to extract bacground from')
    parser.add_argument('output_image', help='file to save extracted background to')
    parser.add_argument('background_type', help='type of background extraction [running_avg, avg, maximum, mix, simple]')
    parser.add_argument('-v', "--verbose", help='print verbose statements while executing', action = 'store_true')
    return parser

def main():
    parser = build_parser()
    opts = parser.parse_args()
    if not os.path.isfile(opts.input_video):
        parser.error("Video file %s does not exist." % opts.input_video)


    elif opts.background_type == 'avg':
        extractor = AverageExtractor(opts.input_video, opts)
    elif opts.background_type == 'max':
        extractor = MaximumExtractor(opts.input_video, opts)
    elif opts.background_type == 'mix':
        extractor = MixedExtractor(opts.input_video, opts)
    elif opts.background_type == 'simple':
        extractor = SimpleExtractor(opts.input_video, opts)

    bg = extractor.extract()
    cv2.imwrite(opts.output_image, bg)

if __name__ == '__main__':
    main()
