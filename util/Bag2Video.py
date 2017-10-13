#! /usr/bin/env python
"""
Converts a DataBag file or object descriptor into a simulated video.


CHANGELOG:
    
    v17.6.8   Now using circles instead of hand-cropped sprites.
              Hopefully, we can eventually use a well trained autoencoder 
              to generate the sprites in the future.

USING:

    As a command line utility:
    
        $ Bag2Video.py bg_image input_bag output_video
    
    As a module:
    
        import Bag2Video from Bag2Video
        b2v = BagToVideo(aDataBagObjectOrFilename, dotdict({"bg": backgroundImage}))
        b2v.generateAndSave("./output_video.avi")
        

Author: Martin Humphreys
"""

import cv2

from argparse import ArgumentParser
from math import floor, ceil
import random
import os
import re
import pickle
import scipy.io
from DataBag import DataBag
from Query import Query
import numpy as np

# This will be system specific, depending on OpenCV config
# ... Maybe not actually, I need 0 for .avi, and 33 for .mp4
#     may have always been a codec difference ...
FOURCC = 33


class dotdict(dict):
  """dot.notation access to dictionary attributes"""
  # https://stackoverflow.com/a/23689767
  __getattr__ = dict.get
  __setattr__ = dict.__setitem__
  __delattr__ = dict.__delitem__


class Particle:
    def __init__(self, b2v, particle):
        self.b2v = b2v
        self.particle = particle
        
        
    def rect(self):
        p = self.particle
        h, w = self.particle.height, self.particle.width
        h2, w2 = floor(h / 2), floor(w / 2)
        mw, mh = self.b2v.width - 1, self.b2v.height - 1
        fy1, fy2 = int(max(0, p.y - h2)), int(min(mh, p.y + h2))
        fx1, fx2 = int(max(0, p.x - w2)), int(min(mw, p.x + w2))
        if h2 * 2 < h:
            if fy2 == mh:
                fy1 -= 1
            else:
                fy2 += 1
        if w2 * 2 < w:
            if fx2 == mw:
                fx1 -= 1
            else:
                fx2 += 1
        
        oy1, oy2 = 0, h
        ox1, ox2 = 0, w
        if fy1 == 0:
            oy1 += h - (fy2 - fy1)
        if fy2 == mh:
            oy2 -= h - (fy2 - fy1)          
        if fx1 == 0:
            ox1 += w - (fx2 - fx1)
        if fx2 == mw:
            ox2 -= w - (fx2 - fx1)
        
        return fy1, fy2, fx1, fx2, oy1, oy2, ox1, ox2
    
    def paint(self, frame):
        # Working withing "transmission space" allows the
        #  blending to be performed as an attenuation of  
        #  any intensity values behind the object being painted.
        
        p = self.particle
        # print p
        if p.id is not None:
            radius = np.sqrt(p.area / np.pi)
            
            cv2.circle(frame, (int(round(p.x)), int(round(p.y))), int(round(radius)), int(round(p.intensity)), -1)
        
        """ OLD sprite painting
        # Get sprite coordinates in the (f)rame and the (o)bject
        fy1, fy2, fx1, fx2, oy1, oy2, ox1, ox2 = self.rect()
        # We'll use the alpha channel as a mask for the blending
        mask = np.float32(self.sprite[oy1:oy2, ox1:ox2, 3] / 255.0)
        # ... first we'll expand the mask a little, then blur for smoother edges
        mask = cv2.dilate(mask, (8,8))
        mask = cv2.blur(mask, (8,8))

        for c in range(0,3):
            bg = frame[fy1:fy2, fx1:fx2, c] * (1-mask)
            fg = frame[fy1:fy2, fx1:fx2, c] * (self.sprite[oy1:oy2, ox1:ox2, c]/255.0) * mask

            frame[fy1:fy2, fx1:fx2, c] = bg + fg
        """
        
        

    def paint_binary(self, frame):
        # Working withing "transmission space" allows the
        #  blending to be performed as an attenuation of  
        #  any intensity values behind the object being painted.

        # Get sprite coordinates in the (f)rame and the (o)bject
        fy1, fy2, fx1, fx2, oy1, oy2, ox1, ox2 = self.rect()

        # We'll use the alpha channel as a mask for the blending
        mask = np.bool8(self.sprite[oy1:oy2, ox1:ox2, 3])
        # ... first we'll expand the mask a little, then blur for smoother edges
        # mask = cv2.dilate(mask, (8,8))
        # mask = cv2.blur(mask, (8,8))
        crop = frame[fy1:fy2, fx1:fx2]
        crop[mask>0] = 1
        
        # for c in range(0,3):
        #     bg = frame[fy1:fy2, fx1:fx2, c] * (1-mask)
        #     fg = frame[fy1:fy2, fx1:fx2, c] * (self.sprite[oy1:oy2, ox1:ox2, c]/255.0) * mask

        #     frame[fy1:fy2, fx1:fx2, c] = bg + fg



