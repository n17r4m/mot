#! /usr/bin/env python
"""
Retrieve a frame from a video.

USING:

    As a command line utility:
    
        $ LinePipe.py input_bin output_image action
    
    As a module:
        

Author: Martin Humphreys
"""


from argparse import ArgumentParser
import os
import cv2
import numpy as np
from numpy.fft import fft, ifft
from skimage.morphology import watershed
from skimage.feature import peak_local_max
from skimage import segmentation
from skimage import morphology
from scipy import ndimage


class LinePipe(object):
  
    def __init__(self, in_bin, width = 2336):
        if isinstance(in_bin, (str, unicode)):
            self.data = np.fromfile(in_bin, dtype='uint8')
        else:
            self.data = in_bin
        self.width = width
        self.length = self.data[8:12].view(dtype="uint32")
        self.data = self.data[12:].reshape(len(self), width) / 255.0
        self.bg_cache = {"max": None, "mean": None, "median": None}
        
    def __len__(self):
        return self.length
        
    def line(self, line_no=0):
        return self.data[line_no:line_no+1]
    
    def lines(self, line_start=0, nlines=100):
        return self.data[line_start:line_start+nlines]
    
    def transformRange(self, value, oldmin, oldmax, newmin, newmax):
        return (((value - oldmin) * (newmax - newmin)) / (oldmax - oldmin)) + newmin
    
    def bg(self, method="max"):
        if self.bg_cache[method] is not None:
            return self.bg_cache[method]
        sample = self.transformRange(self.random(1000), 0.0, 1.0, 1.0, 256.0)
        if   method == "max":    self.bg_cache["max"]    = np.max(sample, axis=0)
        elif method == "mean":   self.bg_cache["mean"]   = np.mean(sample, axis=0)
        elif method == "median": self.bg_cache["median"] = np.median(sample, axis=0)
        return self.bg_cache[method]
    
    def random(self, n=1000):
        return self.data[np.random.choice(len(self)/10, n, replace=False), :]
    
    def bgdivide(self, line_start=0, nlines=100):
        self.preProc = self.lines(line_start, nlines)
        return self.transformRange(self.preProc, 0.0, 1.0, 1.0, 256.0) / self.bg()
    
    def binarize(self, line_start=0, nlines=100, threshold=127):
        buf = self.bgdivide(line_start, nlines)
        self.normalized = buf
        
        buf[buf>1] = 1
        buf = np.uint8(buf*255)
        buf = 255 - buf
        buf[buf>=threshold] = 255
        buf[buf<threshold] = 0
        
        buf = buf[:,self.width/5:4*self.width/5]
        
        self.preProc = np.uint8(self.preProc*255)
        self.preProc = self.preProc[:,self.width/5:4*self.width/5]
        
        self.normalized[self.normalized>1] = 1
        self.normalized = np.uint8(self.normalized*255)
        self.normalized = self.normalized[:,self.width/5:4*self.width/5]
        
        return buf
    
    
        

def build_parser():
    parser = ArgumentParser()
    parser.add_argument('input_bin', help='line scanner binary data')
    parser.add_argument('action', help='action', default="none")
    parser.add_argument('-s', help='start', type=int, default=10)
    parser.add_argument('-n', help='nlines', type=int, default=1000)
    parser.add_argument('-t', help='binary threshold', type=int, default=127)
    return parser


