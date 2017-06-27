### An example of detection using the databag ###
import cv2
import numpy as np

from BackgroundExtractor import AverageExtractor
from FrameGrabber import FrameGrabber
from ForegroundExtractor import NormalizedForegroundExtractorV2 as NormalizedForegroundExtractor
from BinaryExtractor import BinaryExtractor
from ComponentExtractor import ComponentExtractorV2 as ComponentExtractor
from DataBag import DataBag

import os

videos_path = "../data/videos/"
bags_path = "../data/bags/"
backgrounds_path = "../data/backgrounds/"
inspections_path = "../data/videos/inspection/"

batch_directory = 'BU-2015-09-14'

### create the directories
if not os.path.isdir(backgrounds_path + batch_directory):
    os.mkdir(backgrounds_path + batch_directory)
if not os.path.isdir(inspections_path + batch_directory):
    os.mkdir(inspections_path + batch_directory)
if not os.path.isdir(bags_path + batch_directory):
    os.mkdir(bags_path + batch_directory)

for file in os.listdir(videos_path + batch_directory):
    if not file.endswith(".avi"):
        continue
        
    print 'processing', os.path.join(videos_path + batch_directory, file)
    video_name = batch_directory + '/' + file.split('.')[0]

    ### Get background ###
    # Try to load from pre-computed background first
    background = cv2.imread(backgrounds_path + video_name + '_background.png', cv2.IMREAD_GRAYSCALE)
    bg_ext = AverageExtractor(videos_path + video_name + '.avi')

    # If no background found, compute it
    if background is None:
        background = bg_ext.extract(verbose=True)
        cv2.imwrite(backgrounds_path + video_name + '_background.png', background)
    ### End get background ###

    ### Init our utilities
    frameGrabber = FrameGrabber(videos_path + video_name + '.avi')
    fg_ext = NormalizedForegroundExtractor(background)
    bin_ext = BinaryExtractor(invert=True, threshold=217)
    bag = DataBag(bags_path + video_name + '.db')
    comp_ext = ComponentExtractor(bag, save_binary=False)
    ### End Init our utilities


    ### Manual inspection video
    shape = background.shape[1] * 3, background.shape[0]
    vw = cv2.VideoWriter(inspections_path + video_name + '.mp4', 
                         33, 
                         30, 
                         shape, 
                         False)
    ### End Manual inspection video

    N_frames = bg_ext.frames

    for i in range(N_frames):
        if i%10==0:
            print video_name + ": processing batch", i/10
    
        ### Get the frame ###
        frame = frameGrabber.frame(i)

        ### Abyssus has a problem reading the last frame... :(
        if frame is None:
            print video_name + ": Error Reading frame " + str(i)
            continue

        ### Enhance foreground ###
        fg = fg_ext.extract(frame)

        ### Extract binary foreground ###
        fg_bin = bin_ext.extract(fg)

        ### Extract component data ###
        component_data = comp_ext.extract(i, fg_bin, fg)

        ### Save results to manual inspection video
        vw.write(np.concatenate([fg_bin, fg, frame], axis=1))

    ### Commit our changes to the database ###
    bag.batchCommit()
    vw.release()
