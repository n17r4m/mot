#! /usr/bin/env python
"""
USING:

    As a command line utility:
    
        $ ComponentExtractor.py binary_video intensity_video dataBag [--frame frame_no --binary]
    
    As a module:
    
        # use the component data directly
        from ComponentExtractor import ComponentExtractor
        componentExtractor = ComponentExtractor([databag=None, save_binary=False])
        props = comp_ext.extract(frame_no, binary_frame, intensity_frame)\
        # or store the component data in a database
        componentExtractor = ComponentExtractor(databag[, save_binary=False])
        comp_ext.extract(frame_no, binary_frame, intensity_frame)
        bag.commit()

Author: Kevin Gordon
"""

import cv2
from argparse import ArgumentParser
import numpy as np
import os
from skimage import measure
from DataBag import DataBag
from FrameGrabber import FrameGrabber

class ComponentExtractor(object):

    def __init__(self, bag = None, save_binary=False):
        self.bag = bag
        self.save_binary = save_binary

    def extract(self, frame_no, binary_image, intensity_image):
        label_image = cv2.connectedComponents(binary_image)[1]
        props = measure.regionprops(label_image, intensity_image)

        binary_image_out = np.zeros((binary_image.shape), dtype=np.bool8)

        frame_props = {'number': frame_no}

        if self.bag is None:
            return props

        for prop in props:
            if self.filterByArea(prop.area):
                continue

            particle_props = {'area': float(prop.area), 
                              'perimeter': prop.perimeter, 
                              'intensity': prop.mean_intensity,
                              'radius': prop.major_axis_length}

            pid = self.bag.batchInsertParticle(particle_props)

            y, x = prop.centroid

            assoc_props = {'frame': frame_no, 'particle': pid, 'x': x, 'y': y}

            self.bag.batchInsertAssoc(assoc_props)

            if self.save_binary:            
                binary_image_out[label_image == prop.label] = 1

        if self.save_binary:
            frame_props['bitmap'] = binary_image_out       

        self.bag.batchInsertFrame(frame_props)

        return props

    def filterByArea(self, area, min_area=5, max_area=1000000):
        pass
        return area < min_area or area > max_area

def build_parser():
    parser = ArgumentParser()
    parser.add_argument('binary_video', help='binary video to extract component data from')
    parser.add_argument('intensity_video', help='original or normalized video')
    parser.add_argument('bag', help='databag to store the component data')

    parser.add_argument('-f', '--frame', help='frame to process', type=int, nargs='?')
    parser.add_argument('-b', '--binary', help='save the binary mask when processing', action='store_true')

    return parser


def main():
    parser = build_parser()
    options = parser.parse_args()

    if not os.path.isfile(options.binary_video):
        parser.error("binary video %s does not exist." % options.binary_video)
    if not os.path.isfile(options.intensity_video):
        parser.error("instensity video %s does not exist." % options.intensity_video)

    bag = DataBag(options.bag)

    extractor = ComponentExtractor(bag, options.binary)

    binary_video = FrameGrabber(options.binary_video)
    intensity_video = FrameGrabber(options.intensity_video)

    if options.frame:
        N = [options.frame]
    else:
        N = range(binary_video.frames)

    for i in N:
        frame_binarized = binary_video.frame(i, gray=True)
        frame_normalized = intensity_video.frame(i, gray=True)
        print np.min(frame_binarized), np.max(frame_binarized)
        extractor.extract(i, frame_binarized, frame_normalized)

    bag.commit()

if __name__ == '__main__':
    main()