def main():
    parser = build_parser()
    opts = parser.parse_args()
    if not os.path.isfile(opts.input_bin):
        parser.error("Data file %s does not exist." % opts.input_bin)
    
    pipe = LinePipe(opts.input_bin, 2336)
    
    
    if opts.action == "correlate":
        lines1 = pipe.lines(opts.s, opts.n)
        lines2 = pipe.lines(opts.s+1, opts.n)
        corr = ifft(fft(lines1) * fft(lines2).conj()).real
        out = pipe.transformRange(corr, np.amin(corr), np.amax(corr), 0.0, 1.0)
    
    elif opts.action == "convolve":
        lines1 = pipe.lines(opts.s, opts.n)
        lines2 = pipe.lines(opts.s+1, opts.n)
        
        conv = ifft(fft(lines2) * fft(lines1)).real
        out = pipe.transformRange(conv, np.amin(conv), np.amax(conv), 0.0, 1.0)
    
    elif opts.action == "auto":
        lines1 = pipe.lines(opts.s, opts.n)
        lines2 = pipe.lines(opts.s+1, opts.n)
        
        corr = np.zeros_like(lines1)
        for i in range(len(corr)):
            corr[i] = np.correlate(lines1[i], lines2[i], mode="same")
        out = pipe.transformRange(corr, np.amin(corr), np.amax(corr), 0.0, 1.0)
    
    elif opts.action == "divide":
        lines1 = pipe.lines(opts.s, opts.n) + 0.0001
        lines2 = pipe.lines(opts.s+1, opts.n) + 0.0001
        div = lines1 / lines2
        out = pipe.transformRange(div, np.amin(div), np.amax(div), 0.0, 1.0)
    
    elif opts.action == "subtract":
        lines1 = pipe.lines(opts.s, opts.n)
        lines2 = pipe.lines(opts.s+1, opts.n)
        div = lines1 - lines2
        out = pipe.transformRange(div, np.amin(div), np.amax(div), 0.0, 1.0)
    
    elif opts.action == "canny":
        lines = pipe.lines(opts.s, opts.n)
        lines = pipe.transformRange(lines, 0.0, 1.0, 0.0, 255.0)
        out = cv2.Canny(lines.astype('uint8'), 30, 100, 5)
    
    elif opts.action == "canny2":
        bg = np.mean(pipe.transformRange(pipe.lines(10, 10), 0.0, 1.0, 1.0, 256.0), axis=0)
        lines = pipe.transformRange(pipe.lines(opts.s, opts.n), 0.0, 1.0, 1.0, 256.0)
        lines = pipe.transformRange(lines / bg, 0.0, 1.0, 0.0, 255.0)
        lines = cv2.blur(lines,(3,3))
        out = 1.0 - cv2.Canny(lines.astype('uint8'), 30, 100, 5)
    
    elif opts.action == "bgsubtract":
        bg = np.mean(pipe.lines(10, 10), axis=0)
        lines = pipe.lines(opts.s, opts.n)
        lines = lines - bg
        lines = pipe.transformRange(lines, np.amin(lines), np.amax(lines), 0.0, 1.0)
        out = lines
    
    elif opts.action == "bgdivide":
        out = pipe.bgdivide(opts.s, opts.n)
        
    elif opts.action == "binarize":
        out = pipe.binarize(opts.s, opts.n, opts.t)
    
    elif opts.action == "segment":
        bg = np.mean(pipe.transformRange(pipe.lines(10, 10), 0.0, 1.0, 1.0, 256.0), axis=0)
        lines = pipe.transformRange(pipe.lines(opts.s, opts.n), 0.0, 1.0, 1.0, 256.0)
        lines = lines / bg
        lines = ndimage.median_filter(lines, 3)
        bmask = lines < 0.75#.astype('float32')
        
        distance = ndimage.distance_transform_edt(bmask)
        local_maxi = peak_local_max(distance, indices=False, footprint=np.ones((9, 9)), labels=bmask)
        
        markers = morphology.label(local_maxi)
        
        markers[~bmask] = -1
        labels_ws = watershed(-distance, markers, mask=bmask)
        
        out = (labels_ws.astype('uint8') + 100)
        
    
    elif opts.action == "bgsobel":
        bg = np.mean(pipe.transformRange(pipe.lines(10, 10), 0.0, 1.0, 1.0, 256.0), axis=0)
        lines = pipe.transformRange(pipe.lines(opts.s, opts.n), 0.0, 1.0, 1.0, 256.0)
        lines = lines / bg
        lines = lines.astype("float32")
        #lines = ndimage.median_filter(lines, 3)
        #lines = cv2.bilateralFilter(lines, 3,75,75)
        lines = lines.astype('float32')
        sx = ndimage.sobel(lines, axis=0, mode='constant')
        sy = ndimage.sobel(lines, axis=1, mode='constant')
        sob = np.hypot(sx, sy)
        #binary_img = sob > 0.3
        #open_img = ndimage.binary_opening(binary_img)
        #close_img = ndimage.binary_closing(open_img)
        out = sob
        #out = close_img.astype("float32")
    else: # action = none|normal
        out = pipe.lines(opts.s, opts.n)
    
    if opts.action == "view":
        for i in xrange(0, len(pipe), opts.s):
            print(i)
            lines = pipe.lines(i, opts.n)
            cv2.imshow("view", lines)
            cv2.waitKey(10)
        out = None
    else:
        out = cv2.resize(out, dsize=(0,0), fx=0.5, fy=0.5)
        preProc = cv2.resize(pipe.preProc, dsize=(0,0), fx=0.5, fy=0.5)
        cv2.imwrite('../data/linescan/raw.png', preProc)
        cv2.imwrite('../data/linescan/proc.png', out)
        # cv2.imshow("out", out)
        # cv2.waitKey(0)

if __name__ == '__main__':
    main()
 
