#! /usr/bin/env python
"""
Given a databag and a video, generate crops of interesting particles.


CHANGELOG:
    
    

USING:

    As a command line utility:
    
        $ Cropper.py input_video input_bag output_dir [-p particle_id -pad padding]
        
        
    
    As a module:
    
        import Cropper from Cropper
        cropper = Cropper(aDataBagObjectOrFilename, input_video)
        crop = cropper.isolate(particle_id, frame_id)
        

Author: Martin Humphreys
"""



import cv2

from argparse import ArgumentParser
from math import floor, ceil
import os
from DataBag import DataBag
from Query import Query
import numpy as np
from functions.to_precision import to_precision

class Cropper(object):
    
    
    def __init__(self, video, bag, opts):
        
        self.bag = DataBag.fromArg(bag)
        self.q = Query(self.bag)
        
        
        if isinstance(video, (str, unicode)):
            self.vc = cv2.VideoCapture(video)
        else:
            self.vc = video
            
            
        self.frames = int(self.vc.get(cv2.CAP_PROP_FRAME_COUNT))
        
        
        if isinstance(opts, dict):
            self.opts = dotdict(opts)
        else:
            self.opts = opts
            
        self.output_dir = self.opts.output_dir or "crops"
        self.size = self.opts.size or 64
        self.pad = self.opts.pad or 5
        
        self.isolate_last_frame = None
        self.isolate_last_frame_id = -1
    
    def crop(self, img, top_left_x, top_left_y, width, height):
        """
        Crops a ROI from an image, handling OOB issues correctly.
        https://stackoverflow.com/a/42032814
        """
        bottom_right_x = top_left_x + width;
        bottom_right_y = top_left_y + height;
        
        if (top_left_x < 0 or top_left_y < 0 or bottom_right_x > img.shape[1] or bottom_right_y > img.shape[0]):
            # border padding will be required
            border_left, border_right, border_top, border_bottom = 0, 0, 0, 0
            if (top_left_x < 0):
                width = width + top_left_x
                border_left = -1 * top_left_x
                top_left_x = 0
            if (top_left_y < 0):
                height = height + top_left_y
                border_top = -1 * top_left_y
                top_left_y = 0
            if (bottom_right_x > img.shape[1]):
                width = width - (bottom_right_x - img.shape[1])
                border_right = bottom_right_x - img.shape[1]
            if (bottom_right_y > img.shape[0]):
                height = height - (bottom_right_y - img.shape[0])
                border_bottom = bottom_right_y - img.shape[0]
            crop = img[top_left_y:top_left_y+height, top_left_x:top_left_x+width]
            crop = cv2.copyMakeBorder(crop, border_top, border_bottom, border_left, border_right, cv2.BORDER_REPLICATE)
        else:
            # no border padding required
            crop = img[top_left_y:top_left_y+height, top_left_x:top_left_x+width]
        return crop;


    def isolate(self, frame_no, particle_id):
        props = self.q.particle_properties(frame_no, particle_id)
        
        if props != None:
            
            x, y, a, r = int(round(props.x)), int(round(props.y)), float(props.area), float(props.radius)
            
            r = int(max(r, np.sqrt(a/np.pi)))
            x1, y1, d = x - r - self.pad, y - r - self.pad, (r*2)+(self.pad*2)
            
            if frame_no == self.isolate_last_frame_id:
                ret, frame = True, self.isolate_last_frame
            else:
                self.vc.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
                ret, frame = self.vc.read()
                self.isolate_last_frame = frame
                self.isolate_last_frame_id = frame_no

            if ret:
                return self.crop(frame, x1, y1, d, d)
            else:
                return None
                
        return None   
    
    def save(self, img, frame_no, particle_id, category=0):
        c = "u"
        if category == "bitumen" or category == 2:
            c = 'd'
        if category == "sand" or category == 3:
            c = 's'
        if category == "bubble" or category == 4:
            c = 'b'
        
        s = to_precision(float(self.size) / float(img.shape[0]), 3)
        
        resized_image = cv2.resize(img, (self.size, self.size), interpolation = cv2.INTER_CUBIC) 
        
        fname = "{}_{}_{}_{}.png".format(c, frame_no, particle_id, s)
        
        cv2.imwrite(os.path.join(self.output_dir, fname), resized_image)
        

class dotdict(dict):
  """dot.notation access to dictionary attributes"""
  # https://stackoverflow.com/a/23689767
  __getattr__ = dict.get
  __setattr__ = dict.__setitem__
  __delattr__ = dict.__delitem__
  
  

def build_parser():
    parser = ArgumentParser()
    
    parser.add_argument('input_video', help='The video file to use')
    parser.add_argument('bag', help='The databag file with stored detection or tracking results')
    parser.add_argument('output_dir', help='location to save the crops of the particles')
    
    
    parser.add_argument("-p", "--particle", help="particle_id to crop", type=int, nargs="?")
    parser.add_argument("-f", "--frame", help="frame to crop from", type=int, nargs="?")
    parser.add_argument("-s", "--size", help="Size of crop to generate", type=int, default=64)
    parser.add_argument("-pad", "--pad", help="amount of padding to use", type=int, default=10)
    parser.add_argument("-l", "--limit", help="Maximum number of particles to crop", type=int, default=2**32)
    
    
    parser.add_argument('-v', help='print verbose statements while executing', 
                              action = 'store_true')    

    return parser


def main(opts):
    if not os.path.isfile(opts.input_video):
        parser.error("Input video file %s does not exist." % opts.bg)
    if not os.path.isfile(opts.bag):
        parser.error("DataBag file %s does not exist." % opts.bag)
    
    if not os.path.exists(opts.output_dir):
        os.makedirs(opts.output_dir)
        
        
    cropper = Cropper(opts.input_video, opts.bag, opts)
    
    
    if opts.frame != None and opts.particle != None: 
        
        crop = cropper.isolate(opts.frame, opts.particle)
        cropper.save(crop, opts.frame, opts.particle)
    
    elif opts.frame != None:
        
        particles = cropper.q.particles_in_frame(opts.frame)
        for p in particles[:opts.limit]:
            crop = cropper.isolate(p.frame, p.id)
            cropper.save(crop, p.frame, p.id)
        
    elif opts.particle != None:
        
        particles = cropper.q.particle_instances(opts.particle)
        for p in particles[:opts.limit]:
            
            crop = cropper.isolate(p.frame, p.id)
            cropper.save(crop, p.frame, p.id)
    
    else:
        frames = cropper.q.frame_list()
        c = 0
        try: 
            for f in frames:
                particles = cropper.q.particles_in_frame(f.frame)
                for p in particles:
                    crop = cropper.isolate(p.frame, p.id)
                    cropper.save(crop, p.frame, p.id)
                    c += 1
                    if c > opts.limit: 
                        raise StopIteration("Limit reached")
        except StopIteration as e:
            pass
        
if __name__ == '__main__':
    main(build_parser().parse_args())
 









