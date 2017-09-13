#! /usr/bin/env python
"""
dumps crops from a databag to disk.dumps

USING:

        

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



def build_parser():
    parser = ArgumentParser()
    
    
    parser.add_argument('bag', help='The databag file with stored detection or tracking results')
    parser.add_argument('output_dir', help='Place to dump crops to')
    parser.add_argument("-b", "--background", help="Normalize with given background")
    parser.add_argument('-v', "--verbose", help='print verbose statements while executing', action = 'store_true')    
    

    return parser


def main(opts):
        
    
    if not os.path.isfile(opts.bag):
        parser.error("DataBag file %s does not exist." % opts.bag)
    
    if not os.path.exists(opts.output_dir):
        os.makedirs(opts.output_dir)
    
    bag = DataBag.fromArg(opts.bag)
    query = Query(bag)
    
    for f in query.frame_list():
        if opts.verbose:
            print "Extracting crops from frame", f.frame
        for p in query.particles_in_frame(f.frame):
            
            if f.frame % 10 == 5: # only one particle crop per burst please.
                crop = bag.getCrop(p.frame, p.id)[0]
                
                path = os.path.join(opts.output_dir, str(p.category))
                file = "{}.png".format(uuid.uuid4())
                if not os.path.exists(path):
                    os.makedirs(path)
                
                cv2.imwrite(os.path.join(path, file), crop)
    
    
if __name__ == '__main__':
    main(build_parser().parse_args())
 









