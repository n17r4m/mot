#Doesn't work

from AutoBG import AutoBG
from keras.datasets import mnist
from keras.utils import to_categorical
import matplotlib.pyplot as plt
import numpy as np
import os
import cv2
from util.FrameGrabber import FrameGrabber


from dataset_generator import dataset_generator


BG = AutoBG((2336, 1729, 1),  True)



path = "/mnt/SIA/BU-2015-10-06/T02494.avi"
fg = FrameGrabber(path)


def fetch_data(training=True, samples = 128):
    X = []
    for i in range(samples):
        X.append(fg.frame(np.random.randint(fg.frames), True))
    X = np.array(X)
    X = X.reshape((len(X), 2336, 1729, 1))
    return (X, X)

def fetch_data_generator(training=True, samples = 128):
    while True:
        yield fetch_data(training, samples)
        


#(x_train, y_train) = fetch_data(1024, True)

print BG.model.summary()

BG.model.fit_generator(fetch_data_generator(True, 1), 50,
    epochs=2 )



BG.save(os.path.join(BG.path(), "AutoBG.h5"))
print("weights saved")


# BG.load(os.path.join(BG.path(), "AutoBG.h5"))


for i in range(10):
    (x_test, y_test) = fetch_data(False, 1)
    
    # encode and decode some crops
    # note that we take them from the *validation* set
    img = BG.model.predict(x_test)
    cv2.imshow("reconst", img.reshape(2336, 1729, 1))
    cv2.waitKey(0)





