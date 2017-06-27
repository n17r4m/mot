#! /usr/bin/env python
"""
Calculate the difference between an image and a video

USING:

    As a command line utility:
    
        $ FrameGrabber.py input_video frame_no output_image
    
    As a module:
    
        import VideoDifference
        dif = VideoDifference("input_video.avi", input_image)
        bg = dif.difference()

Author: Martin Humphreys
"""


from argparse import ArgumentParser
import os
import cv2
import numpy as np


class FrameGrabber:
  
    def __init__(self, filename):
        self.vc = cv2.VideoCapture(filename)
        self.frames = int(self.vc.get(cv2.CAP_PROP_FRAME_COUNT))
    
    def frame(self, frame=0, gray=True):
        self.vc.set(cv2.CAP_PROP_POS_FRAMES, frame)
        ret, frame = self.vc.read()
        if gray:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return frame


def build_parser():
    parser = ArgumentParser()
    parser.add_argument('input_video', help='video to extract from')
    parser.add_argument('frame_no', help='frame number to extract', type=int)
    parser.add_argument('output_image', help='file to save extracted frame to')
    return parser


def main():
    parser = build_parser()
    options = parser.parse_args()
    if not os.path.isfile(options.input_video):
        parser.error("Video file %s does not exist." % options.input_video)
    
    grabber = FrameGrabber(options.input_video)
    
    if not options.frame_no > 0 and options.frame_no < grabber.frames :
        parser.error("Frame %{no} out of range (%{r})" % {"n": options.frame_no, "r": grabber.frames} )
    
    frame = grabber.frame(options.frame_no)
    cv2.imwrite(options.output_image, frame)

if __name__ == '__main__':
    main()
 
