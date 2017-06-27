#! /usr/bin/env python
"""
Deprecated. Please see Simulation.py and Bag2Video.py

USING:

    As a command line utility:
    
    ./Simulator.py  [-h] [-n NUM] [-fps FPS] [-d DROP_DIR] [-s SAND_DIR]
                    [-dn DROP_NUM] [-dvm DROP_VEL_MEAN] [-dvv DROP_VEL_VAR]
                    [-dsm DROP_SIZE_MEAN] [-dsv DROP_SIZE_VAR] [-sn SAND_NUM]
                    [-svm SAND_VEL_MEAN] [-svv SAND_VEL_VAR]
                    [-ssm SAND_SIZE_MEAN] [-ssv SAND_SIZE_VAR] [-b BAG] [-v]
                    [-p]
                    bg output_video
    
    As a module:
    
        Untested

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
import numpy as np

# This will be system specific, depending on OpenCV config
# ... Maybe not actually, I need 0 for .avi, and 33 for .mp4
#     may have always been a codec difference ...
FOURCC = 0

class Particle:
    def __init__(self, sim, id_gen, vm, vv, sprite):
        self.id_gen = id_gen
        self.id = self.id_gen()
        self.sim = sim
        self.sx = random.randint(0, sim.width-1)
        self.sy = random.randint(0, sim.height-1)
        self.vy = np.random.normal(vm, vv)
        self.sprite = self.augment(sprite)
        
    def tick(self, n):
        
        self.x = self.sx
        
        _y = self.sy + (self.vy * n)
        y = _y % self.sim.height 
        if _y != y:
            self.id = self.id_gen()    
        self.y = y
    
    def augment(self, sprite):
        """
        sprite = np.rot90(sprite, random.randint(0,3))
        if random.randint(0,1):
            sprite = cv2.flip(sprite, 0)
        if random.randint(0,1):
            sprite = cv2.flip(sprite, 1)
        """
        return sprite
        
    def rect(self):
        h, w, c = self.sprite.shape
        h2, w2 = floor(h / 2), floor(w / 2)
        mw, mh = self.sim.width - 1, self.sim.height - 1
        fy1, fy2 = int(max(0, self.y - h2)), int(min(mh, self.y + h2))
        fx1, fx2 = int(max(0, self.x - w2)), int(min(mw, self.x + w2))
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

class Simulator:
  
    def __init__(self, opts):
        global FOURCC
        self.opts = opts
        self.save_bitmask = self.opts.p
        self.verbose = self.opts.v
        if self.verbose:
            print "initializing..."
            
        if isinstance(opts.bg, str):
            self.bg = cv2.imread(opts.bg)
        else:
            self.bg = opts.bg

        self.height, self.width, self.channels = self.bg.shape
        self.vw = cv2.VideoWriter(opts.output_video, FOURCC , opts.fps, (self.width, self.height), False)
        self.bag = DataBag(opts.bag, verbose = self.verbose)

        self.particles = []

        self.drop_sprites = self.loadSprites(self.opts.drop_dir)
        self.sand_sprites = self.drop_sprites
        # self.sand_sprites = self.loadSprites(self.opts.sand_dir)
        def counter(first = 1):
            current = [first - 1]
            def next():
                current[0] += 1
                return current[0]
            return next
        
        id_gen = counter() 

        if self.verbose:
            print "sprites loaded..."

        # If we do not specify a mean drop size, we instead randomly sample the 
        #  loaded sprites
        if not self.opts.drop_size_mean:        
            l = []
            for k,v in self.drop_sprites.iteritems():
                l.extend(len(v)*[int(k)])

            count = 0
            # for n in range(opts.drop_num):
            while (count < opts.drop_num):
                size = random.choice(l)
                if size < 150:
                    continue

                sprite = random.choice(self.drop_sprites[size])
                p = Particle(self, id_gen, opts.drop_vel_mean,  opts.drop_vel_var, sprite)
                self.particles.append(p)
                self.bag.insertParticle(size, p.id)
                count +=1
        else:
            strkeys = self.drop_sprites.keys()
            intkeys = map(int, strkeys)
            for n in range(opts.drop_num):
                while True:
                    size = str(int(round(np.random.normal(opts.drop_size_mean, opts.drop_size_var))))                    
                    if size in strkeys:
                        break;
                sprite = random.choice(self.drop_sprites[size])
                p = Particle(self, id_gen, opts.drop_vel_mean,  opts.drop_vel_var, sprite)
                self.particles.append(p)
                self.bag.insertParticle(3.14159 * ((float(size)/2.0)**2), 1, p.id)

        if self.verbose:
            print "drop selection complete..."

        # If we do not specify a mean sand size, we instead randomly sample the 
        #  loaded sprites
        if not self.opts.sand_size_mean:        
            l = []
            for k,v in self.sand_sprites.iteritems():
                l.extend(len(v)*[int(k)])

            count = 0
            # for n in range(opts.drop_num):
            while (count < opts.sand_num):
                size = random.choice(l)
                # if size < 50:
                #     continue
                sprite = random.choice(self.sand_sprites[size])
                p = Particle(self, count, size, opts.sand_vel_mean,  opts.sand_vel_var, sprite)
                self.particles.append(p)
                self.bag.insertParticle(size, p.id)
                count +=1
        else:
            strkeys = self.sand_sprites.keys()
            intkeys = map(int, strkeys)
            for n in range(opts.sand_num):
                while True:
                    size = str(int(round(np.random.normal(opts.sand_size_mean, opts.sand_size_var))))
                    if size in strkeys:
                        break;
                sprite = random.choice(self.sand_sprites[size])
                self.particles.append(Particle(self, id_gen, opts.sand_vel_mean,  opts.sand_vel_var, sprite))

        if self.verbose:
            print "sand selection complete..."

        # sprite = cv2.cvtColor(random.choice(self.sand_sprites[size]), cv2.COLOR_GRAY2RGBA)

        random.shuffle(self.particles)

        
    
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
        binary_mask = np.zeros((self.height, self.width), dtype=np.bool8)
        for p in self.particles:
            p.tick(n)
            self.bag.insertAssoc(n-1, p.id, p.x, p.y)
            p.paint(frame)            
            self.blackbar(frame)
            p.paint_binary(binary_mask)

        if self.save_bitmask:
            self.bag.insertFrame(n-1, binary_mask)
        else:
            self.bag.insertFrame(n-1)

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
                
    def generate(self, outfile, n=10):
        if self.verbose:
            print "generating frames..."
    
        for n in range(1, n+1):
            if self.verbose:
                print "frame ", n, ' ...'
            frame = self.frame(n)            
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = self.fines(frame)       
            frame = np.uint8(frame)
            self.vw.write(frame)


def build_parser():
    parser = ArgumentParser()
    
    parser.add_argument('bg', help='The background image to use')
    parser.add_argument('output_video', help='file to save simulated video to')
    
    
    parser.add_argument("-n", "--num", help="number of frames to generate", type=int, default=10)    
    parser.add_argument("-fps", "--fps", help="frames per second", type=int, default=300)
    parser.add_argument("-d", "--drop_dir", help="dir or path to drop sprites", default="drop")
    parser.add_argument("-s", "--sand_dir", help="dir or path to sand sprites", default="sand")
    
    parser.add_argument("-dn",  "--drop_num", help="number of drops", type=int, default=250)
    parser.add_argument("-dvm", "--drop_vel_mean", help="drop velocity mean", type=float, default=-2.5)
    parser.add_argument("-dvv", "--drop_vel_var", help="drop velocity variance", type=float, default=3)
    parser.add_argument("-dsm", "--drop_size_mean", help="drop size mean; 0 to randomly sample loaded drops", type=float, default=8)
    parser.add_argument("-dsv", "--drop_size_var", help="drop size variance", type=float, default=10)    

    parser.add_argument("-sn",  "--sand_num", help="number of sand particles", type=int, default=300)
    parser.add_argument("-svm", "--sand_vel_mean", help="sand velocity mean", type=float, default=1)
    parser.add_argument("-svv", "--sand_vel_var", help="sand velocity variance", type=float, default=1)
    parser.add_argument("-ssm", "--sand_size_mean", help="sand size mean; 0 to randomly sample loaded sand", type=float, default=8)
    parser.add_argument("-ssv", "--sand_size_var", help="sand size variance", type=float, default=6)

    parser.add_argument("-b", "--bag", help="bag file to save to", type=str, default=":memory:")
    parser.add_argument('-v', help='print verbose statements while executing', 
                              action = 'store_true')    
    parser.add_argument('-p', help='Store the png bitmask image for detection validation; slows frame generation', action = 'store_true')

    return parser


def main(opts):
    if not os.path.isfile(opts.bg):
        parser.error("Background image file %s does not exist." % opts.bg)
    sim = Simulator(opts)
    sim.generate(opts.output_video, opts.num)

if __name__ == '__main__':
    main(build_parser().parse_args())
 
