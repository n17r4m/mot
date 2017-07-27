#! /usr/bin/env python
"""
A utility to assign an error rate to a detector, while simultaneously building
a ground truth set.

USING:
    With IPython
        %matplotlib tk
        from DetectorValidator import DetectorValidator

        path = '../raw_data/'
        tmp = 'tmp/'

        video_name = 'T02666'
        video_ext = '.avi'

        val = DetectorValidator(path+video_name+video_ext, 10, 10, 200)
        val.validate()

    The follow controls are available:
        q - View mode: clicking has no action.
        w - True positive mode: clicking a region adds that region to the 'true positive' 
                                ground truth list
        e - False Negative mode: clicking a region adds the position to the 'false negative' 
                                 ground truth list
        r - False Positive mode: clicking a region adds that region to the 'false positive' list
                                 ground truth list
    
        right arrow - go to next crop
        left arrow - fo to previous crop

    Once a region is marked in the ground truth list, it will be drawn white if the 
    crop is revisited.

    Detections smaller than the lowest bracket are shown in red.



Author: Kevin Gordon
"""

import cv2
from argparse import ArgumentParser
import numpy as np
import os, random
import matplotlib.pyplot as plt
from matplotlib.widgets import MultiCursor

from BackgroundExtractor import AverageExtractor
from ForegroundExtractor import ForegroundExtractor, NormalizedForegroundExtractor
from BinaryExtractor import BinaryExtractor
from ComponentExtractor import ComponentExtractor
# from BurstGrabber import BurstGrabber
from FrameGrabber import FrameGrabber

