#! /usr/bin/env python
"""
Calculate the difference between an image and a video

USING:

    As a command line utility:
    
        $ VideoDifference.py input_video input_image output_video
    
    As a module:
    
        import VideoDifference
        dif = VideoDifference("input_video.avi", input_image)
        

Author: Martin Humphreys
"""

from argparse import ArgumentParser
from skimage.feature import peak_local_max
from skimage.morphology import watershed
from scipy import ndimage
import numpy as np
import os
import cv2


class VideoDifference:

    def __init__(self, infile, image, outfile):
        self.vc = cv2.VideoCapture(infile)
        self.frames = int(self.vc.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = float(self.vc.get(cv2.CAP_PROP_FPS))
        self.width = int(self.vc.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.vc.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fourcc = int(self.vc.get(cv2.CAP_PROP_FOURCC))
        self.vw = cv2.VideoWriter(outfile, self.fourcc, self.fps, (self.width, self.height))
        if isinstance(image, str):
            bg = cv2.imread(image)
        else:
            bg = image
        self.bg = cv2.cvtColor(bg, cv2.COLOR_RGB2GRAY)
    
    def difference2(self):
        f = 1
        while(True):
            ret, frame = self.vc.read()
            if not ret:
                break;
            dframe = cv2.pyrMeanShiftFiltering(frame, 21, 51)
            gray = cv2.cvtColor(dframe, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
            
            # loop over the contours
            for (i, c) in enumerate(cnts):
	            # draw the contour
	            ((x, y), _) = cv2.minEnclosingCircle(c)
	            cv2.putText(frame, "#{}".format(i + 1), (int(x) - 10, int(y)),
		            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
	            cv2.drawContours(frame, [c], -1, (0, 255, 0), 2)
            self.vw.write(dframe)
    
    def difference(self):
        f = 1
        while(True):
            ret, frame = self.vc.read()
            if not ret:
                break;
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            dframe = cv2.absdiff(frame, self.bg)
            mean = cv2.mean(dframe)
            dframe = cv2.subtract(dframe, mean)
            dframe = cv2.subtract((255,255,255,255), dframe)
            dframe = self.adjust_gamma(dframe, 0.5)
            dframe = cv2.blur(dframe,(16,16))
            thresh = cv2.threshold(dframe, 170, 255, cv2.THRESH_BINARY_INV)[1]
            dframe = 255 - cv2.bitwise_and(255 - frame, thresh)
            dframe = cv2.cvtColor(dframe, cv2.COLOR_GRAY2RGB)
            self.vw.write(dframe)
    
    def watershed(self, image):
        markers = cv2.findContours(image, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        print markers
        return cv2.watershed(image, markers)
        
    
    # http://www.pyimagesearch.com/2015/10/05/opencv-gamma-correction/
    def adjust_gamma(self, image, gamma=1.0):
	    # build a lookup table mapping the pixel values [0, 255] to
	    # their adjusted gamma values
	    invGamma = 1.0 / gamma
	    table = np.array([((i / 255.0) ** invGamma) * 255
		    for i in np.arange(0, 256)]).astype("uint8")
     
	    # apply gamma correction using the lookup table
	    return cv2.LUT(image, table)
            
  
  
def build_parser():
    parser = ArgumentParser()
    parser.add_argument('input_video', help='video to process')
    parser.add_argument('input_image', help='image to subtract')
    parser.add_argument('output_video', help='file to save video to')
    return parser


def main():
    parser = build_parser()
    options = parser.parse_args()
    if not os.path.isfile(options.input_video):
        parser.error("Video file %s does not exist." % options.input_video)
    if not os.path.isfile(options.input_image):
        parser.error("Image file %s does not exist." % options.input_image)
    dif = VideoDifference(options.input_video, options.input_image, options.output_video)
    dif.difference()


if __name__ == '__main__':
    main()
