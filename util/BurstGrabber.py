#! /usr/bin/env python
"""
Grab a burst from a video, returned in an array of nparrays.

In the command line utility, returns a numpy binary.

USING:

    As a command line utility:
    
        $ BurstGrabber.py input_video burst_no, output_binary   , [-len=10]
    
    As a module:
    
        import BurstGrabber
        burstGrabber = BurstGrabber("input_video.avi")
        burst = burstGrabber.burst(burst_no)

Author: Kevin Gordon
"""


from argparse import ArgumentParser
import os
import cv2
import numpy as np


class BurstGrabber:
  
    def __init__(self, filename):
        self.vc = cv2.VideoCapture(filename)
        self.frames = int(self.vc.get(cv2.CAP_PROP_FRAME_COUNT))
    
    def burst(self, burst_no=0, burst_len=10):
        frame_no = burst_len * burst_no

        self.vc.set(cv2.CAP_PROP_POS_FRAMES, frame_no)

        out = []

        for i in range(burst_len):
            ret, frame = self.vc.read()

            if ret:            
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                out.append(frame)
            else:
                print "Error reading video frame " + str(i) + " ..."

        return out

def build_parser():
    parser = ArgumentParser()
    parser.add_argument('input_video', help='video to extract from')
    parser.add_argument('burst_no', help='burst number to extract', type=int)
    parser.add_argument('output_binary', 
                        help='file to save extracted burst to')
    parser.add_argument('-len', 
                        help='number of frames in a burst',
                        type=int,
                        default=10)
    return parser

def main():
    parser = build_parser()
    options = parser.parse_args()
    if not os.path.isfile(options.input_video):
        parser.error("Video file %s does not exist." % options.input_video)
    
    grabber = BurstGrabber(options.input_video)
    
    if not options.burst_no*options.len >= 0 and options.burst_no*options.len < grabber.frames :
        parser.error("Frame %{no} out of range (%{r})" % {"n": options.burst_no*options.len, "r": grabber.frames} )
    
    burst = grabber.burst(options.burst_no, options.len)

    np.save(options.output_binary, np.array(burst))

if __name__ == '__main__':
    main()
 