class Bag2Video:
  
    def __init__(self, bag, opts):
        global FOURCC
        
        if isinstance(opts, dict):
          opts = dotdict(opts)
          
        self.bag = DataBag.fromArg(bag)
        self.query = Query(self.bag)
        self.opts = opts
        self.verbose = self.opts.v
        
        if self.verbose:
            print "initializing..."
            
        if isinstance(opts.bg, str):
            self.bg = cv2.imread(opts.bg)
        else:
            self.bg = opts.bg

        self.height, self.width, self.channels = self.bg.shape
        self.vw = cv2.VideoWriter(opts.output_video, FOURCC , opts.fps, (self.width, self.height), False)
        
        """
        self.sprites = {
            2: self.loadSprites(self.opts.drop_dir),
            3: self.loadSprites(self.opts.sand_dir),
            4: self.loadSprites(self.opts.bubble_dir)
        }
        
        
        self.sprites[0] = self.sprites[2]
        self.sprites[1] = self.sprites[2]
        
        if self.verbose:
            print "sprites loaded..."
        """
        
        
    
    def loadSprites(self, folder):
        # Are we loading sprite files from a directory, or a pickled sprites file
        if os.path.isdir(folder):
            sprites = {}
            files = os.listdir(folder)
            num_re = re.compile("\d+")
            for sfile in files:
                nums = num_re.findall(sfile)
                sprite = cv2.imread(folder + "/" + sfile, -1)
                if nums[0] in sprites.keys():
                    sprites[nums[0]].append(sprite)
                else:
                    sprites[nums[0]] = [sprite]
        else:
             sprites = pickle.load(open(folder, "rb"))
                
        return sprites
    
    def blackbar(self, frame):
        w = 16
        frame[:, 0:15, :] = 0
    
    def frame(self, n):
        
        frame = self.bg.copy()
        
        particles = self.query.particles_in_frame(n)
        
        for p in particles:
            
            Particle(self, p).paint(frame)            
            

        self.blackbar(frame)

        return frame

    def fines(self, image):
        # Gaussian Noise (only attenuates background intensity)
        #  intended to simulate fines
        row,col= image.shape
        mean = 0
        var = 16
        sigma = var**0.5
        gauss = np.random.normal(mean,sigma,(row,col))
        gauss = (100.0 - gauss)/100.0
        gauss[gauss>1]=1
        gauss = gauss.reshape(row,col)
        frame = image * gauss

        return frame
                
    def generate(self, outfile):
        if self.verbose:
            print "generating frames..."
        
        for f in self.query.frame_list():
            if self.verbose:
                print "frame ", f.frame, ' ...'
            frame = self.frame(f.frame)            
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = self.fines(frame)       
            frame = np.uint8(frame)
            self.vw.write(frame)


def build_parser():
    parser = ArgumentParser()
    
    parser.add_argument('bg', help='The background image to use')
    parser.add_argument('bag', help='The databag file to generate video from')
    parser.add_argument('output_video', help='file to save simulated video to')
    
    
    parser.add_argument("-fps", "--fps", help="frames per second", type=int, default=300)
    #parser.add_argument("-d", "--drop_dir", help="dir or path to drop sprites", default="data/particles/drop")
    #parser.add_argument("-s", "--sand_dir", help="dir or path to sand sprites", default="data/particles/sand")
    #parser.add_argument("-b", "--bubble_dir", help="dir or path to bubble sprites", default="data/particles/bubble")
    
    parser.add_argument('-v', help='print verbose statements while executing', 
                              action = 'store_true')    

    return parser


def main(opts):
    if not os.path.isfile(opts.bg):
        parser.error("Background image file %s does not exist." % opts.bg)
    if not os.path.isfile(opts.bag):
        parser.error("DataBag file %s does not exist." % opts.bag)
        
    b2v = Bag2Video(opts.bag, opts)
    b2v.generate(opts.output_video)

if __name__ == '__main__':
    main(build_parser().parse_args())
 
