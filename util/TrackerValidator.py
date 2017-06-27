#! /usr/bin/env python
"""
A utility to assign an error rate to a detector, while simultaneously building
a ground truth set.

USING:
    With IPython
                %matplotlib tk
                from TrackerValidator import TrackerValidator

                path = '../raw_data/'
                tmp = 'tmp/'

                video_name = 'T02666'
                video_ext = '.avi'

                val = TrackerValidator(path+video_name+video_ext)
                val.validate(100)

    The follow controls are available:
        q - no action
        w - mark track as correct
        e - mark track as incorrect
        right arrow - go to next track
        left arrow - fo to previous track

    Once a region is marked in the ground truth list, it will be drawn white if the 
    crop is revisited.

    Detections smaller than the lowest bracket are shown in red.



Author: Kevin Gordon
"""

# Imports
import cv2
from argparse import ArgumentParser
import numpy as np
import os, random
import matplotlib.pyplot as plt
from matplotlib.widgets import MultiCursor
from time import time
from scipy import stats
from scipy.spatial.distance import cosine

# Our classes
from BackgroundExtractor import AverageExtractor
from ForegroundExtractor import ForegroundExtractor, NormalizedForegroundExtractor
from BinaryExtractor import BinaryExtractor
from ComponentExtractor import ComponentExtractor
from FrameGrabber import FrameGrabber
from BurstGrabber import BurstGrabber
from Tracker import Tracker

# VAEGAN stuff
from fauxtograph import VAE, GAN, VAEGAN, get_paths, image_resize
from chainer import Variable

# Some helper functions
from functions_cv3 import *

