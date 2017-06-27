#! /usr/bin/env python
"""
Given a background image and an array of images (np.arrays), 
returns an array of images containing foregrounds.

Choose between absolute difference and normalized subtraction.

Normalized subtraction is experimental, and compensates for inter and intra
frame illumination changes.


USING:

    As a command line utility:
    
        $ ForegroundExtractor.py input_array background output_array [-n]
    
    As a module:
    
        import ForegroundExtractor
        extractor = ForegroundExtractor(input_array, background_image)
        bg = extractor.extract()

    Optional args:
        -n for normalized

Author: Kevin Gordon
"""
from argparse import ArgumentParser
import numpy as np
import os
import cv2


class ForegroundExtractor(object):

    def __init__(self, input_array, background):
        self.images = input_array
        self.bg = background
        self.frames = len(input_array)
        self.width = self.images[0].shape[1]
        self.height = self.images[0].shape[0]

    def extract(self):
        output = []

        for i in range(self.frames):
            foreground = 255-cv2.absdiff(self.bg, self.images[i])            
            # Clip/saturate
            # foreground[foreground<0] = 0
            # foreground[foreground>255] = 255
            output.append(foreground)

        return output

class NormalizedForegroundExtractor(ForegroundExtractor):

    def extract(self):
        # The light in a frame aka the maximum intensity value we can expect is 
        #  equal to the average background intensity. The lowest intensity value
        #  possible is assumed to be 0 for all positions.
        dynamic_range = np.float64(self.bg)

        # Some areas are always occluded on the image, so the dynamic range is
        #  very low (~0). We handle this degenerate case by clipping the minumum
        #  allowable range. In the future this could be improved to be 1st-2nd 
        #  order smooth to play nicer with edge detectors.
        # Still thinking on this... Might prefer to account for differences below the 
        # noise floor, and leave everything else raw...

        # Remove div by 0
        dynamic_range[dynamic_range<5] = 5

        images_mean = np.mean(self.images)

        output = []
        for i in range(self.frames):
            i_mean = np.mean(self.images[i])
            bias = np.float(i_mean) - np.float(images_mean)

            # Shift the intensities to the origin
            buf = self.images[i] - dynamic_range - bias

            # Scale to range [0,1]
            buf /= (dynamic_range + bias)

            # Scale to output range [0,255]
            buf *= 255

            # Shift to positive range
            buf += 255

            # Clip/saturate
            buf[buf<0] = 0
            buf[buf>255] = 255

            # Fix our div by zero fix from earlier.
            buf[self.bg<5]=255
            output.append(np.uint8(buf))

        return output

    def extract_simple(self):
        # The light in a frame aka the maximum intensity value we can expect is 
        #  equal to the average background intensity. The lowest intensity value
        #  possible is assumed to be 0 for all positions.
        dynamic_range = np.float64(self.bg)

        # Some areas are always occluded on the image, so the dynamic range is
        #  very low (~0). We handle this degenerate case by clipping the minumum
        #  allowable range. In the future this could be improved to be 1st-2nd 
        #  order smooth to play nicer with edge detectors.
        dynamic_range[dynamic_range<40] = 40

        images_mean = np.mean(self.images)

        output = []
        for i in range(self.frames):
            i_mean = np.mean(self.images[i])
            bias = np.float(i_mean) - np.float(images_mean)

            # Shift the intensities to the origin
            buf = self.images[i] - bias

            # Scale to range [0,1]
            buf /= (dynamic_range)

            # Scale to output range [0,255]
            buf *= 255

            # Clip/saturate
            buf[buf<0] = 0
            buf[buf>255] = 255

            output.append(np.uint8(buf))

        return output

class NormalizedForegroundExtractorV2(ForegroundExtractor):

    def __init__(self, background):
        self.bg = background
        self.dynamic_range =  dynamic_range = np.float64(self.bg)
        self.dynamic_range[self.dynamic_range<5] = 5

    def extract(self, frame):
        # Some areas are always occluded on the image, so the dynamic range is
        #  very low (~0). We handle this degenerate case by clipping the minumum
        #  allowable range. In the future this could be improved to be 1st-2nd 
        #  order smooth to play nicer with edge detectors.
        # Still thinking on this... Might prefer to account for differences below the 
        # noise floor, and leave everything else raw...
        
        # Shift the intensities to the origin
        buf = frame - self.dynamic_range

        # Scale to range [0,1]
        buf /= self.dynamic_range

        # Scale to output range [0,255]
        buf *= 255

        # Shift to positive range
        buf += 255

        # Clip/saturate
        buf[buf<0] = 0
        buf[buf>255] = 255

        return np.uint8(buf)

def build_parser():
    parser = ArgumentParser()
    parser.add_argument('input_array', help='images to extract foreground from')
    parser.add_argument('background', help='background model image')
    parser.add_argument('output_array', help='filename of output array')
    parser.add_argument('-n', help='normalize intensity value on the range [0-255]',
                         action = 'store_true')
    return parser

def main():
    parser = build_parser()
    options = parser.parse_args()
    if not os.path.isfile(options.input_array):
        parser.error("binary file %s does not exist." % options.input_array)
    
    array = np.load(options.input_array)

    bg = cv2.imread(options.background, cv2.IMREAD_GRAYSCALE)

    if options.n:
        extractor = NormalizedForegroundExtractor(array, bg)
    else:
        extractor = ForegroundExtractor(array, bg)

    fg = extractor.extract()

    np.save(options.output_array, np.array(fg))

if __name__ == '__main__':
    main()
