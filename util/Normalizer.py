#! /usr/bin/env python
"""
Normalizes a vidoe by dividing against it's background.
See: BackgroundExtractor.py to get the background of a video.

USING:

    As a command line utility:
    
        $ Normalizer.py input_video input_image output_video
    
    As a module:
    
        from Normalizer import Normalizer
        norm = Normalizer("input_video.avi", input_image, "output_video.avi")
        norm.normalize()
        

Author: Martin Humphreys
"""

from argparse import ArgumentParser
import numpy as np
import os
import cv2



class Normalizer:

    def __init__(self):
        pass
        
    def imageFromArg(self, image):
        if isinstance(image, (str, unicode)):
            return cv2.imread(image)
        else:
            return image
        
    def videoReaderFromArg(self, video):
        if isinstance(video, (str, unicode)):
            vc = cv2.VideoCapture((video)
        else:
            vc = video
    
    def normalize(self, background, in_video, out_video, showit = False):
        vc = self.videoReaderFromArg(in_video)
        frames = int(vc.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(vc.get(cv2.CAP_PROP_FPS)) 
        if fps == float('inf'):
            fps = 300
        width = int(self.vc.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.vc.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = int(self.vc.get(cv2.CAP_PROP_FOURCC))
        
        vw = cv2.VideoWriter(outfile, fourcc, fps, (width, height))
        
        self.normalizeVideo(background, vc, vw, showit)
        
    
    def normalizeVideo(self, background, video_reader, video_writer, showit = False):
        f = 1
        while(True):
            ret, frame = video_reader.read()
            if not ret:
                break;
            f += 1
            normal_frame = self.normaliseFrame(background, frame, showit)
            
            video_writer.write(normal_frame)
            
    def normalizeFrame(self, background, frame, showit = False):
        if callable(background):
            bg = background(frame)
        else:
            bg = self.imageFromArg(background)
        
        a = frame
        b = bg
        
        c = a/((b.astype('float')+1)/256)
        d = c*(c < 255)+255*np.ones(np.shape(c))*(c > 255)
        
        if showit:
            cv2.imshow("watch", e)
            cv2.waitKey(1)
            
        return d.astype('uint8')    
            
  
def build_parser():
    parser = ArgumentParser()
    parser.add_argument('input_video', help='video to process')
    parser.add_argument('background', help='background image')
    parser.add_argument('output_video', help='file to save normalized video to')
    return parser


def main():
    parser = build_parser()
    opts = parser.parse_args()
    if not os.path.isfile(opts.input_video):
        parser.error("Video file %s does not exist." % opts.input_video)
    if not os.path.isfile(options.background):
        parser.error("Image file %s does not exist." % opts.background)
    norm = Normalizer()
    norm.normalize(opts.background, opts.input_video, opts.output_video)


if __name__ == '__main__':
    main()
