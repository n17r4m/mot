### An example of using the DataBag to store/retrieve intermediate results
import cv2
import numpy as np

import time

from BackgroundExtractor import AverageExtractor
from FrameGrabber import FrameGrabber
from ForegroundExtractor import NormalizedForegroundExtractorV2 as NormalizedForegroundExtractor
from BinaryExtractor import BinaryExtractor
from ComponentExtractor import ComponentExtractorV2 as ComponentExtractor
from DataBag import DataBag
# from Tracker import Tracker

### Setup path and video info ###
path = '../data/videos/validation/'
tmp = 'tmp/'

video_name = 'val1'
video_ext = '.avi'

### Get background ###
background = cv2.imread('../data/backgrounds/'+video_name+'_background.png', cv2.IMREAD_GRAYSCALE)

bg_ext = AverageExtractor(path+video_name+video_ext)
if background is None:
    background = bg_ext.extract()
    cv2.imwrite('../data/backgrounds/'+video_name+'_background.png', background)
background = background[:-1,:]

N_frames = bg_ext.frames

dbName = "../data/bags/tmp" + video_name + ".db"

bag = DataBag(dbName)
# bag = None
frameGrabber = FrameGrabber(path+video_name+video_ext)
fg_ext = NormalizedForegroundExtractor(background)
bin_ext = BinaryExtractor(invert=True, threshold=217)
comp_ext = ComponentExtractor(bag, save_binary=True)

shape = background.shape[1] * 3, background.shape[0]
vw = cv2.VideoWriter('../data/videos/tmp/' + video_name + '.mp4', 
                     33, 
                     10, 
                     shape, 
                     False)

start = time.time()
for i in range(N_frames):
# for i in range(100):
    frame = frameGrabber.frame(i)

    ### Enhance foreground ###
    fg = fg_ext.extract(frame)

    ### Extract binary foreground ###
    fg_bin = bin_ext.extract(fg)

    ### Extract component data ###
    component_data = comp_ext.extract(i, fg_bin, fg)

    ### Save the results for manual inspection ###
    vw.write(np.concatenate([fg_bin, fg, frame], axis=1))

    if i % 10 == 0 and i != 0:
        print "batch " + str(i/10) + " took",  time.time() - start, "seconds"
        start = time.time()

### Commit our changes to the database ###
bag.batchCommit()
vw.release()
