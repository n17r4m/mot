#! /usr/bin/env python
"""
Given a frame, generate crops of interesting particles.

Author: Martin Humphreys
"""



from math import floor, ceil
import os
import uuid

from lib.Database import Database
import numpy as np
import base64

SIZE = 64

class Crop(object):
    
    
    def __init__(self, image):
        
        self.image = image

    def crop(self, x, y, w = SIZE, h = SIZE):
        cx, cy = w // 2, h // 2
        x1, y1 = x - cx, y - cy
        return self._crop(x1, y1, w, h)

    def _crop(self, top_left_x, top_left_y, width, height, mode = "symmetric"):
        """
        Crops a ROI from an image, handling OOB issues correctly.
        https://stackoverflow.com/a/42032814
        """
        bottom_right_x = top_left_x + width;
        bottom_right_y = top_left_y + height;
        
        ch = len(self.image.shape)
        iw = self.image.shape[1]
        ih = self.image.shape[0]
        
        if (top_left_x < 0 or top_left_y < 0 or bottom_right_x > iw or bottom_right_y > ih):
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
            if (bottom_right_x > iw):
                width = width - (bottom_right_x - iw)
                border_right = bottom_right_x - iw
            if (bottom_right_y > ih):
                height = height - (bottom_right_y - ih)
                border_bottom = bottom_right_y - ih
            crop = self.image[top_left_y:top_left_y+height, top_left_x:top_left_x+width]
            
            
            if   ch == 3:
                crop = np.lib.pad(crop, ((border_top, border_bottom), (border_left, border_right), (0, 0)), mode)
            elif ch == 2:
                crop = np.lib.pad(crop, ((border_top, border_bottom), (border_left, border_right)), mode)
                
            
        else:
            # no border padding required
            crop = self.image[top_left_y:top_left_y+height, top_left_x:top_left_x+width]
        return crop;



        