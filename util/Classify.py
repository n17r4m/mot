#! /usr/bin/env python
"""
When provided with crops extracted from a video, this utility
will try to predict which type of particle the crop is of.

CHANGELOG:
    
USING:

    As a command line utility:
    
        $ Classify.py crop_dir output_dir
        
        
    As a module:
    
        import Classify from Classify
        classifier = Classify()
        crop_features = classifier.features(crop)   # accepts filename or [filenames]
        crops_features = classifier.features(crops) # or cv2 image or [images]
        category = classifier.classify(crop)        
        likelyhoods = classifier.predict(crop)
        

Author: Martin Humphreys
"""


import os
import cv2
import numpy as np
from argparse import ArgumentParser
import shutil

from models.ClassyCoder import ClassyCoder




class Classify(object):
    
    def __init__(self, weight_file = "ClassyCoder.h5"):
        
        self.CC = ClassyCoder()
        self.CC.load(os.path.join(self.CC.path(), weight_file))
    
    def cropTensorFromArg(self, crops):
        if isinstance(crops, (str, unicode)):
            print "single file"
            crops = numpy.array([cv2.imread(crop, 0).reshape(64, 64, 1)])
        elif isinstance(crops[0], (str, unicode)):
            print "multiple file"
            crops = np.array(map(lambda f: cv2.imread(f, 0).reshape(64, 64, 1), crops))
        elif len(crops.shape) == 3:
            print "single crop (numpy image or feature vector)"
            crops = numpy.array([crops])
        else:
            print "# 4d tensor of images / feature vectors"
            pass
        return crops.astype("float32") / 255
        
    def predict(self, crops, using_features = False):
        crops = self.cropTensorFromArg(crops)
        print crops.shape
        classifier = self.CC.featureclassifier if using_features else self.CC.imageclassifier
        
        return self.CC.classycoder.predict(crops)
        
        return classifier.predict(crops)
        
    def classify(self, crops, using_features = False, named = False):
        predictions = self.predict(crops)
        categories = np.argmax(predictions[1], axis=-1)
        if named:
            return map(self.category_name, categories)
        else:
            return categories
    
    def category_name(self, num):
        return ["undefined", "unknown", "bitumen", "sand", "bubble"][num]
        
        
    


def build_parser():
    parser = ArgumentParser()
    
    parser.add_argument('mode', help='mode [move, copy, bag]')
    parser.add_argument('source', help='source_dir or bag')
    parser.add_argument('target', help='target_dir', nargs="?")
    
    parser.add_argument('-w', "--weights", help='use custom weights file for model', default="ClassyCoder.h5")
    parser.add_argument('-v', "--verbose", help='print verbose statements while executing', action = 'store_true')    

    return parser


def main(opts):
    
    classifier = Classify(opts.weights)
    
    if opts.mode is "bag":
        # TODO - inplace classification of particles in a databag
        # TODO - thoughts: why not store the crop in the bag?
        pass
    else:
    
        if not os.path.isdir(opts.source):
            raise TypeError("Crop source directory %s does not exist." % opts.source)
        
        if not opts.target:
            raise TypeError("Crop target directory must be supplied.")
        
        if not os.path.isdir(opts.target):
            raise TypeError("Crop target directory %s does not exist." % opts.target)
        
        crops = map(lambda f: os.path.join(opts.source, f), os.listdir(opts.source))
        categories = []
        batch_size = 1000
        for i in range(0, len(crops), batch_size):
            
            batch = crops[i:i+batch_size]
            categories = classifier.classify(batch, named=True)
            
            
            
            for k, cat in enumerate(categories):
                
                if opts.mode == "move":
                    shutil.move(batch[k], os.path.join(opts.target, cat, os.path.basename(batch[k])))
                elif opts.mode == "copy":
                    shutil.copy(batch[k], os.path.join(opts.target, cat, os.path.basename(batch[k])))
                else:
                    print batch[k], cat
                #print batch[k]
                
                
            
            
            
            
    
        
if __name__ == '__main__':
    main(build_parser().parse_args())
 


    
        
        