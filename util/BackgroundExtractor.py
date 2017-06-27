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


class BackgroundExtractor(object):

    def __init__(self, filename):
        self.vc = cv2.VideoCapture(filename)
        self.frames = int(self.vc.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.vc.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.vc.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
    def extract(self, verbose=False):  
        ret, frame = self.vc.read()
        bg = np.float32(frame)
        f = 1
        while(True):
            ret, frame = self.vc.read()
            a = 1 / self.frames
            if not ret:
                break;
            if f is 1:
                bg = np.float32(frame)
            else:
                cv2.accumulateWeighted(frame, bg, a)
            
            f += 1
        return cv2.convertScaleAbs(bg)
  
class AverageExtractor(BackgroundExtractor):

    def extract(self, verbose=False):
        shape = (self.height, self.width)

        avg_bg = np.zeros(shape)

        N = int(self.frames)
        self.vc.set(cv2.CAP_PROP_POS_FRAMES, 0)
        count = 0
        for i in range(N):
            self.vc.set(cv2.CAP_PROP_POS_FRAMES, i)
                        
            ret, frame = self.vc.read()
            
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                avg_bg += frame * 1.0 / N

            else:
                count +=1
                print "Error reading video frame " + str(i) + " ..."

            if i%100==0 and verbose:
                print 'processed frame ' + str(i) + ' of ' + str(N-1)

        print "error reading", count, 'frames'
        return np.uint8(avg_bg)

class MaximumExtractor(BackgroundExtractor):

    def extract(self, verbose=False):
        shape = (self.height, self.width)

        max_bg = np.zeros(shape)

        N = int(self.frames)
        self.vc.set(cv2.CAP_PROP_POS_FRAMES, 0)

        for i in range(N):
            self.vc.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = self.vc.read()

            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                max_bg = self.maximum(max_bg, frame)

            else:
                print "Error reading video frame " + str(i) + " ..."

            if i%100==0 and verbose:
                print 'processed frame ' + str(i) + ' of ' + str(N-1)

        return np.uint8(max_bg)

    def maximum (self, A, B):
        BisBigger = A-B
        BisBigger = np.where(BisBigger < 0, 1, 0)
        return A - A * BisBigger + B * BisBigger

class SimpleExtractor(AverageExtractor):
    # The only difference between this and Average is that
    #  we only average the first 10 frames...
    def extract(self, verbose=False):
        shape = (self.height, self.width)

        avg_bg = np.zeros(shape)

        N = 20
        self.vc.set(cv2.CAP_PROP_POS_FRAMES, 0)

        for i in range(N):
            self.vc.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = self.vc.read()

            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                avg_bg += frame * 1.0 / N

            else:
                print "Error reading video frame " + str(i) + " ..."

            if i%100==0 and verbose:
                print 'processed frame ' + str(i) + ' of ' + str(N-1)

        return np.uint8(avg_bg)

def build_parser():
    parser = ArgumentParser()
    parser.add_argument('input_video', help='video to extract bacground from')
    parser.add_argument('output_image', help='file to save extracted background to')
    parser.add_argument('background_type', help='type of background extraction [running_avg, avg, maximum, simple]')
    parser.add_argument('-v', help='print verbose statements while executing', 
                              action = 'store_true')
    return parser

def main():
    parser = build_parser()
    options = parser.parse_args()
    if not os.path.isfile(options.input_video):
        parser.error("Video file %s does not exist." % options.input_video)
    
    if options.background_type == 'running_avg':
        extractor = BackgroundExtractor(options.input_video)
    elif options.background_type == 'avg':
        extractor = AverageExtractor(options.input_video)
    elif options.background_type == 'max':
        extractor = MaximumExtractor(options.input_video)
    elif options.background_type == 'simple':
        extractor = SimpleExtractor(options.input_video)

    bg = extractor.extract(verbose=options.v)
    cv2.imwrite(options.output_image, bg)

if __name__ == '__main__':
    main()
