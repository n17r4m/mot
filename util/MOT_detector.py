#! /usr/bin/env python
"""
Given a video to analyse, MOT_detector will seperate the
foreground from the background and construct a detection
results databag, which can then be analysed for tracking.


USING:

    As a command line utility:
    
        $ MOT_detector.py input_video output_bag [options]
    
    As a module:
    
        from MOT_detector import MOT_detector
        detector = MOT_detector(input_video)
        bag = detector.detect()

Author: Martin Humphreys
"""

import os

from BackgroundExtractor import AverageExtractor
from FrameGrabber import FrameGrabber
from BurstGrabber import BurstGrabber
from ForegroundExtractor import NormalizedForegroundExtractorV2 \
                             as NormalizedForegroundExtractor
from BinaryExtractor import BinaryExtractor
from ComponentExtractor import ComponentExtractorV2 as ComponentExtractor






def build_parser():
    parser = ArgumentParser()
    parser.add_argument('input_video', help='The video file to perform detections on')
    parser.add_argument('output_bag', help='filename of output data bag')
    parser.add_argument('-tmp', help='location to store temporary files', default="/tmp")
    

    return parser


def main():
    parser = build_parser()
    options = parser.parse_args()
    if not os.path.isfile(options.input_video):
        parser.error("video file %s does not exist." % options.input_array)
    
    array = np.load(options.input_array)

    if options.type == 'simple':
        extractor = BinaryExtractor(array, invert=options.inv, otsu=options.otsu)

    if options.type == 'adaptive':
        extractor = AdaptiveBinaryExtractor(params={}, input_array=array, gaussian=options.gaussian)


    binary = extractor.extract()

    np.save(options.output_array, np.array(binary))

if __name__ == '__main__':
    main()


