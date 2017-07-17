#------------------------------------------------------------------------------#
#                                                                              #
#  A background extraction example                                             #
#  In iPython: copy -> %paste the following in the interpreter                 #
#                                                                              #
#------------------------------------------------------------------------------#

from BackgroundExtractor import AverageExtractor, MaximumExtractor, \
                                SimpleExtractor, BackgroundExtractor
from functions_cv3 import disp_four
%matplotlib tk

# Init the classes that will perform the background extraction
# Average over the entire video
avg_bg_ext = AverageExtractor('../data/videos/validation/val1.avi')
# Maximum over the entire video
max_bg_ext = MaximumExtractor('../data/videos/validation/val1.avi')
# Maximum over the first 10 frames
simple_bg_ext = SimpleExtractor('../data/videos/validation/val1.avi')
# Running average
running_ext = BackgroundExtractor('../data/videos/validation/val1.avi')

# Compute the backgrounds
avg_background = avg_bg_ext.extract()
max_background = max_bg_ext.extract()
simple_background = simple_bg_ext.extract()
running_background = running_ext.extract()

# Display the results
disp_four(avg_background, max_background, simple_background, running_background)