#! /usr/bin/env python
"""
Given an array of images (np.arrays), returns an array of BW images with
foreground and background separated.

Choose between simple, simple w/ OTSU, and adaptive thresholding.

TODO: implement parsing of params from command line, probably refactor
       this entire class... it's not pretty.

USING:

    As a command line utility:
    
        $ BinaryExtractor.py input_array output_array [type]
    
    As a module:
    
        import BinaryExtractor
        extractor = BinaryExtractor(input_array, type)
        bg = extractor.extract()

Author: Kevin Gordon
"""

from argparse import ArgumentParser
import numpy as np
import os
import cv2


class BinaryExtractor(object):

    def __init__(self, threshold=50, otsu=False, invert=False):
        self.type = 0
        self.threshold = threshold

        if otsu:
            self.type = cv2.THRESH_OTSU

        if invert:
            self.type += cv2.THRESH_BINARY_INV
        else:
            self.type += cv2.THRESH_BINARY

    def extract(self, frame):
        t, frame = cv2.threshold(frame, self.threshold, 255, self.type)
        return np.uint8(frame)

class AdaptiveBinaryExtractor(BinaryExtractor):

    def __init__(self, params={}, gaussian=False, **kw):
        super(AdaptiveBinaryExtractor, self).__init__(**kw)
        if gaussian:
            self.method = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
        else:
            self.method = cv2.ADAPTIVE_THRESH_MEAN_C

        if 'blockSize' in params:
            self.blockSize = params['blockSize']
        else:
            self.blockSize = 17

        if 'c' in params:
            self.c = params['c']
        else:
            self.c = 15

    def extract(self, frame):
        buf = cv2.adaptiveThreshold(frame, 255, self.method, self.type, self.blockSize, self.c)            
        return np.uint8(buf)
      

def build_parser():
    parser = ArgumentParser()
    parser.add_argument('input_array', help='images to extract binary image from')
    parser.add_argument('output_array', help='filename of output array')
    parser.add_argument('type', help='simple or adaptive thresholding')
    parser.add_argument('-otsu', help='otsu\'s method (simple thresholding)',
                                 action = 'store_true')
    parser.add_argument('-inv', help='invert the output', 
                                action = 'store_true')
    parser.add_argument('-gaussian', help='gaussian (adaptive threshold)',
                                     action = 'store_true')

    return parser


def main():
    parser = build_parser()
    options = parser.parse_args()
    if not os.path.isfile(options.input_array):
        parser.error("binary file %s does not exist." % options.input_array)
    
    array = np.load(options.input_array)

    if options.type == 'simple':
        extractor = BinaryExtractor(array, invert=options.inv, otsu=options.otsu)

    if options.type == 'adaptive':
        extractor = AdaptiveBinaryExtractor(params={}, input_array=array, gaussian=options.gaussian)


    binary = extractor.extract()

    np.save(options.output_array, np.array(binary))

if __name__ == '__main__':
    main()
