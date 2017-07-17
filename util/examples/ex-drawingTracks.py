#------------------------------------------------------------------------------#
#                                                                              #
#  A tracking result drawing example                                           #
#  In iPython: copy -> %paste the following in the interpreter                 #
#                                                                              #
#------------------------------------------------------------------------------#

from DataBag import DataBag
from BurstGrabber import BurstGrabber
from BagDrawing import drawTracks, drawTrack

from functions_cv3 import *
%matplotlib tk

# Init a burstgrabber
bgrabber = BurstGrabber('../data/videos/validation/val1.avi')

# Load a burst
burst = bgrabber.burst(0)

# Load in the tracking results
bag = DataBag('../data/bags/validation/val1_trackingExample.db')

# Draw all tracks
a = drawTracks(bag, burst, 0, 10)

# Display the resutls
disp_seq(a)