#------------------------------------------------------------------------------#
#                                                                              #
#  A tracking example                                                          #
#  In iPython: copy -> %paste the following in the interpreter                 #
#                                                                              #
#------------------------------------------------------------------------------#

import os

from DataBag import DataBag
from Tracker import TrackerV2 as Tracker

# Destroy previous results if they exist
if os.path.isfile("../data/bags/validation/val1_trackingExample.db"):
    os.remove("../data/bags/validation/val1_trackingExample.db")

# Load a databag with precomputed detection results
bag = DataBag('../data/bags/validation/val1_detection.db')

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

# View the results
tracking_bag = DataBag("../data/bags/validation/val1_trackingExample.db")
tracking_bag.query("select * from assoc")