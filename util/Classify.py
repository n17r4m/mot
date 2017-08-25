#! /usr/bin/env python
"""
When provided with crops extracted from a video, this utility
will try to predict which type of particle the crop is of.

CHANGELOG:
    
USING:

    As a command line utility:
    
        $ Classify.py copy crop_dir output_dir
        
        
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

from models.ClassyVCoder import ClassyVCoder
from DataBag import DataBag
from Cropper import Cropper
from Query import Query



class Classify(object):
    
    def __init__(self, weight_file = "ClassyVCoder.h5", verbose = False):
        
        self.verbose = verbose
        self.CC = ClassyVCoder()
        self.CC.load(os.path.join(self.CC.path(), weight_file))
    
    def cropTensorFromArg(self, crops):
        if isinstance(crops, (str, unicode)):
            if self.verbose:
                print "single file"
            crops = numpy.array([cv2.imread(crop, 0).reshape(64, 64, 1)])
        elif isinstance(crops[0], (str, unicode)):
            if self.verbose:
                print "multiple file"
            crops = np.array(map(lambda f: cv2.imread(f, 0).reshape(64, 64, 1), crops))
        elif len(crops.shape) == 3:
            if self.verbose:
                print "single crop (numpy image or feature vector)"
            crops = numpy.array([crops])
        else:
            if self.verbose:
                print "# 4d tensor of images / feature vectors"
            pass
        return crops.astype("float32") / 255.0
        
    def predict(self, crops, using_features = False):
        crops = self.cropTensorFromArg(crops)
        classifier = self.CC.featureclassifier if using_features else self.CC.imageclassifier
        
        # this needs a looksie at... [1]
        return self.CC.classycoder.predict(crops)
        
        return classifier.predict(crops)
        
    def classify(self, crops, using_features = False, named = False):
        predictions = self.predict(crops)
        # relies on above behavior... discuss. [1]
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
    
    parser.add_argument('-w', "--weights", help='use custom weights file for model', default="ClassyVCoder.h5")
    parser.add_argument('-v', "--verbose", help='print verbose statements while executing', action = 'store_true')    

    return parser


def main(opts):
    
    classifier = Classify(opts.weights, opts.verbose)
    
    if opts.mode == "bag":
        
        if not os.path.isfile(opts.source):
            raise TypeError("Target bag to classify %s does not exist." % opts.target)
        
        
        if opts.verbose:
            print "Loading data bag"
        bag = DataBag(opts.source)
        
        if opts.verbose:
            print "Querying particle list"
        q = Query(bag)
        particles = q.particle_list()
        
        c = bag.cursor()
    
        for p in particles:
            
            if opts.verbose:
                print "Classifying particle", p.id
            
            f = q.particle_instances(p.id)
            crops = []
            for i in f:
                crop, s = bag.getCrop(i.frame, p.id)
                if opts.verbose:
                    cv2.imshow("out", crop)
                    cv2.waitKey(1)
                crops.append(crop)
            crops = np.array(crops)
            shape = crops.shape
            
            crops = np.array(crops).reshape(shape[0], shape[1], shape[2], 1)
            
            cat = classifier.classify(crops)
            if opts.verbose:
                print cat
            cat_vote = np.argmax(np.bincount(cat))    
            if opts.verbose:
                print "Choosing category", cat_vote
            
            c.execute("UPDATE particles SET category = ? where id=?", (cat_vote, p.id))
        bag.commit()
            
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
 


    
        
        