#! /usr/bin/env python
"""
Retrieve a frame from a video.

USING:

    As a command line utility:
    
        $ FrameGrabber.py input_video frame_no output_image [--gray]
    
    As a module:
        from FrameGrabber import FrameGrabber
        frameGrabber = FrameGrabber(input_video)
        frame = frameGrabber.frame(frame_no[, gray=False])

Author: Martin Humphreys / Kevin Gordon
"""


from argparse import ArgumentParser
import os
# import cv2
import pims
import numpy as np
from skimage.color import rgb2gray

class FrameGrabber:
  
    def __init__(self, in_video):
        self.vc = self.videoReaderFromArg(in_video)
        self.frames = len(self.vc)
        self.height, self.width, _ = self.vc[0].shape
        self.shape = (self.height, self.width)
    
    def __len__(self):
        return self.frames

    def frame(self, frame_no=0, gray=True):
        
        frame = self.vc[frame_no]
        
        if not len(frame):
            print("Error reading video frame " + str(frame_no) + " ...")
        else:
            if gray:
                frame =rgb2gray(frame)
            
        return frame

    def videoReaderFromArg(self, video):
        if isinstance(video, str):
            vc = pims.open(video)
            self.video_path = video
        else:
            vc = video
        return vc

def build_parser():
    parser = ArgumentParser()
    parser.add_argument('input_video', help='video to extract from')
    parser.add_argument('frame_no', help='frame number to extract', type=int)
    parser.add_argument('output_image', help='file to save extracted frame to')
    parser.add_argument('--gray', help='output file as grayscale image', action = 'store_true')
    return parser


def main():
    parser = build_parser()
    options = parser.parse_args()
    if not os.path.isfile(options.input_video):
        parser.error("Video file %s does not exist." % options.input_video)
    
    grabber = FrameGrabber(options.input_video)
    
    if not options.frame_no > 0 and options.frame_no < grabber.frames :
        parser.error("Frame %{no} out of range (%{r})" % {"n": options.frame_no, "r": grabber.frames} )
    
    frame = grabber.frame(options.frame_no, options.gray)
    cv2.imwrite(options.output_image, frame)

if __name__ == '__main__':
    main()
 
