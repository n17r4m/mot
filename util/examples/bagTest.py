### An example of using the DataBag to store/retrieve intermediate results
### We read a simulated video
### Note: Apr 28, cannot read/store to ../data
### Note: Apr 29, at least 1 OoM slower than local...?
### An example of using the DataBag to store/retrieve intermediate results
import cv2
import numpy as np
import time

from functions_cv3 import *

from BackgroundExtractor import SimpleExtractor
from FrameGrabber import FrameGrabber
from ForegroundExtractor import NormalizedForegroundExtractorV2 as NormalizedForegroundExtractor
from BinaryExtractor import BinaryExtractor
from ComponentExtractor import ComponentExtractorV2 as ComponentExtractor
from DataBag import DataBag
# from Tracker import Tracker

### Setup path and video info ###
path = '../data/videos/'

video_name = 'T02604'
video_ext = '.avi'

### Get background ###
background = cv2.imread('../data/backgrounds/'+video_name+'_background.png', cv2.IMREAD_GRAYSCALE)

bg_ext = SimpleExtractor(path+video_name+video_ext)
if background is None:
    background = bg_ext.extract()


N_frames = bg_ext.frames

dbName = "../data/bags/" + video_name + ".db"

bag = DataBag(dbName)
# bag = None
frameGrabber = FrameGrabber(path+video_name+video_ext)
fg_ext = NormalizedForegroundExtractor(background)
bin_ext = BinaryExtractor(invert=True, threshold=217)
comp_ext = ComponentExtractor(bag)

results = []

start = time.time()
for i in range(N_frames):
    frame = frameGrabber.frame(i)

    ### Enhance foreground ###
    fg = fg_ext.extract(frame)

    ### Extract binary foreground ###
    fg_bin = bin_ext.extract(fg)

    ### Extract component data ###
    component_data = comp_ext.extract(i, fg_bin, fg)

    ### Save the results for manual inspection ###
    results.append(np.concatenate([fg_bin, fg], axis=1))

    if i % 10 == 0 and i != 0:
        print "batch " + str(i/10) + " took",  time.time() - start, "seconds"
        start = time.time()

### Commit our changes to the database ###
bag.batchCommit()
### Save the video results to disk ###
save_video(results, '../data/videos/detection/' + video_name, True, 10)


