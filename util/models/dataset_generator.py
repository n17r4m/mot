import os
import re
import cv2
import numpy as np
import random

# AGAIN, OMG fix this/
TRAINING = "/local/scratch/mot/data/crops/training"
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
        
    
    def fetch(self, n=128, training=True):
        X = []
        Y = []
        
        for i in range(n):
            if training:
                item = random.choice(self.training)
            else:
                item = random.choice(self.validation)
            X.append(cv2.imread(item["path"], 0))
            Y.append(item["category"])
            
        return (np.array(X), np.array(Y))
    
        
    def readdir_parse(self, directory):
        items = []
        for type, num in CAT_MAP.items():
            path = os.path.join(directory, type)
            for file in os.listdir(path):
                m = re.match(r"^([\w+\d-]+)_(\d+\.\d+).png$", file)
                items.append({
                    "path":     os.path.join(path, file),
                    "type":     type,
                    "category": num,
                    "scale":    float(m.group(2))
                })
        return items

