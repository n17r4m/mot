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
from math import floor, ceil
from skimage.io import imread
import random
import os
import re
import pickle
import scipy.io
from DataBag import DataBag
import numpy as np

# import cv2

class linear_motion:
    def __init__(self, dx_mean=0, dx_std=0, dy_mean=0, dy_std=0):
        self.dx_mean = dx_mean
        self.dx_std = dx_std
        self.dy_mean = dy_mean
        self.dy_std = dy_std

    def set(self, particle):
        self.particle = particle
        self.dx = np.random.normal(self.dx_mean, self.dx_std)
        self.dy = np.random.normal(self.dy_mean, self.dy_std)

    def tick(self, n):
        x = self.particle.sx + (self.dx * n)
        y = self.particle.sy + (self.dy * n)
        return x, y


class second_order_motion:
    def __init__(self, params):
        self.dx_mean = params['dx_mean']
        self.dx_std = params['dx_std']
        self.dy_mean = params['dy_mean']
        self.dy_std = params['dy_std']
        self.ddx_mean = params['ddx_mean']
        self.ddx_std = params['ddx_std']
        self.ddy_mean = params['ddy_mean']
        self.ddy_std = params['ddy_std']

    def set(self, particle, n):
        self.particle = particle
        self.ddx = np.random.normal(self.ddx_mean, self.ddx_std)
        self.ddy = np.random.normal(self.ddy_mean, self.ddy_std)
        self.dx = np.random.normal(self.dx_mean, self.dx_std) +  self.ddx * n
        self.dy = np.random.normal(self.dy_mean, self.dy_std) + self.ddy * n

    def tick(self, n):
        x = self.particle.sx + (self.dx * (n - self.particle.sn)) + 0.5 * (self.ddx * (n - self.particle.sn) ** 2)
        y = self.particle.sy + (self.dy * (n - self.particle.sn)) + 0.5 * (self.ddy * (n - self.particle.sn) ** 2)
        return x, y

class horizontal_split_motion:
    def __init__(self, params):
        self.dx_mean = params['dx_mean']
        self.dx_std = params['dx_std']
        self.dy_mean = params['dy_mean']
        self.dy_std = params['dy_std']
        self.ddx_mean = params['ddx_mean']
        self.ddx_std = params['ddx_std']
        self.ddy_mean = params['ddy_mean']
        self.ddy_std = params['ddy_std']
        self.split = params['split']
        self.state = 0
        
    def set(self, particle, n):
        self.particle = particle
        self.ddx = np.random.normal(self.ddx_mean, self.ddx_std)
        self.ddy = np.random.normal(self.ddy_mean, self.ddy_std)
        self.dx = np.random.normal(self.dx_mean, self.dx_std) +  self.ddx * n
        self.dy = np.random.normal(self.dy_mean, self.dy_std) + self.ddy * n
        try:
            if self.particle.x > self.split:
                self.dy = -np.abs(self.dy)
            else:
                self.dy = np.abs(self.dy)
        except AttributeError:
            pass
        
    def tick(self, n):
        prev_state = self.state
        
        if self.particle.x > self.split:
            self.dy = -np.abs(self.dy)
            self.state = 1
        elif self.particle.x < self.split:
            self.dy = np.abs(self.dy)
            self.state = -1
        
        if self.state != prev_state:
            self.particle.sn = n
            self.particle.sx = self.particle.x
            self.particle.sy = self.particle.y
            
        x = self.particle.sx + (self.dx * (n - self.particle.sn)) + 0.5 * (self.ddx * (n - self.particle.sn) ** 2)
        y = self.particle.sy + (self.dy * (n - self.particle.sn)) + 0.5 * (self.ddy * (n - self.particle.sn) ** 2)
        return x, y

class Particle:
    def __init__(self, sim, id_gen, motion_model, particle_class, class_sprites):
        self.id_gen = id_gen
        self.sim = sim
        self.motion_model = motion_model
        self.class_sprites = class_sprites

        self.particle_class = particle_class
        if self.particle_class == 'drop':
            self.category = 1
            self.area = 250
        elif self.particle_class == 'sand':
            self.category = 2
            self.area = 100
        
        self.gen()
            
    def gen(self, x=None, y=None, n=None):
        self.id = self.id_gen()
        
        if n is None:
            self.sn = 0
            n = 0
        else:
            self.sn = n  
        
        self.motion_model.set(self, n)
        
        if x is None and y is None:
            self.sx = random.randint(0, self.sim.width-1)
            self.sy = random.randint(0, self.sim.height-1)
        elif x is None:
            if self.motion_model.dx > 0:
                self.sx = 0
            else:
                self.sx = self.sim.width-1
            self.sy = y
        elif y is None:
            if self.motion_model.dy > 0:
                self.sy = 0
            else:
                self.sy = self.sim.height-1
            self.sx = x

        self.x = self.sx
        self.y = self.sy

 
        self.sprite = random.choice(self.class_sprites)
        self.sprite = None
        d = {'id': self.id,
             'area': self.area,
             'category': self.category}

        self.sim.bag.batchInsertParticle(d)

    def tick(self, n):
        _x, _y = self.motion_model.tick(n)
        
        x, y = _x % self.sim.width, _y % self.sim.height        
        
        if _y != y:
            y = None
            self.gen(x, y, n)
        elif _x != x:
            x = None
            self.gen(x, y, n)
        else:    
            self.x, self.y = x, y


