import os
import re
import cv2
import numpy as np
import random

CLASSIFIED = "/mnt/SIA/crop_testing/classified"
UNCLASSIFIED = "/mnt/SIA/crop_testing/crops"
CAT_MAP = {
    "u": 0,
    "x": 1,
    "d": 2,
    "s": 3,
    "b": 4
}

class dataset_generator(object):

    def __init__(self):
        
        self.classified = self.readdir_parse(CLASSIFIED)
        self.unclassified = self.readdir_parse(UNCLASSIFIED)
        
    
    def fetch(self, n=128, training=True):
        X = []
        Y = []
        
        for i in range(n):
            if training:
                item = random.choice(self.classified)
            else:
                item = random.choice(self.unclassified)
            X.append(cv2.cvtColor(cv2.imread(item["path"]), cv2.COLOR_RGB2GRAY))
            Y.append(item["category"])
            
        return (np.array(X), np.array(Y))
    
        
    def readdir_parse(self, directory):
        items = []
        for file in os.listdir(directory):
            m = re.match(r"^(\w)_(\d+)_(\d+)_(\d*\.\d*)\.(\w+)$", file)
            items.append({
                "path":     os.path.join(directory, file),
                "type":     m.group(1),
                "frame":    m.group(2),
                "particle": m.group(3),
                "scale":    m.group(4),
                "ext":      m.group(5),
                "category": CAT_MAP[m.group(1)]
            })
        return items

