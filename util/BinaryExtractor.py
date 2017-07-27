#! /usr/bin/env python
"""
Convert images into binary images.

USING:

    As a command line utility:
    
        $ BinaryExtractor.py input_video output_video [--threshold threshold --invert --frame frame]
    
    As a module:
    
        from BinaryExtractor import BinaryExtractor
        binaryExtractor = BinaryExtractor([invert=False, threshold=50])
        frame_binarized = binaryExtractor.extract(input_frame)

Author: Kevin Gordon
"""

from argparse import ArgumentParser
import numpy as np
import os
import cv2

from FrameGrabber import FrameGrabber

class BinaryExtractor(object):

    def __init__(self, threshold=50, invert=False):
        self.type = 0
        self.threshold = threshold

        if invert:
            self.type += cv2.THRESH_BINARY_INV
        else:
            self.type += cv2.THRESH_BINARY

    def extract(self, frame):
        t, frame = cv2.threshold(frame, self.threshold, 255, self.type)
        return frame.astype('uint8')

def build_parser():
    parser = ArgumentParser()
    parser.add_argument('input_video', help='video to extract binary video from')
    parser.add_argument('output_video', help='filename of output array')

    parser.add_argument('-t', '--threshold', help='binary threshold, above threshold->1, below threshold->0', type=int)
    parser.add_argument('-inv', '--invert', help='invert the output', action = 'store_true')
    parser.add_argument('-f', '--frame', help='frame to process', type=int, nargs='?')

    return parser


def main():
    parser = build_parser()
    options = parser.parse_args()

    if not os.path.isfile(options.input_video):
        parser.error("input video file %s does not exist." % options.input_video)
    
    in_video = FrameGrabber(options.input_video)

    binarizer = BinaryExtractor(options.threshold, options.invert)

    vw = cv2.VideoWriter(options.output_video, 
                         in_video.fourcc, 
                         in_video.fps, 
                         in_video.shape)

    if options.frame:        
        N = [options.frame]
    else:
        N = range(in_video.frames)

    for i in N:
        in_frame = in_video.frame(i)
        binary_frame = binarizer.extract(in_frame)
        vw.write(binary_frame)

    vw.release()

if __name__ == '__main__':
    main()