class DetectorValidator(object):

    def __init__(self, filename, no_frames, no_crops, crop_size):
        self.filename = filename

        ### Get background ###
        self.bg_ext = AverageExtractor(filename)

        self.background = cv2.imread('../backgrounds/T02666_background.png', cv2.IMREAD_GRAYSCALE)
        if self.background is None:
            self.background = self.bg_ext.extract()

        self.background = self.background[100:1100,100:1100]

        ### Random Experiment Parameters ###
        self.no_frames = no_frames
        

        self.no_crops = 10
        self.crop_size = 200

        self.x_range = self.background.shape[1] - self.crop_size
        self.y_range = self.background.shape[0] - self.crop_size

        rnd_pos_x = random.sample(range(self.x_range), self.no_crops)
        rnd_pos_y = random.sample(range(self.y_range), self.no_crops)
        self.rnd_pos = zip(rnd_pos_x, rnd_pos_y)

        self.idx = 0

    def get_frames(self):
        self.rnd_frames = random.sample(range(self.bg_ext.frames), self.no_frames)
        frame_grab = FrameGrabber(self.filename)

        self.frames = []    
        for i in range(self.no_frames):
            self.frames.append(frame_grab.frame(self.rnd_frames[i]))
        
        self.frames = [i[100:1100,100:1100] for i in self.frames]

    def get_components(self):        
        ### Enhance foregrounds ###
        fg_ext = NormalizedForegroundExtractor(self.frames, self.background)
        self.fg = fg_ext.extract()

        ### Extract binary foregrounds ###
        bin_ext = BinaryExtractor(self.fg, invert=True, threshold=225)
        fg_bin = bin_ext.extract()

        ### Extract component data ###
        comp_ext = ComponentExtractor(fg_bin)
        self.component_data = comp_ext.extract()

    def get_crops(self):
        idx = self.idx
        i = idx/self.no_frames
        j = idx%self.no_frames

        frame = self.frames[i]
        foreground = self.fg[i]
        label = self.component_data['img'][i]

        pos_x = self.rnd_pos[j][1]
        pos_y = self.rnd_pos[j][0]
        width = self.crop_size
        height = self.crop_size
        
        crop = frame[pos_y:pos_y+height, pos_x:pos_x+width]
        crop = cv2.cvtColor(crop, cv2.COLOR_GRAY2RGB)

        fg_crop = foreground[pos_y:pos_y+height, pos_x:pos_x+width]
        fg_crop = cv2.cvtColor(fg_crop, cv2.COLOR_GRAY2RGB)

        crop_label = label[pos_y:pos_y+height, pos_x:pos_x+width]
        crop_label = np.stack((crop_label, crop_label, crop_label), axis=2)

        bg_crop = self.background[pos_y:pos_y+height, pos_x:pos_x+width]
        bg_crop = cv2.cvtColor(bg_crop, cv2.COLOR_GRAY2RGB)        

        component_ids = np.unique(crop_label)

        self.fg_crop = fg_crop
        self.bg_crop = bg_crop
        self.crop_label = crop_label
        self.crop = crop
        self.x_hair_colour = 'b'
        self.mode = 'view'

    def draw_components(self):
        component_ids = np.unique(self.crop_label)
        idx = self.idx
        i = idx/self.no_frames
        j = idx%self.no_frames

        tmp = self.fg_crop.copy()

        for l in component_ids:
            ### Fill in anything not in range 
            L, T, W, H, A = self.component_data['comp'][i][l]
            if l == 0:
                continue

            if A < 7:
                tmp[:,:,0][self.crop_label[:,:,0] == l] = 127
                tmp[:,:,1][self.crop_label[:,:,1] == l] = 0
                tmp[:,:,2][self.crop_label[:,:,2] == l] = 0

            else:
                tmp[:,:,0][self.crop_label[:,:,0] == l] = 255
                tmp[:,:,1][self.crop_label[:,:,1] == l] = 128
                tmp[:,:,2][self.crop_label[:,:,2] == l] = 0

            for k,v in self.ground_truth.iteritems():
                if l in v:
                    tmp[:,:,0][self.crop_label[:,:,0] == l] = 255
                    tmp[:,:,1][self.crop_label[:,:,1] == l] = 255
                    tmp[:,:,2][self.crop_label[:,:,2] == l] = 0

        self.drawn = tmp

    def validate(self, verbose=False):
        ### for cross hairs
        self.fig = plt.figure()
        self.ax1 = self.fig.add_subplot(131)
        self.ax2 = self.fig.add_subplot(132, sharex=self.ax1, sharey=self.ax1)
        self.ax3 = self.fig.add_subplot(133, sharex=self.ax1, sharey=self.ax1)
        self.plt1 = None
        self.plt2 = None
        self.plt3 = None
        self.fig.canvas.mpl_connect('button_press_event', self.onClick)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_event)        

        self.ground_truth = {'t-pos':[],
                             'f-pos':[],
                             'f-neg':[]}

        self.get_frames()
        self.get_components()
        self.get_crops()
        self.draw_components()

        self.fig.suptitle("View mode")

        self.redraw()
        self.fig.show()

    def redraw(self):

        if self.plt1 is None:
            self.ax1.clear()
            self.ax2.clear()
            self.ax3.clear()
            self.plt1 = self.ax1.imshow(self.crop, vmin=0, vmax=255)
            self.plt2 = self.ax2.imshow(self.drawn, vmin=0, vmax=255)
            self.plt3 = self.ax3.imshow(self.bg_crop, vmin=0, vmax=255)
        else:
            self.plt1.set_data(self.crop)
            self.plt2.set_data(self.drawn)
            self.plt3.set_data(self.bg_crop)

        if self.mode == 'view':
            self.x_hair_colour = 'b'
            self.fig.suptitle("View Mode")
        elif self.mode == 't-pos':
            self.x_hair_colour = 'g'
            self.fig.suptitle("True Positive Mode")
        elif self.mode == 'f-pos':
            self.x_hair_colour = 'r'
            self.fig.suptitle("False Positive Mode")
        elif self.mode == 'f-neg':
            self.x_hair_colour = 'm'
            self.fig.suptitle("False Negative mode")

        self.cursor = MultiCursor(self.fig.canvas,
                                  (self.ax1, self.ax2, self.ax3), 
                                  horizOn=True,
                                  color=self.x_hair_colour, 
                                  alpha=0.25)

    def onClick(self, event):
        x, y = int(event.xdata), int(event.ydata)

        if self.mode != 'view':
            region_id = self.crop_label[y][x][0]
            self.ground_truth[self.mode].append(region_id)

        self.draw_components()
        self.redraw()

        self.fig.show()

    def on_key_event(self, event):
        '''Keyboard interaction'''
        key = event.key

        # In Python 2.x, the key gets indicated as "alt+[key]"
        # Bypass this bug:
        if key.find('alt') == 0:
            key = key.split('+')[1]

        curAxis = plt.gca()
        if key == 'right':
            self.idx += 1
            self.get_crops()
            self.draw_components()
            self.plt1 = None
            self.plt2 = None
            self.plt3 = None

        elif key == 'left':
            self.idx -= 1
            self.get_crops()
            self.draw_components()
            self.plt1 = None
            self.plt2 = None
            self.plt3 = None
        elif key == 'q':
            self.mode = 'view'          

        elif key == 'w':
            self.mode = 't-pos'

        elif key == 'e':
            self.mode = 'f-pos'

        elif key == 'r':
            self.mode = 'f-neg'

        self.redraw()
        self.fig.show()
