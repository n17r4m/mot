#! /usr/bin/env python
"""
Given an array of binary images, returns a dictionary of component information
with at least the following key/value pairs:
    num: array containing a number of components... integer
         where the array index corresponds to the frame index
    img: array containing labelled images... np.array
         where the array index corresponds to the frame index
    comp: array containing component stats ... list of tuples
          where first array index corresponds to the frame index
          and second array index correspondes to the component index
    cent: array containing centroid data ... list of *check docs...tuples?*
          where first array index corresponds to the frame index
          and second array index correspondes to the component index

USING:

    As a command line utility:
    
        $ ComponentExtractor.py input_binary output_file
    
    As a module:
    
        import ComponentExtractor
        extractor = ComponentExtractor(input_array)
        component_data = extractor.extract()

Author: Kevin Gordon
"""

import cv2
from argparse import ArgumentParser
import numpy as np
import os
from skimage import measure

class ComponentExtractor(object):

    def __init__(self, input_array):
        self.images = input_array
        self.frames = len(input_array)        

    def extract(self, verbose=False):
        global MAX_OBJECTS_PER_FRAME

        out = {'num': [],
               'img': [],
               'comp': [],
               'cent': []}

        for i in range(self.frames):
            num, img, comp, cent  = cv2.connectedComponentsWithStats(self.images[i])

            out['num'].append(num)
            out['img'].append(img)
            out['comp'].append(comp)
            out['cent'].append(cent)            

            if verbose:
                print 'component data extracted for image ' + str(i) + ' of ' + str(self.frames-1)

        self.component_data = out

        return out

    def filter(self, min_area=3, max_area=200, verbose=False, as_indices=False):
        '''
        Return a boolean array indicating whether the component at
        the corresponding index in component_data made it past the filter
        (true) or not (false)

        '''
        # Init our output data structure
        out = []
        self.indices = []

        removed_total = 0
        kept_total = 0

        # Number of frames
        N = self.frames

        for i in range(N):

            # Number of components in frame i
            M = self.component_data['num'][i]

            buf = []

            self.indices.append([])

            for j in range(M):

                # Stats for component j
                L, T, W, H, A = self.component_data['comp'][i][j]
                pt1 = (L,T)
                pt2 = (L+W,T+H)

                x, y = np.array(pt2) - np.array(pt1)

                if A < min_area or A > max_area:

                    buf.append(False)
                    removed_total += 1
                    continue

                kept_total += 1
                buf.append(True)
                self.indices[i].append(j)

            out.append(buf)

        if verbose:
            print "removed " + str(removed_total)
            print "kept " + str(kept_total)

        self.filter = out
        if as_indices:
            return self.indices

        return  self.filter


class ComponentExtractorV2(object):

    def __init__(self, bag = None, save_binary=False):
        self.bag = bag
        self.save_binary = save_binary

    def extract(self, frame_no, binary_image, intensity_image):
        label_image = cv2.connectedComponents(binary_image)[1]
        props = measure.regionprops(label_image, intensity_image)

        binary_image_out = np.zeros((binary_image.shape), dtype=np.bool8)

        self.bag.batchInsertFrame(frame_no)

        if self.bag is None:
            return props

        for prop in props:
            if self.filterByArea(prop.area):
                continue

            pid = self.bag.batchInsertParticle(int(prop.area), int(prop.mean_intensity), int(prop.perimeter))
            y, x = prop.centroid
            self.bag.batchInsertAssoc(frame_no, pid, x, y)

            if self.save_binary:            
                binary_image_out[label_image == prop.label] = 1

        if self.save_binary:
            self.bag.query("DELETE FROM FRAMES WHERE frame == " + str(frame_no))
            self.bag.batchInsertFrame(frame_no, binary_image_out)        

        return props

    def filterByArea(self, area, min_area=5, max_area=1000000):
        pass
        return area < min_area or area > max_area


def build_parser():
    parser = ArgumentParser()
    parser.add_argument('input_array', help='binary images to extract component data from')
    parser.add_argument('output_file', help='output file name')
    parser.add_argument('-b', help='save the binary mask when processing', action='store_true')
    parser.add_argument('-v', help='print verbose statements while executing', 
                              action='store_true')

    return parser


def main():
    parser = build_parser()
    options = parser.parse_args()
    if not os.path.isfile(options.input_array):
        parser.error("binary file %s does not exist." % options.input_array)
    
    array = np.load(options.input_array)

    extractor = ComponentExtractorV2(array, opts.b)

    component_data = extractor.extract(verbose=options.v)

    np.save(options.output_file, component_data)


if __name__ == '__main__':
    main()
