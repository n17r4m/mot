import os
import re
import cv2
import numpy as np
import random
from keras.utils import to_categorical

# AGAIN, OMG fix this/
TRAINING = "/local/scratch/martin/noscale/training"
VALIDATION = "/local/scratch/martin/noscale/validation"
CAT_MAP = {
    "undefined": 0,
    "unknown": 1,
    "bitumen": 2,
    "sand": 3,
    "bubble": 4
}

class dataset_generator(object):

    def __init__(self, CC):
        self.CC = CC
        self.n_categories = CC.num_categories
        self.trainingX, self.trainingY = self.readdir_parse(TRAINING)
        self.validationX, self.validationY = self.readdir_parse(VALIDATION)
        
    
    def fetch(self, n=128, training=True):
        
        X = self.trainingX if training else self.validationX
        Y = self.trainingY if training else self.validationY
        picks = np.random.choice(X.shape[0], size=n, replace=False)
        
        return (X[picks], Y[picks])
        
        
    def readdir_parse(self, directory):
        X, Y = [], []
        for type, num in CAT_MAP.items():
            path = os.path.join(directory, type)
            for file in os.listdir(path):
                fpath = os.path.join(path, file)
                crop = self.CC.preproc(cv2.imread(fpath, 0))
                category = to_categorical(num, self.n_categories)
                X.append(crop)
                X.append(np.fliplr(crop))
                Y.append(category)
                Y.append(category)
                
        return np.array(X), np.array(Y).reshape(len(Y), self.n_categories)