class Simulator:
  
    def __init__(self, bag, verbose=True):

        self.verbose = verbose
        if self.verbose:
            print("initializing...")

        self.bag = DataBag(bag, verbose = self.verbose)
        self.detection_bag = DataBag(bag.split('.')[0]+'_detection.'+bag.split('.')[1], verbose = self.verbose)
        self.detection_pid = 0
        
        self.height, self.width = (1000, 1000) 
        drop_num = 100
        sand_num = 0

        drop_params = {'dx_mean': 0,
                       'dx_std': 2,
                       'dy_mean': -10,
                       'dy_std': 2,
                       'ddx_mean': 0,
                       'ddx_std': 0,
                       'ddy_mean': 0.00,
                       'ddy_std': 0,
                       'split': 500,
        }

        sand_params = {'dx_mean': 0,
                       'dx_std': 1,
                       'dy_mean': 5,
                       'dy_std': 1,
                       'ddx_mean': 0,
                       'ddx_std': 0,
                       'ddy_mean': 0.05,
                       'ddy_std': 0,
        }

        self.drop_sprites = self.loadSprites('/local/scratch/mot/data/crops/noscale/training/bitumen/')[:1]
        self.sand_sprites = self.loadSprites('/local/scratch/mot/data/crops/noscale/training/sand/')[:1]

        if self.verbose:
            print("sprites loaded...")

        self.particles = []

        def counter(first = 1):
            current = [first - 1]
            def next():
                current[0] += 1
                return current[0]
            return next

        id_gen = counter() 

        for n in range(drop_num):
            motion_model = horizontal_split_motion(drop_params)
            p = Particle(self, id_gen, motion_model, 'drop', self.drop_sprites)
            self.particles.append(p)

        for n in range(sand_num):
            motion_model = horizontal_split_motion(sand_params)
            p = Particle(self, id_gen, motion_model, 'sand', self.sand_sprites)
            self.particles.append(p)

        if self.verbose:
            print("particle selection complete...")

    def loadSprites(self, folder):
        sprites = []
        files = os.listdir(folder)

        for sfile in files:            
            sprite = imread(folder + "/" + sfile, as_grey=True)
            sprites.append(sprite)
                
        return sprites
                
    def updateDataBag(self, n):
        for p in self.particles:           
            crop = p.sprite
            d = {'frame': n,
                 'particle': p.id,
                 'x': p.x,
                 'y': p.y,
                 'crop': crop}
            self.bag.batchInsertAssoc(d)
            
            
            d = {'id': self.detection_pid,
                 'area': p.area,
                 'category': p.category}
            self.detection_bag.batchInsertParticle(d)
            
            d = {'frame': n,
                 'particle': self.detection_pid,
                 'x': p.x,
                 'y': p.y,
                 'crop': crop}
            self.detection_bag.batchInsertAssoc(d)

            self.detection_pid += 1
            
    def gkern(self, l=5, sig=1.):
        """
        creates gaussian kernel with side length l and a sigma of sig
        """
    
        ax = np.arange(-l // 2 + 1., l // 2 + 1.)
        xx, yy = np.meshgrid(ax, ax)
    
        kernel = np.exp(-(xx**2 + yy**2) / (2. * sig**2))
    
        return kernel / np.sum(kernel) 
    
    def generate(self, n=10):
        
        # Chart animation
        # vw = cv2.VideoWriter('/local/scratch/mot/data/videos/deepVelocity/gt_tmp5_local.avi', 0 , 24, (101, 101), False)
        
        for n in range(n):
            if self.verbose:
                print("frame ", n, ' ...')

            [p.tick(n) for p in self.particles]            
            # self.particles = [p for p in self.particles if p.alive]

            self.updateDataBag(n)

            d = {'number': n}
            self.bag.batchInsertFrame(d)
            
            
            '''
            For a chart:
            Draw the probability curve to video
            
            '''
            # dy mean + ddy mean * time
            roll = int(-10 + 0.05 * n)
            # vw.write(np.uint8(255*np.roll(self.gkern(101, 2)/np.max(self.gkern(101,2)), roll, axis=0)))
            
        # vw.release()
        self.bag.commit()
        self.detection_bag.commit()