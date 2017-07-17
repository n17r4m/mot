#------------------------------------------------------------------------------#
#                                                                              #
#  A background -> detection -> tracking pipeline example                      #
#  In iPython: copy -> %paste the following in the interpreter                 #
#                                                                              #
#------------------------------------------------------------------------------#

import os

from BackgroundExtractor import AverageExtractor
from FrameGrabber import FrameGrabber
from BurstGrabber import BurstGrabber
from ForegroundExtractor import NormalizedForegroundExtractorV2 \
                             as NormalizedForegroundExtractor
from BinaryExtractor import BinaryExtractor
from ComponentExtractor import ComponentExtractorV2 as ComponentExtractor
from Tracker import TrackerV2 as Tracker
from DataBag import DataBag
from BagDrawing import drawTracks

from functions_cv3 import disp_seq
%matplotlib tk

#--------------------------------- Clean Up -----------------------------------#
# Destroy previous results if they exist
if os.path.isfile("../data/bags/val1_detectionExample.db"):
    os.remove("../data/bags/val1_detectionExample.db")

if os.path.isfile("../data/bags/validation/val1_trackingExample.db"):
    os.remove("../data/bags/validation/val1_trackingExample.db")

#---------------------------- Compute Background ------------------------------#
# Init the classes that will perform the extraction
avg_bg_ext = AverageExtractor('../data/videos/validation/val1.avi')

# Compute the background
background = avg_bg_ext.extract()

#---------------------------- Perform Detection -------------------------------#
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

#----------------------------- Perform Tracking -------------------------------#
# Init a tracker, passing in a databag
tracker = Tracker(bag, verbose=True)

# Build the graph for the frames in the inputted range
tracker.build(0, 10)

# Solve the min-cost flow for the inputted number of tracks
tracker.solve(100)

# Reconstruct the paths from the min-cost solution
tracker.reconstruct_paths()

# Save the results in the databag
tracker.save_paths("../data/bags/validation/val1_trackingExample.db")

#---------------------------- Display the Results -----------------------------#
# Load the tracking results
tracking_bag = DataBag("../data/bags/validation/val1_trackingExample.db")

# Init a burstgrabber
bgrabber = BurstGrabber('../data/videos/validation/val1.avi')

# Load a burst
burst = bgrabber.burst(0)

# Draw all tracks
results = drawTracks(tracking_bag, burst, 0, 10)

# Display the resutls
disp_seq(results)