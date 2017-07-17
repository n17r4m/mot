#------------------------------------------------------------------------------#
#                                                                              #
#  A detection  example                                                        #
#  In iPython: copy -> %paste the following in the interpreter                 #
#                                                                              #
#------------------------------------------------------------------------------#

import cv2
import os

from FrameGrabber import FrameGrabber
from ForegroundExtractor import NormalizedForegroundExtractorV2 \
                             as NormalizedForegroundExtractor
from BinaryExtractor import BinaryExtractor
from ComponentExtractor import ComponentExtractorV2 as ComponentExtractor
from DataBag import DataBag

# Destroy previous results if they exist
if os.path.isfile("../data/bags/val1_detectionExample.db"):
    os.remove("../data/bags/val1_detectionExample.db")

# Load in a pre-computed background (see ex-backgroundExtraction to compute)
background = cv2.imread('../data/backgrounds/validation/val1_background.png', 
                        cv2.IMREAD_GRAYSCALE)

# Init a frame grabber with the video
frameGrabber = FrameGrabber('../data/videos/validation/val1.avi')

# Init the foreground extractor with a background model
fg_ext = NormalizedForegroundExtractor(background)

# Init the binary extractor, setting the threshold hyperparameter
#  note that we invert the image s.t. the droplets are high-valued
#  and the background is low-valued
bin_ext = BinaryExtractor(invert=True, threshold=217)

# Create a databag to store the detection results
bag = DataBag("../data/bags/val1_detectionExample.db")

# Init a component extractor, passing in a databag.
# Note that we can optionally save the computed binary image
#  in the databag for later retreival
comp_ext = ComponentExtractor(bag, save_binary=False)

N_frames = frameGrabber.frames

for i in range(N_frames):
    # Get the frame
    frame = frameGrabber.frame(i)

    # Enhance foreground
    fg = fg_ext.extract(frame)

    # Extract binary foreground
    fg_bin = bin_ext.extract(fg)

    # Extract component data
    component_data = comp_ext.extract(i, fg_bin, fg)

# Commit our changes to the database ###
bag.batchCommit()

# View the results
bag.query('select * from assoc')