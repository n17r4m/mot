import os
import re
import cv2
import numpy as np
import imutils
import random

# AGAIN, OMG fix this/
TRAINING = "/local/scratch/mot/data/crops/micro"
VALIDATION = "/local/scratch/mot/data/crops/validation"
CAT_MAP = {
    "undefined": 0,
    "unknown": 1,
    "bitumen": 2,
    "sand": 3,
    "bubble": 4
}

class dataset_generator(object):

    def __init__(self):
        
        self.training = self.readdir_parse(TRAINING)
        self.validation = self.readdir_parse(VALIDATION)
        
        self.training = self.augment(self.training)
        
        self.mean = np.mean([item["crop"] for item in self.training], axis=0)
        
        
        
    
    def fetch(self, n=128, training=True):
        X = []
        Y = []
        
        for i in range(n):
            if training:
                item = random.choice(self.training)
            else:
                item = random.choice(self.validation)
            X.append(item["crop"])
            Y.append(item["category"])
            
        return (np.array(X), np.array(Y))
    
        
    def readdir_parse(self, directory):
        items = []
        for type, num in CAT_MAP.items():
            path = os.path.join(directory, type)
            for file in os.listdir(path):
                #m = re.match(r"^([\w+\d-]+)_(\d+\.\d+).png$", file)
                loc = os.path.join(path, file)
                items.append({
                    "path":     loc,
                    "type":     type,
                    "category": num,
                    #"scale":    float(m.group(2)),
                    "crop":     cv2.imread(loc, 0)
                })
        return items

    def augment(self, training):
        augmented = []
        for item in training:
            #for angle in np.arange(0, 360, 90):
            for flip in [True, False]:
                aug = item.copy()
                #aug["crop"] = imutils.rotate(item["crop"], angle)
                if flip:
                    aug["crop"] = np.fliplr(aug["crop"])
                augmented.append(aug)
        return augmented
                
            
            
            
        