class TrackerValidator(object):

    def __init__(self, filename):
        self.filename = filename

        ### Get background ###
        self.bg_ext = AverageExtractor(filename)
        movie_name = filename.split('.')[-2].split('/')[-1]
        self.movie_name = movie_name
        self.background = cv2.imread('../backgrounds/'+movie_name+'_background.png', cv2.IMREAD_GRAYSCALE)
        if self.background is None:
            self.background = self.bg_ext.extract(verbose=True)

        # self.background = self.background[300:800,300:800]

        self.shape = self.background.shape

    def get_burst(self, burst_no):
        burst_grab = BurstGrabber(self.filename)
        self.burst_no = burst_no
        self.frames = burst_grab.burst(burst_no)        
        # self.frames = [i[300:800,300:800] for i in self.frames]

    def get_components(self, 
                       min_area=9, 
                       max_area=20000, 
                       as_indices=False,
                       bin_threshold=223):
        ### Enhance foregrounds ###
        fg_ext = NormalizedForegroundExtractor(self.frames, self.background)
        self.fg = fg_ext.extract()

        ### Extract binary foregrounds ###
        bin_ext = BinaryExtractor(self.fg, invert=True, threshold=bin_threshold)
        self.fg_bin = bin_ext.extract()

        ### Extract component data ###
        comp_ext = ComponentExtractor(self.fg_bin)
        self.component_data = comp_ext.extract()
        self.filter = comp_ext.filter(min_area=min_area, max_area=max_area, as_indices=as_indices)

    def get_tracks_VAEGAN(self):
        # Init the network
        model_name = 'new_arch_test_epoch20'
        loader ={}        
        loader['enc'] = 'VAEGAN/' + model_name + '_enc.h5'
        loader['dec'] = 'VAEGAN/' + model_name + '_dec.h5'
        loader['disc'] = 'VAEGAN/' + model_name + '_disc.h5'
        loader['enc_opt'] = 'VAEGAN/' + model_name + '_enc_opt.h5'
        loader['dec_opt'] = 'VAEGAN/' + model_name + '_dec_opt.h5'
        loader['disc_opt'] = 'VAEGAN/' + model_name + '_disc_opt.h5'
        loader['meta'] = 'VAEGAN/' + model_name + '_meta.json'
        vg = VAEGAN.load(flag_gpu=False, **loader)

        # Get image boundaries
        shape = self.frames[0].shape
        left, right, top, bottom = 0, shape[1]-1, 0, shape[0]-1

        # Get number of frames
        N = len(self.frames)

        ### Build Ground Truth, aka filtered frame 0
        f0_data = {'num': [self.component_data['num'][0]],
                   'img': [self.component_data['img'][0]],
                   'comp': [self.component_data['comp'][0]],
                   'cent': [self.component_data['cent'][0]]}

        out = []
        delta_out = []
        match_errors = []
        ### Compute scores  
        # Number of regions in filtered data
        M = len(self.filter[0])

        # Ground truth labeled image
        img0 = self.component_data['img'][0]
        self.tracks = {}
        self.similarity_scores = {'my_cos':[],'cos':[], 'dot':[], 'abs_diff':[]}
        self.uniques = []
        # For every frame after f0
        for j in range(1,N):
            buf = []
            delta_buf = []
            match_errors_buf = []
            for i in range(M):
                # Skip if didn't pass filter test
                if self.filter[0][i] is False:
                    continue

                # Skip the background for now...
                if i == 0:
                    continue

                l, t, w, h, a = self.component_data['comp'][0][i]

                ### MATCHING SECTION
                search_delta = 1*max(w,h)
                match_threshold = 0.05
                margin = 10

                if t-search_delta < top: t_s = top
                else: t_s = t-search_delta

                if t_s+(h+3*search_delta) > bottom: h_s = bottom-t+1
                else: h_s = h+3*search_delta

                if l-search_delta < left: l_s = left
                else: l_s = l-search_delta

                if l_s+w+3*search_delta > right: w_s = right-l+1
                else: w_s = w+3*search_delta

                # Get unique components in search window
                uniques = np.unique(self.component_data['img'][j][t_s:t_s+h_s, l_s:l_s+w_s])

                # Get the template to compare to, convert it to latent space
                if t-margin < top or t + margin + h > bottom:
                    continue
                if l-margin < left or l + margin + w > right:
                    continue                   
                match_template = self.fg[0][t-margin:t+h+margin, l-margin:l+w+margin]                
                match_template[self.component_data['img'][0][t-margin:t+h+margin, l-margin:l+w+margin] != i] = 255
                match_template = cv2.resize(match_template, (32,32))
                match_template_img = match_template.copy()
                match_template = cv2.cvtColor(match_template, cv2.COLOR_GRAY2RGB)
                match_template = np.array([np.float32(match_template)/255.0])
                match_template = match_template.transpose(0, 3, 1, 2)
                _, match_template = vg.disc(Variable(match_template), test=True)
                # match_template = vg.transform(match_template)
                match_template = match_template.data[0].ravel()
                # print match_template.shape

                best_similarity = None
                id_index = None

                # print "##############"
                count = 0
                for k in uniques:
                    if self.filter[j][k] is False:
                        continue
                    l_k, t_k, w_k, h_k, a_k = self.component_data['comp'][j][k]

                    if t_k-margin < top or t_k + margin + h_k > bottom:
                        continue
                    if l_k-margin < left or l_k + margin + w_k > right:
                        continue    


                    count += 1
                    # Get the proposed region
                    match_src = self.fg[j][t_k-margin:t_k+h_k+margin, l_k-margin:l_k+w_k+margin]                    
                    # Clear the background
                    match_src[self.component_data['img'][j][t_k-margin:t_k+h_k+margin, l_k-margin:l_k+w_k+margin] != k] = 255
                    # Resize
                    match_src = cv2.resize(match_src, (32,32))   
                    # match_src_img = match_src.copy()
                    # convert to 3-channel RGB
                    match_src = cv2.cvtColor(match_src, cv2.COLOR_GRAY2RGB)
                    # Convert to float[0,255]->[0.0,1.0], put it in an array
                    match_src = np.array([np.float32(match_src)/255.0], dtype=np.float32)
                    # Transpose as per fauxtograph img_load function
                    match_src = match_src.transpose(0, 3, 1, 2)

                    # sanity =  vg.inverse_transform(vg.transform(match_src), test=True)
                    # Pass throught network
                    # match_src = vg.transform(match_src)
                    _, match_src = vg.disc(Variable(match_src), test=True)

                    match_src = match_src.data[0].ravel()

                    similarity = cosine(match_template, match_src)
                    self.similarity_scores['cos'].append(similarity)
                    # print 'cos: ', similarity

                    similarity = np.dot(match_template, match_src.T) / (np.linalg.norm(match_template,2) * np.linalg.norm(match_src,2))
                    self.similarity_scores['my_cos'].append(similarity)
                    # print 'my_cos: ', similarity

                    similarity = np.dot(match_src, match_template.T)
                    self.similarity_scores['dot'].append(similarity)
                    # print 'dot: ', similarity

                    similarity = np.sum(np.abs(match_template - match_src))
                    self.similarity_scores['abs_diff'].append(similarity)
                    # print 'abs_diff: ', similarity, '\n'

                    # disp_seq_compare([match_template_img], [sanity], hz=0)

                    similarity = self.similarity_scores['my_cos'][-1]

                    if best_similarity is None:
                        best_similarity = similarity
                        id_index = k
                    elif similarity > best_similarity:
                        best_similarity = similarity
                        id_index = k

                if id_index is None:
                    id_index = 0

                ### END TEMPLATE MATCHING
                if i not in self.tracks and j==1:
                    self.tracks[i] = []

                # if min_val > match_threshold or id_index == 0:
                if id_index == 0:
                    self.filter[0][i] = False
                    self.tracks.pop(i)
                    continue

                self.tracks[i].append(id_index)
                self.uniques.append(len(uniques))

        self.rnd_indexes = self.tracks.keys()
        random.shuffle(self.rnd_indexes)

    def get_tracks_optFlow(self):
        print 'entering optFlow'
        # Get image boundaries
        shape = self.frames[0].shape
        left, right, top, bottom = 0, shape[1]-1, 0, shape[0]-1

        # Get number of frames
        N = len(self.frames)

        ### Build Ground Truth, aka filtered frame 0
        f0_data = {'num': [self.component_data['num'][0]],
                   'img': [self.component_data['img'][0]],
                   'comp': [self.component_data['comp'][0]],
                   'cent': [self.component_data['cent'][0]]}

        out = []
        delta_out = []
        match_errors = []
        ### Compute scores  
        # Number of regions in filtered data
        M = len(self.filter[0])

        # Ground truth labeled image
        img0 = self.component_data['img'][0]
        self.tracks = {}

        # For every frame after f0
        for j in range(1,N):
            imgj = self.component_data['img'][j]
            buf = []
            delta_buf = []
            match_errors_buf = []
            grads = img_gradients(self.frames[j])
            diffs = img_diff(self.frames[0], self.frames[j], absolute=True, boost=True, threshold=0)
            for i in range(M):
                # Skip if didn't pass filter test
                if self.filter[0][i] is False:
                    continue

                # Skip the background for now...
                if i == 0:
                    continue

                l, t, w, h, a = self.component_data['comp'][0][i]


                ### TEMPLATE MATCHING SECTION
                search_delta = 1*max(w,h)
                match_threshold = 0.05

                if t-search_delta < top: t_s = top
                else: t_s = t-search_delta

                if t_s+(h+3*search_delta) > bottom: h_s = bottom-t+1
                else: h_s = h+3*search_delta

                if l-search_delta < left: l_s = left
                else: l_s = l-search_delta

                if l_s+w+3*search_delta > right: w_s = right-l+1
                else: w_s = w+3*search_delta

                match_src = self.frames[j][t_s:t_s+h_s, l_s:l_s+w_s]
                match_template = self.frames[0][t:t+h, l:l+w]

                ########## OPTIC FLOW SECTION ##########


                t_opt = t
                l_opt = l

                threshold = 2.0
                opt_proposal = self.frames[j][t_opt:t_opt+h, l_opt:l_opt+w]

                error = np.sqrt(np.sum((opt_proposal - match_template)**2)) / np.float(a)

                itr = 0
                poor_cond = False

                while error > threshold and itr < 50:
                    # print "error: " + str(error)
                    itr += 1

                    Ix = grads[0][t_s:t_s+h_s, l_s:l_s+w_s].ravel()
                    Iy = grads[1][t_s:t_s+h_s, l_s:l_s+w_s].ravel()                    

                    if match_template.shape != opt_proposal.shape:
                        print "mismatch: ", match_template.shape, opt_proposal.shape
                        print "pos: ", t, l, t_opt, l_opt

                    b = diffs[t_s:t_s+h_s, l_s:l_s+w_s]
                    b = b.ravel()
                    Ix = Ix[np.where(b>0)]
                    Iy = Iy[np.where(b>0)]
                    b = b[np.where(b>0)]

                    if b.shape[0] == 0:
                        print "no diff ..."
                        break

                    A = np.column_stack((Ix, Iy))

                    cond_A = np.linalg.cond(A)

                    if cond_A > 100 or cond_A < 0.01:
                        poor_cond = True
                        break

                    s = -np.linalg.lstsq(A, b)[0]

                    t_opt += int(s[0])
                    l_opt += int(s[1])

                    ### ensure limits ok
                    if t_opt < top: t_opt = top
                    if l_opt < left: l_opt = left
                    if t_opt+h > bottom: t_opt = bottom-h
                    if l_opt+w > bottom: l_opt = right-w                    

                    error = np.sqrt(np.sum((opt_proposal - match_template)**2)) / np.float(a)
                    opt_proposal = self.frames[j][t_opt:t_opt+h, l_opt:l_opt+w]

                ########## END OPTIC FLOW SECTION ##########

                ### END TEMPLATE MATCHING
                if i not in self.tracks and j==1:
                    self.tracks[i] = []

                id_index = imgj[t_opt+h/2, l_opt+w/2]

                # if min_val > match_threshold or id_index == 0:
                if id_index == 0 or poor_cond:
                    self.filter[0][i] = False
                    self.tracks.pop(i)
                    continue

                self.tracks[i].append(id_index)
        print 'tracks: ', self.tracks
        self.rnd_indexes = self.tracks.keys()
        random.shuffle(self.rnd_indexes)

    def get_tracks_flowGraph(self, no_tracks=600):

        self.tracker = Tracker(self.component_data, self.filter, self.frames, self.fg, verbose=True)
        self.tracker.build()
        self.tracker.solve(no_tracks)
        self.tracker.reconstruct_paths()
        self.tracks = {}

        N = len(self.frames)

        for i in self.tracker.paths:
            if len(i) != len(self.frames):
                continue
            
            for j in range(N):
                component_id = int(i[j].split('_')[2])
                if j==0:
                    self.tracks[component_id] = []
                else:
                    self.tracks[int(i[0].split('_')[2])].append(component_id)        

        self.rnd_indexes = self.tracks.keys()
        random.shuffle(self.rnd_indexes)

    def get_tracks(self):
        # Get image boundaries
        shape = self.frames[0].shape
        left, right, top, bottom = 0, shape[1]-1, 0, shape[0]-1

        # Get number of frames
        N = len(self.frames)

        ### Build Ground Truth, aka filtered frame 0
        f0_data = {'num': [self.component_data['num'][0]],
                   'img': [self.component_data['img'][0]],
                   'comp': [self.component_data['comp'][0]],
                   'cent': [self.component_data['cent'][0]]}

        out = []
        delta_out = []
        match_errors = []
        ### Compute scores  
        # Number of regions in filtered data
        M = len(self.filter[0])

        # Ground truth labeled image
        img0 = self.component_data['img'][0]
        self.tracks = {}

        # For every frame after f0
        for j in range(1,N):
            imgj = self.component_data['img'][j]
            buf = []
            delta_buf = []
            match_errors_buf = []
            for i in range(M):
                # Skip if didn't pass filter test
                if self.filter[0][i] is False:
                    continue

                # Skip the background for now...
                if i == 0:
                    continue

                l, t, w, h, a = self.component_data['comp'][0][i]


                ### TEMPLATE MATCHING SECTION
                search_delta = 1*max(w,h)
                match_threshold = 0.05

                if t-search_delta < top: t_s = top
                else: t_s = t-search_delta

                if t_s+(h+3*search_delta) > bottom: h_s = bottom-t+1
                else: h_s = h+3*search_delta

                if l-search_delta < left: l_s = left
                else: l_s = l-search_delta

                if l_s+w+3*search_delta > right: w_s = right-l+1
                else: w_s = w+3*search_delta

                match_src = self.frames[j][t_s:t_s+h_s, l_s:l_s+w_s]
                match_template = self.frames[0][t:t+h, l:l+w]

                match_result = cv2.matchTemplate(match_src, match_template, cv2.TM_SQDIFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match_result)

                dx, dy = l_s-l+min_loc[0], t_s-t+min_loc[1]
                ### END TEMPLATE MATCHING
                if i not in self.tracks and j==1:
                    self.tracks[i] = []

                slice0 = img0[t:t+h, l:l+w]
                sliceN = imgj[t+dy:t+h+dy, l+dx:l+w+dx]

                id_index = imgj[t+dy+h/2, l+dx+w/2]

                # if min_val > match_threshold or id_index == 0:
                if id_index == 0:
                    self.filter[0][i] = False
                    self.tracks.pop(i)
                    continue

                self.tracks[i].append(id_index)

        self.rnd_indexes = self.tracks.keys()
        random.shuffle(self.rnd_indexes)

    def get_crops(self, full_image=False):
        if full_image:
            self.crops = [cv2.cvtColor(i, cv2.COLOR_GRAY2RGB) for i in self.frames]
            return 

        i = self.rnd_indexes[self.idx]

        track = [i]
        for j in self.tracks[i]:
            track.append(j)

        # Get the bounding box around the whole track
        L = self.shape[1]
        T = self.shape[0]
        R = 0
        B = 0
        margin = 30

        for j in range(len(self.frames)):
            l, t, w, h, a = self.component_data['comp'][j][track[j]]

            if l < L:
                L = l

            if t < T:
                T = t

            if l+w > R: 
                R = l + w

            if t+h > B:
                B = t + h

        R += margin
        B += margin
        L -= margin
        T -= margin

        if R > self.shape[1]:
            R = self.shape[1]

        if B > self.shape[0]:
            B = self.shape[0]

        if L < 0:
            L = 0

        if T < 0:
            T = 0

        self.crops = []
        self.crop_pos = (L,T)
        
        for j in range(len(self.frames)):
            crop = self.frames[j][T:B, L:R]
            crop = cv2.cvtColor(crop, cv2.COLOR_GRAY2RGB)
            self.crops.append(crop)

    def draw_components(self):
        i = self.rnd_indexes[self.idx]

        track = [i]
        for j in self.tracks[i]:
            track.append(j)

        for j in range(len(self.frames)):
            centre = self.component_data['cent'][j][track[j]]
            centre = (int(centre[0])-self.crop_pos[0], 
                      int(centre[1])-self.crop_pos[1])

            cv2.circle(self.crops[j], centre, 3, (0,255,0), 1)

    def validate(self, burst_no, verbose=False):
        ### for cross hairs
        self.fig = plt.figure()
        self.ax1 = self.fig.add_subplot(111)
        # self.ax2 = self.fig.add_subplot(132, sharex=self.ax1, sharey=self.ax1)
        # self.ax3 = self.fig.add_subplot(133, sharex=self.ax1, sharey=self.ax1)
        self.plt1 = None
        # self.plt2 = None
        # self.plt3 = None

        self.ground_truth = {'correct':[],
                             'incorrect':[]}

        # which track are we looking at?
        self.idx = 0
        self.crop_idx = 0

        self.get_burst(burst_no)
        self.get_components(as_indices=True)

        start = time()
        # self.get_tracks()

        self.get_tracks_flowGraph()

        elapsed = time()-start
        print "Getting tracks took ", "%.2f" % elapsed, " seconds"
        # self.get_tracks_VAEGAN()
        # self.get_tracks_optFlow()

        self.get_crops()
        self.draw_components()

        self.mode = 'view'
        self.fig.suptitle("View mode")

        self.redraw()
        self.fig.canvas.mpl_connect('button_press_event', self.onClick)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_event)        

        self.fig.show()

    def confidence_interval(self, correct, incorrect, alpha):
        correct = [1]*correct
        incorrect = [0]*incorrect
        total = np.array(correct+incorrect)
        n = len(total)
        c = stats.t.ppf(1-alpha/2.0, n-1)
        mean = total.mean()
        var = total.var()
        return (mean-c*var/np.sqrt(n), mean+c*var/np.sqrt(n))

    def redraw(self):

        if self.plt1 is None:
            self.ax1.clear()
            # self.ax2.clear()
            # self.ax3.clear()
            # print self.crops[self.crop_idx]
            self.plt1 = self.ax1.imshow(self.crops[self.crop_idx], vmin=0, vmax=255)
            # self.plt2 = self.ax2.imshow(self.drawn, vmin=0, vmax=255)
            # self.plt3 = self.ax3.imshow(self.bg_crop, vmin=0, vmax=255)
        else:
            self.plt1.set_data(self.crops[self.crop_idx])
            # self.plt2.set_data(self.drawn)
            # self.plt3.set_data(self.bg_crop)

        if self.mode == 'view':
            self.x_hair_colour = 'b'
            self.fig.suptitle("View Mode")
        elif self.mode == 'correct':
            self.x_hair_colour = 'g'
            self.fig.suptitle("Track labelled correct")
        elif self.mode == 'incorrect':
            self.x_hair_colour = 'r'
            self.fig.suptitle("Track labelled incorrect")

        # (self.ax1, self.ax2, self.ax3), 
        # self.cursor = MultiCursor(self.fig.canvas,
        #                           (self.ax1),
        #                           horizOn=True,
        #                           color=self.x_hair_colour, 
        #                           alpha=0.25)

    def onClick(self, event):
        x, y = event.xdata, event.ydata

        if x is None and y is None:
            return

        x, y = int(x), int(y)

        if self.mode != 'view':
            region_id = self.crop_label[y][x][0]

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
            self.idx = min(len(self.rnd_indexes)-1, self.idx)
            self.crop_idx = 0            
            self.get_crops()
            self.draw_components()
            self.mode = 'view'
            self.plt1 = None
            # self.plt2 = None
            # self.plt3 = None

        elif key == 'left':
            self.idx -= 1
            self.idx = max(0, self.idx)
            self.crop_idx = 0
            self.get_crops()
            self.mode = 'view'
            self.draw_components()
            self.plt1 = None
            # self.plt2 = None
            # self.plt3 = None

        elif key == 'up':
            self.crop_idx += 1
            self.crop_idx = min(len(self.frames)-1, self.crop_idx)

        elif key == 'down':
            self.crop_idx -= 1
            self.crop_idx = max(0, self.crop_idx)

        elif key == 'q':
            self.mode = 'view'

        elif key == 'w':
            self.mode = 'correct'
            current_id = self.rnd_indexes[self.idx]

            # Ensure a track is correct or incorrect not both. 
            # Ensure no duplicates.
            if current_id in self.ground_truth['incorrect']:
                _ = self.ground_truth['incorrect'].remove(current_id)
            if current_id not in self.ground_truth['correct']:
                self.ground_truth[self.mode].append(current_id)


        elif key == 'e':
            self.mode = 'incorrect'
            current_id = self.rnd_indexes[self.idx]

            # Ensure a track is correct or incorrect not both. 
            # Ensure no duplicates.
            if current_id in self.ground_truth['correct']:
                _ = self.ground_truth['correct'].remove(current_id)
            if current_id not in self.ground_truth['incorrect']:
                self.ground_truth[self.mode].append(current_id)

        self.redraw()
        self.fig.show()

    def save_ground_truth(self):
        tracks = []
        
        for i in self.ground_truth['correct']: 
            cnt = 0           
            track = [self.component_data['cent'][cnt][i]]

            for j in self.tracks[i]:
                cnt += 1
                track.append(self.component_data['cent'][cnt][j])

            tracks.append(track)

        np.save(self.movie_name+'_'+str(self.burst_no), tracks)

    def load_ground_truth(self, burst_no, filename=None):
        if filename:
            tmp = np.load(filename)
        else:
            tmp = np.load(self.movie_name+'_'+str(self.burst_no)+'.npy')

        print "loaded ", len(tmp), " tracks ..."
        self.ground_truth_tracks = {}
        missing = 0
        doesnt_span = 0
        for track in tmp:
            cnt = 0
            pos = track[cnt]

            margin = 1
            x,y = int(round(pos[0])), int(round(pos[1]))

            start_id = self.component_data['img'][cnt][y][x]

            if start_id == 0:
                # Search 8 connected neighbours
                for i in [0,1,0,-1,0]:                    
                    if start_id:
                        break
                    for j in [0,1,0,-1,0]:
                        try:
                            start_id = self.component_data['img'][cnt][y+i][x+j]
                        except IndexError:
                            pass

                        if start_id:
                            break

            if start_id == 0:
                # centre = (x,y)
                # cv2.circle(self.frames[0], centre, 3, (255,255,255), 1)                
                missing += 1
                continue

            self.ground_truth_tracks[start_id] = []

            for pos in track[1:]:
                cnt += 1
                pos = track[cnt]
                x = int(round(pos[0]))
                y = int(round(pos[1]))
                try:
                    drop_id = self.component_data['img'][cnt][y][x]
                except IndexError:
                    print "edge case problem in simulator..."
                    continue

                if drop_id == 0:
                    # Search 8 connected neighbours
                    for i in [0,1,0,-1,0]:                    
                        if drop_id:
                            break
                        for j in [0,1,0,-1,0]:
                            try:
                                drop_id = self.component_data['img'][cnt][y+i][x+j]
                            except IndexError:
                                pass
                            if drop_id:
                                break

                self.ground_truth_tracks[start_id].append(drop_id)

            if 0 in self.ground_truth_tracks[start_id]:
                _ = self.ground_truth_tracks.pop(start_id)
                missing += 1    

            elif len(self.ground_truth_tracks[start_id]) != len(self.frames)-1:
                _ = self.ground_truth_tracks.pop(start_id)
                doesnt_span += 1

        if doesnt_span:
            print doesnt_span, " ground truth tracks do not span burst"

        if missing:
            print missing, " detections missing in labelled image ..."

    def draw_ground_truth(self):
        self.get_crops(full_image=True)

        for i in self.ground_truth_tracks.keys():
            track = [i]
            for j in self.ground_truth_tracks[i]:
                track.append(j)

            for j in range(len(self.frames)-1):
                centre1 = self.component_data['cent'][j][track[j]]
                centre2 = self.component_data['cent'][j+1][track[j+1]]

                centre1 = (int(round(centre1[0])), 
                          int(round(centre1[1])))
                centre2 = (int(round(centre2[0])), 
                          int(round(centre2[1])))                 

                for k in range(len(self.frames)):
                    if j == len(self.frames)-2:
                        cv2.arrowedLine(self.crops[k], centre1, centre2, (0,255,0), 2)
                    else:
                        cv2.line(self.crops[k], centre1, centre2, (0,255,0), 2)
                        

        self.crop_idx = 0
        self.plt1 = None
        self.redraw()

    def auto_validate(self, burst_no, min_size=20):
        self.burst_no = burst_no        

        self.ground_truth = {'correct':[],
                             'incorrect':[]}

        # which track are we looking at?
        self.idx = 0
        self.crop_idx = 0

        self.get_burst(self.burst_no)
        self.get_components(as_indices=True)
        self.load_ground_truth(self.burst_no)

        start = time()
        self.get_tracks_flowGraph()
        elapsed = time()-start
        print "Getting tracks took ", "%.2f" % elapsed, " seconds"

        missing = 0
        not_long = 0

        missing_Areas = []
        missing_IDs = []
        
        for i in self.ground_truth_tracks:
            flag = False
            l, t, w, h, a = self.component_data['comp'][0][i]

            # Check to see if we are missing a track starting at ID i
            if not i in self.tracks:
                missing += 1
                missing_IDs.append(i)            
                missing_Areas.append(a)
                flag = True
                # centre = self.component_data['cent'][0][i]
                # centre = (int(centre[0]), 
                #           int(centre[1]))

                # cv2.circle(self.frames[0], centre, 3, (255,255,255), 1)

            # For now, we test "Complete" tracks only
            elif len(self.tracks[i]) != 9:
                not_long += 1
                continue

            # We have a track to check
            else:
                for j in range(len(self.ground_truth_tracks[i])):
                    gt = self.ground_truth_tracks[i][j]
                    tmp = self.tracks[i][j]
                    if tmp != gt:                    
                        flag = True

            if a > min_size:
                if flag:
                    self.ground_truth['incorrect'].append(i)
                else:
                    self.ground_truth['correct'].append(i)

        if missing:
            print missing, " tracks missing with mean area ", np.mean(missing_Areas)
        if not_long:
            print not_long, ' tracks not long enough ...'
        print self.confidence_interval(len(self.ground_truth['correct']), len(self.ground_truth['incorrect']), 0.05)










