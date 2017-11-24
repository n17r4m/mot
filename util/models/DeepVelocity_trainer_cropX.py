

# %load_ext autoreload

import time

import matplotlib.pyplot as plt
import numpy as np
from keras import models

from .DeepVelocity import DeepVelocityV2
# from ClassyVCoder_1 import ClassyVCoder
from util.DataBag import DataBag
# from keras.utils.np_utils import to_categorical

from util.FrameGrabber import FrameGrabber


from scipy.stats import norm

MOTION_SCALE = 1.0 # watch out for fetch data using this and augment not!!!
MAX_DELTA = 25.0
FRAME_WIDTH = 2336.0
FRAME_HEIGHT = 1729.0

import cv2

class DV_trainer(object): 

    def __init__(self, bag, CC, std_dev=3.0, verbose=True):
        self.bag = bag
        self.CC = CC
        self.verbose = verbose
        self.std_dev = std_dev
        self.create_DV()
        self.ratio = 0.0

    def create_DV(self, lr=0.001):
        self.curr_epoch = 0
        self.DV = DeepVelocityV2(lr=lr, verbose=self.verbose)
        
    # https://stackoverflow.com/questions/4601373/better-way-to-shuffle-two-numpy-arrays-in-unison
    def shuffle_in_unison(self, l):
        rng_state = np.random.get_state()
        for i in l:
            np.random.shuffle(i)
            np.random.set_state(rng_state)
        

    def shuffle(self, l):
        for i in l:
            np.random.shuffle(i)

    def augment_data3(self):
        # Idea: Generate new random samples, accepting each with a probability
        #       as determined by the trained network (or equal prob at init)

        feature_select = {'dxdy': True,
                          'lat': True, 
                          'f1f2': True,
                          'xy': True}

        structured_data = []
        screen_data = []
        y_data = []
        crop_data = []

        ###   --- Training Data ---   ###
        for i in range(len(self.dxs_training)):
            dx = self.dxs_training[i]
            dy = self.dys_training[i]
            lat = self.lats_training[i]
            f1 = self.f1s_training[i]
            f2 = self.f2s_training[i]
            x = self.xs_training[i]
            y = self.ys_training[i]
            crop = self.crops_training[i]

            # BEGIN Turn off select features
            if not feature_select['dxdy']:
                dx = np.random.uniform(low = -MAX_DELTA, high = MAX_DELTA, size = dx.shape)
                dy = np.random.uniform(low = -MAX_DELTA, high = MAX_DELTA, size = dy.shape)
            if not feature_select['lat']:
                lat = np.random.normal(0, 1, lat.shape)
            if not feature_select['f1f2']:
                f1 = np.random.normal(0, 1, f1.shape)
                f2 = np.random.normal(0, 1, f2.shape)
            if not feature_select['xy']:
                x = np.random.normal(0, 1, x.shape)
                y = np.random.normal(0, 1, y.shape)
            # END

            # BEGIN Add the gt data to set
            prob = 1.0
            y_data.append([prob, 1.0 - prob])

            structured_data.append(np.concatenate([lat, np.array([dx]), np.array([dy]), np.array([x]), np.array([y])]))
            screen_data.append(np.array([f1,f2]).T)
            crop_data.append(crop)
            # END
        
        target = 2 * len(structured_data)

        while len(structured_data) < target:
            structured_data_buf = []
            screen_data_buf = []
            y_data_buf = []
            crop_data_buf = []
            for i in range(80000):
                idx = np.random.randint(0, len(self.dxs_training))
    
                lat = self.lats_training[idx]
                f1 = self.f1s_training[idx]
                f2 = self.f2s_training[idx]
                x = self.xs_training[idx]
                y = self.ys_training[idx]
                crop = self.crops_training[idx]
                
                # BEGIN Turn off select features
                if not feature_select['dxdy']:
                    dx = np.random.uniform(low = -MAX_DELTA, high = MAX_DELTA, size = dx.shape)
                    dy = np.random.uniform(low = -MAX_DELTA, high = MAX_DELTA, size = dy.shape)
                if not feature_select['lat']:
                    lat = np.random.normal(0, 1, lat.shape)
                if not feature_select['f1f2']:
                    f1 = np.random.normal(0, 1, f1.shape)
                    f2 = np.random.normal(0, 1, f2.shape)
                if not feature_select['xy']:
                    x = np.random.normal(0, 1, x.shape)
                    y = np.random.normal(0, 1, y.shape)
                # END            
                
                dx = np.random.uniform(low = -MAX_DELTA, high = MAX_DELTA, size = dx.shape)
                dy = np.random.uniform(low = -MAX_DELTA, high = MAX_DELTA, size = dy.shape)
                
                prob = 0.0
                
                y_data_buf.append([prob, 1.0 - prob])
                structured_data_buf.append(np.concatenate([lat, np.array([dx]), np.array([dy]), np.array([x]), np.array([y])]))
                screen_data_buf.append(np.array([f1,f2]).T)
                crop_data_buf.append(crop)
     
            self.probs = self.DV.deep_velocity.predict([np.array(structured_data_buf), np.array(screen_data_buf)])[:,0]
            
            keepers  = []
            for prob in self.probs:
                keepers.append(int(np.random.random() + prob))
                
            _ = [structured_data.append(structured_data_buf[i]) for i in range(len(keepers)) if keepers[i]]
            _ = [screen_data.append(screen_data_buf[i]) for i in range(len(keepers)) if keepers[i]]
            _ = [crop_data.append(crop_data_buf[i]) for i in range(len(keepers)) if keepers[i]]
            _ = [y_data.append(y_data_buf[i]) for i in range(len(keepers)) if keepers[i]]

        self.screen_data_training = screen_data
        self.structured_data_training = structured_data
        self.y_data_training = y_data
        self.crop_data_training = crop_data
        
        self.shuffle_in_unison([self.screen_data_training, 
                               self.structured_data_training, 
                               self.y_data_training, 
                               self.crop_data_training])
        
        ###   --- Test Data ---    ###
        structured_data = []
        screen_data = []
        y_data = []
        crop_data = []

        for i in range(len(self.dxs_test)):
            dx = self.dxs_test[i]
            dy = self.dys_test[i]
            lat = self.lats_test[i]
            f1 = self.f1s_test[i]
            f2 = self.f2s_test[i]
            crop = self.crops_test[i]
            x = self.xs_test[i]
            y = self.ys_test[i]

            structured_data.append(np.concatenate([lat, np.array([dx]), np.array([dy]), np.array([x]), np.array([y])]))
            screen_data.append(np.array([f1,f2]).T)
            prob = 1.0
            y_data.append([prob, 1.0 - prob])

            crop_data.append(crop)
        
                     
        self.screen_data_test = screen_data
        self.structured_data_test = structured_data
        self.y_data_test = y_data
        self.crop_data_test = crop_data

        self.shuffle_in_unison([self.screen_data_test, 
                               self.structured_data_test, 
                               self.y_data_test, 
                               self.crop_data_test])

    def augment_data2(self):
        # Idea: have confidence 1 for actual observations
        #       confidence 0 for randomize tupling
        # For every positive example
        # choose which input feature to randomize
        # choose a random sample for the chosen feature
        # assign output confidence 0 and create the training/test sample

        structured_data = []
        screen_data = []
        y_data = []
        crop_data = []

        for i in range(len(self.dxs_training)):
            dx = self.dxs_training[i]
            dy = self.dys_training[i]
            lat = self.lats_training[i]
            f1 = self.f1s_training[i]
            f2 = self.f2s_training[i]
            x = self.xs_training[i]
            y = self.ys_training[i]
            crop = self.crops_training[i]

            # Turn off select features
            # dx = dx
            # dy = dy
            # lat = lat
            # f1 = np.random.normal(0, 1, f1.shape)
            # f2 = np.random.normal(0, 1, f2.shape)
            x = np.random.normal(0, 1, x.shape)
            y = np.random.normal(0, 1, y.shape)
            crop = crop

            prob = 1.0
            y_data.append([prob, 1.0 - prob])

            structured_data.append(np.concatenate([lat, np.array([dx]), np.array([dy]), np.array([x]), np.array([y])]))
            screen_data.append(np.array([f1,f2]).T)
            crop_data.append(crop)

            selector = int(np.random.random() + self.ratio)
            # selector = True
            input_features = 'dxdy,lat,f1f2,xy'
            input_features = input_features.split(',')
            random_feature = np.random.choice(input_features)
            random_feature = 'dxdy'

            if selector:
                # Add random negative observation
                idx = np.random.randint(0, len(self.dxs_training))

                if random_feature == 'dxdy':
                    dx = self.dxs_training[idx]
                    dy = self.dys_training[idx]
                elif random_feature == 'lat':
                    lat = self.lats_training[idx]
                elif random_feature == 'f1f2':
                    f1 = self.f1s_training[idx]
                    f2 = self.f2s_training[idx]
                elif random_feature == 'xy':
                    x = self.xs_training[idx]
                    y = self.ys_training[idx]
                else:
                    print("something wrong in feature selection")

                prob = 0.0
                y_data.append([prob, 1.0 - prob])
                
            else:
                # Generate noise in the motion input feature
                # Should we try adding noise to other features?
                if random_feature == 'dxdy':
                    dx = np.random.uniform(low = -MAX_DELTA, high = MAX_DELTA, size = dx.shape)
                    dy = np.random.uniform(low = -MAX_DELTA, high = MAX_DELTA, size = dy.shape)
                elif random_feature == 'lat':
                    lat = np.random.uniform(low = -1, high = 1, size = lat.shape)
                elif random_feature == 'f1f2':
                    f1 = np.random.uniform(low = 0, high = 1, size = f1.shape)
                    f1[f1>=0.97] = 1
                    f1[f1<0.97] = 0
                    f2 = np.random.uniform(low = 0, high = 1, size = f2.shape)
                    f2[f2>=0.97] = 1
                    f2[f2<0.97] = 0
                elif random_feature == 'xy':
                    x = np.random.uniform(low = 0, high = 1, size = x.shape)
                    y = np.random.uniform(low = 0, high = 1, size = y.shape)
                else:
                    print("something wrong in feature selection")
                

                prob = 0.0
                y_data.append([prob, 1.0 - prob])

            structured_data.append(np.concatenate([lat, np.array([dx]), np.array([dy]), np.array([x]), np.array([y])]))
            screen_data.append(np.array([f1,f2]).T)
            
            crop_data.append(crop)  
 

        self.screen_data_training = screen_data
        self.structured_data_training = structured_data
        self.y_data_training = y_data
        self.crop_data_training = crop_data
        
        self.shuffle_in_unison([self.screen_data_training, 
                               self.structured_data_training, 
                               self.y_data_training, 
                               self.crop_data_training])
        
        # --- For Test Data --- #
        structured_data = []
        screen_data = []
        y_data = []
        crop_data = []

        for i in range(len(self.dxs_test)):
            dx = self.dxs_test[i]
            dy = self.dys_test[i]
            lat = self.lats_test[i]
            f1 = self.f1s_test[i]
            f2 = self.f2s_test[i]
            crop = self.crops_test[i]
            x = self.xs_test[i]
            y = self.ys_test[i]

            structured_data.append(np.concatenate([lat, np.array([dx]), np.array([dy]), np.array([x]), np.array([y])]))
            screen_data.append(np.array([f1,f2]).T)
            prob = 1.0
            y_data.append([prob, 1.0 - prob])

            crop_data.append(crop)
            
            '''
            random_feature = np.random.choice(input_features)
            idx = np.random.randint(0, len(self.dxs_test))
            
            if random_feature == 'dx':
                dx = self.dxs_test[idx]
            elif random_feature == 'dy':
                dx = self.dys_test[idx]
            elif random_feature == 'lat':
                dx = self.lats_test[idx]
            elif random_feature == 'f1':
                dx = self.f1s_test[idx]
            elif random_feature == 'f2':
                dx = self.f2s_test[idx]
            elif random_feature == 'x':
                dx = self.xs_test[idx]
            elif random_feature == 'y':
                dx = self.ys_test[idx]
                
            prob = np.random.random() / 2.0 + 0.25
            structured_data.append(np.concatenate([lat, np.array([dx]), np.array([dy]), np.array([x]), np.array([y])]))
            screen_data.append(np.array([f1,f2]).T)
            y_data.append([prob, 1.0 - prob])
            
            crop_data.append(crop)
            '''
            
            # Generate noise in the motion input feature
            # Should we try adding noise to other features?
            # dx = np.random.uniform(low=-MAX_DELTA, high=MAX_DELTA)
            # dy = np.random.uniform(low=-MAX_DELTA, high=MAX_DELTA)

            # structured_data.append(np.concatenate([lat, np.array([dx]), np.array([dy]), np.array([x]), np.array([y])]))
            # screen_data.append(np.array([f1,f2]).T)
            # y_data.append([0.0, 1.0])
            # crop_data.append(crop)            
                     
        self.screen_data_test = screen_data
        self.structured_data_test = structured_data
        self.y_data_test = y_data
        self.crop_data_test = crop_data

        self.shuffle_in_unison([self.screen_data_test, 
                               self.structured_data_test, 
                               self.y_data_test, 
                               self.crop_data_test])

    def augment_data(self, n_nearby=5, n_noise=1):
        std_dev = self.std_dev / MOTION_SCALE
        # --- For Training Data --- #
        #  Generate negative examples
        ## for each positive examples
        ### sample n examples from the gaussian about the positive example
        ### the n examples have position 
        # norm.pdf(1.1, loc=1)/norm.pdf(1, loc=1.0)
        structured_data = []
        screen_data = []
        y_data = []
        crop_data = []
        
        for i in range(len(self.dxs_training)):
            dx = self.dxs_training[i]
            dy = self.dys_training[i]
            lat = self.lats_training[i]
            f1 = self.f1s_training[i]
            f2 = self.f2s_training[i]
            crop = self.crops_training[i]
            x = self.xs_training[i]
            y = self.ys_training[i]

            # Generate nearby 'almost' groundtruths
            for j in range(n_nearby):
                dx_buf = norm.rvs(loc=dx, scale=std_dev)
                dy_buf = norm.rvs(loc=dy, scale=std_dev)

                dx_prob = norm.pdf(dx_buf, loc=dx, scale=std_dev) / norm.pdf(dx, loc=dx, scale=std_dev)
                dy_prob = norm.pdf(dy_buf, loc=dy, scale=std_dev) / norm.pdf(dy, loc=dy, scale=std_dev)
                
                structured_data.append(np.concatenate([lat, np.array([dx_buf]), np.array([dy_buf]), np.array([x]), np.array([y])]))            
                screen_data.append(np.array([f1,f2]).T)
                y_data.append([dx_prob * dy_prob, 1.0 - dx_prob * dy_prob])
                crop_data.append(crop)

            # Generate noise
            for j in range(n_noise):
                dx_buf = np.random.uniform(low=-MAX_DELTA, high=MAX_DELTA)
                dy_buf = np.random.uniform(low=-MAX_DELTA, high=MAX_DELTA)
                dx_prob = 0.0
                dy_prob = 0.0

                structured_data.append(np.concatenate([lat, np.array([dx_buf]), np.array([dy_buf]), np.array([x]), np.array([y])]))
                screen_data.append(np.array([f1,f2]).T)
                y_data.append([dx_prob * dy_prob, 1.0 - dx_prob * dy_prob])
                crop_data.append(crop)            

            structured_data.append(np.concatenate([lat, np.array([dx]), np.array([dy]), np.array([x]), np.array([y])]))
            screen_data.append(np.array([f1,f2]).T)
            y_data.append([1.0, 0.0])
            crop_data.append(crop)

        self.screen_data_training = screen_data
        self.structured_data_training = structured_data
        self.y_data_training = y_data
        self.crop_data_training = crop_data
        
        self.shuffle_in_unison([self.screen_data_training, 
                               self.structured_data_training, 
                               self.y_data_training, 
                               self.crop_data_training])
        
        # --- For Test Data --- #
        #  Generate negative examples
        ## for each positive examples
        ### sample n examples from the gaussian about the positive example
        ### the n examples have position 
        # norm.pdf(1.1, loc=1)/norm.pdf(1, loc=1.0)
        structured_data = []
        screen_data = []
        y_data = []
        crop_data = []
        

        for i in range(len(self.dxs_test)):
            dx = self.dxs_test[i]
            dy = self.dys_test[i]
            lat = self.lats_test[i]
            f1 = self.f1s_test[i]
            f2 = self.f2s_test[i]
            crop = self.crops_test[i]
            x = self.xs_test[i]
            y = self.ys_test[i]

            # Generate nearby 'almost' groundtruths
            for j in range(n_nearby):
                dx_buf = norm.rvs(loc=dx, scale=std_dev)
                dy_buf = norm.rvs(loc=dy, scale=std_dev)

                dx_prob = norm.pdf(dx_buf, loc=dx, scale=std_dev) / norm.pdf(dx, loc=dx, scale=std_dev)
                dy_prob = norm.pdf(dy_buf, loc=dy, scale=std_dev) / norm.pdf(dy, loc=dy, scale=std_dev)
                
                structured_data.append(np.concatenate([lat, np.array([dx_buf]), np.array([dy_buf]), np.array([x]), np.array([y])]))            
                screen_data.append(np.array([f1,f2]).T)
                y_data.append([dx_prob * dy_prob, 1.0 - dx_prob * dy_prob])
                crop_data.append(crop)

            # Generate noise
            for j in range(n_noise):
                dx_buf = np.random.uniform(low=-MAX_DELTA, high=MAX_DELTA)
                dy_buf = np.random.uniform(low=-MAX_DELTA, high=MAX_DELTA)
                dx_prob = 0.0
                dy_prob = 0.0

                structured_data.append(np.concatenate([lat, np.array([dx_buf]), np.array([dy_buf]), np.array([x]), np.array([y])]))
                screen_data.append(np.array([f1,f2]).T)
                y_data.append([dx_prob * dy_prob, 1.0 - dx_prob * dy_prob])
                crop_data.append(crop)            

            structured_data.append(np.concatenate([lat, np.array([dx]), np.array([dy]), np.array([x]), np.array([y])]))
            screen_data.append(np.array([f1,f2]).T)
            y_data.append([1.0,0.0])
            crop_data.append(crop)

        self.screen_data_test = screen_data
        self.structured_data_test = structured_data
        self.y_data_test = y_data
        self.crop_data_test = crop_data
        
        self.shuffle_in_unison(self.screen_data_test, 
                       self.structured_data_test, 
                       self.y_data_test, 
                       self.crop_data_test)

    def view_screen_feature_effect(self):
        global MOTION_SCALE
        global MAX_DELTA
        global FRAME_HEIGHT
        global FRAME_WIDTH
        
        # Retreive positive examples
        pos = self.bag.query('SELECT a1.crop, f1.bitmap, f2.bitmap, (a2.x - a1.x), (a2.y - a1.y), a1.x, a1.y FROM particles p, assoc a1, assoc a2, frames f1, frames f2 WHERE a1.frame == a2.frame - 1 AND a1.particle == a2.particle AND p.id == a1.particle AND f1.frame == a1.frame AND f2.frame == a2.frame ORDER BY a1.frame limit 1')
        print('dataset',len(pos))

        pos = zip(*pos)

        crops, f1s, f2s, dxs, dys, xs, ys = pos
        
        pos = self.bag.query('SELECT f1.bitmap, f2.bitmap FROM frames f1, frames f2 WHERE f1.frame == f2.frame-1  ORDER BY f1.frame ')
        pos = zip(*pos)
        f1s, f2s = pos
        
        dxs = np.array(dxs)
        dxs /= MOTION_SCALE
        
        dys = np.array(dys)
        dys /= MOTION_SCALE
        
        xs = np.array(xs)
        xs /= FRAME_WIDTH
        ys = np.array(ys)
        ys /= FRAME_HEIGHT

        f1s = np.array([np.frombuffer(f1, dtype='uint8').reshape(64,64) for f1 in f1s], dtype='float64')
        f2s = np.array([np.frombuffer(f2, dtype='uint8').reshape(64,64) for f2 in f2s], dtype='float64')
        f1s /= 255.0
        f2s /= 255.0

        crops = np.array([self.CC.preproc(np.frombuffer(crop, dtype="uint8").reshape(64, 64)) for crop in crops])
        
        crops = crops.reshape(len(crops), 64, 64, 1).astype('float64')
        lats = self.CC.encoder.predict(crops)
    

        
        vw = cv2.VideoWriter('/local/scratch/mot/data/videos/deepVelocity/tmp5_local_hyp.avi', 0 , 24, (101, 101), False)

        for frame in range(499):
            if not frame % 10:
                print 'frame', frame
            structured_data_vis = []
            screen_data_vis = []
            
            for i in range(101):
                for j in range(101):
                    dx = (i-50) / MOTION_SCALE
                    dy = (j-50) / MOTION_SCALE
                    structured_vec = np.concatenate([lats[0], np.array([dx]), np.array([dy]), np.array([xs[0]]), np.array([ys[0]])])
                    screen_vec = np.array([f1s[frame] ,f2s[frame]]).T
                    structured_data_vis.append(structured_vec)
                    screen_data_vis.append(screen_vec)

            # print('vis data generated')
            structured_data_vis = np.array(structured_data_vis)
            screen_data_vis = np.array(screen_data_vis)
    
            probs = self.DV.deep_velocity.predict([structured_data_vis, screen_data_vis])[:,0]
            # print('vis data predicted')
    
            buf = np.zeros((101,101))
            count = 0
            for i in range(101):
                for j in range(101):
                    buf[j,i] = probs[count]
                    count += 1
            vw.write(np.uint8(255*buf/np.max(buf)))
        vw.release()
                
    def gkern(self, l=5, sig=1.):
        """
        creates gaussian kernel with side length l and a sigma of sig
        """
    
        ax = np.arange(-l // 2 + 1., l // 2 + 1.)
        xx, yy = np.meshgrid(ax, ax)
    
        kernel = np.exp(-(xx**2 + yy**2) / (2. * sig**2))
    
        return kernel / np.sum(kernel) 

    def fetch_data(self, n=None):
        global MOTION_SCALE
        global MAX_DELTA
        global FRAME_HEIGHT
        global FRAME_WIDTH
        
        # Retreive positive examples
        pos = self.bag.query('SELECT a1.crop, f1.bitmap, f2.bitmap, (a2.x - a1.x), (a2.y - a1.y), a1.x, a1.y FROM particles p, assoc a1, assoc a2, frames f1, frames f2 WHERE a1.frame == a2.frame - 1 AND a1.particle == a2.particle AND p.id == a1.particle AND f1.frame == a1.frame AND f2.frame == a2.frame ORDER BY a1.frame')
        print('dataset',len(pos))

        pos = zip(*pos)

        crops, f1s, f2s, dxs, dys, xs, ys = pos

        dxs = np.array(dxs)
        dxs /= MOTION_SCALE
        
        dys = np.array(dys)
        dys /= MOTION_SCALE
        
        xs = np.array(xs)
        xs /= FRAME_WIDTH 
        ys = np.array(ys)
        ys /= FRAME_HEIGHT 

        f1s = np.array([np.frombuffer(f1, dtype='uint8').reshape(64,64) for f1 in f1s], dtype='float64')
        f2s = np.array([np.frombuffer(f2, dtype='uint8').reshape(64,64) for f2 in f2s], dtype='float64')
        f1s /= 255.0
        f2s /= 255.0

        crops = np.array([self.CC.preproc(np.frombuffer(crop, dtype="uint8").reshape(64, 64)) for crop in crops])
        
        crops = crops.reshape(len(crops), 64, 64, 1).astype('float64')
        lats = self.CC.encoder.predict(crops)
        
        # Get unprocessed crops for viewing later
        crops = pos[0]
        crops = np.array([np.frombuffer(crop, dtype="uint8").reshape(64, 64) for crop in crops])

        if self.verbose:
            print("Dataset loaded", len(crops), "samples")
        # Optional: reduce dataset size
        # n = 1000
        if n is not None:
            crops = crops[:n]
            lats = lats[:n]
            dxs = dxs[:n]
            dys = dys[:n]
            f1s = f1s[:n]
            f2s = f2s[:n]
            xs = xs[:n]
            ys = ys[:n]
            
            if self.verbose:
                print("Dataset reduced to", len(crops), "samples")

        split = int(0.8 * len(crops))

        self.shuffle_in_unison([crops, lats, dxs, dys, f1s, f2s, xs, ys])

        self.crops_training = crops[:split]
        self.lats_training = lats[:split]
        self.dxs_training = dxs[:split]
        self.dys_training = dys[:split]
        self.f1s_training = f1s[:split]
        self.f2s_training = f2s[:split]
        self.xs_training = xs[:split]
        self.ys_training = ys[:split]
        
        self.crops_test = crops[split:]
        self.lats_test = lats[split:]
        self.dxs_test = dxs[split:]
        self.dys_test = dys[split:]
        self.f1s_test = f1s[split:]
        self.f2s_test = f2s[split:]
        self.xs_test = xs[split:]
        self.ys_test = ys[split:]

    def train(self, epochs=1, batch_size=128):
        self.training_loss = []
        self.test_loss = []

        metrics = self.DV.deep_velocity.metrics_names
        
        for i in range(epochs):
            if self.curr_epoch == 0:
                self.augment_data2()
            else:
                start = time.time()
                self.augment_data3()
                print('data augmented', time.time() - start)
            # Train
            loss = []
            start = time.time()
            for j in range(0, len(self.structured_data_training), batch_size):
                if len(self.structured_data_training) - j < batch_size:
                    continue

                structured_data_batch = np.array(self.structured_data_training[j:j+batch_size])
                screen_data_batch = np.array(self.screen_data_training[j:j+batch_size])
                y_data_batch = self.y_data_training[j:j+batch_size]

                loss.append(self.DV.deep_velocity.train_on_batch([structured_data_batch, screen_data_batch], y_data_batch))

            loss = np.mean(loss, axis=0)
            self.training_loss.append(loss)
            
            print("Training loss -  epoch", i+1, " - ", time.time() - start, "s - ", [metrics[k] +': '+ str(loss[k]) for k in range(len(metrics))])

            # Test
            loss = []
            start = time.time()
            for j in range(0, len(self.structured_data_test), batch_size):
                if len(self.structured_data_test) - j < batch_size:
                    continue

                structured_data_batch = np.array(self.structured_data_test[j:j+batch_size])
                screen_data_batch = np.array(self.screen_data_test[j:j+batch_size])
                y_data_batch = self.y_data_test[j:j+batch_size]

                loss.append(self.DV.deep_velocity.test_on_batch([structured_data_batch, screen_data_batch], y_data_batch))

            loss = np.mean(loss, axis=0)
            self.test_loss.append(loss)
            print("Test loss     -  epoch", i+1, " - ", time.time() - start, "s - ", [metrics[k] +': '+ str(loss[k]) for k in range(len(metrics))])
            self.curr_epoch += 1
            
    def save(self, path):
        self.DV.save(path)

    def load(self, path):
        self.DV.load(path)

    def view(self, scale = 1.0, view_set='test'):
        ####
        # Cycle through real training or test examples and view network performance
        scale = scale
        plt1 = None
        for n in range(100):
            if view_set == 'test':
                idx = np.random.randint(0, len(self.structured_data_test))
                structured_data_single = self.structured_data_test[idx]
                screen_data_single = self.screen_data_test[idx]
                y_data_single = self.y_data_test[idx]
                crop = self.crop_data_test[idx]
            elif view_set == 'training':
                idx = np.random.randint(0, len(self.structured_data_training))
                structured_data_single = self.structured_data_training[idx]
                screen_data_single = self.screen_data_training[idx]
                y_data_single = self.y_data_training[idx]
                crop = self.crop_data_training[idx]              

            structured_data_vis = []
            screen_data_vis = []

            gt_dx = int(structured_data_single[64] * MOTION_SCALE * scale + 50)
            gt_dy = int(structured_data_single[65] * MOTION_SCALE * scale + 50)

            x = structured_data_single[66]
            y = structured_data_single[67]
            print('x:', x * FRAME_WIDTH)
            print('y:', y * FRAME_HEIGHT)
            for i in range(101):
                for j in range(101):
                    dx = (i-50) / (MOTION_SCALE * scale)
                    dy = (j-50) / (MOTION_SCALE * scale)
                    vec = structured_data_single[:64]
                    structured_vec = np.concatenate([vec, np.array([dx]), np.array([dy]), np.array([x]), np.array([y])])
                    screen_vec = screen_data_single
                    structured_data_vis.append(structured_vec)
                    screen_data_vis.append(screen_vec)


            print('vis data generated')
            structured_data_vis = np.array(structured_data_vis)
            screen_data_vis = np.array(screen_data_vis)

            probs = self.DV.deep_velocity.predict([structured_data_vis, screen_data_vis])[:,0]
            print('vis data predicted')

            buf = np.zeros((101,101))
            count = 0
            for i in range(101):
                for j in range(101):
                    buf[j,i] = probs[count]
                    count += 1
                    
            xbar, ybar, cov = self.intertial_axis(buf)
            print((xbar-50)/scale, (ybar-50)/scale, np.sqrt(cov[0][0]/scale), np.sqrt(cov[1,1]/scale))
            
            print('local min:', np.min(buf), 'local max:', np.max(buf))
            
            gt = np.zeros((101,101))
            try:
                for i in [-1,0,1]:
                    for j in [-1,0,1]:
                        gt[gt_dy+i, gt_dx+j] = 1
            except IndexError:
                print('gt error')

            print('ground truth', gt_dx-50, gt_dy-50, 'scale:', scale)

            prob_gt = np.zeros((101,101))
            prob_gt.fill(y_data_single[0])

            try:
                prob_hyp = np.zeros((101,101))
                prob_hyp.fill(buf[gt_dy, gt_dx])
            except IndexError:
                print('prob_hyp error')

            print('visualization prepared')
            
            shape = screen_data_single.shape
            screen_data_single_RGB = np.zeros((shape[0], shape[1], shape[2]+1))
            screen_data_single_RGB[:,:,:2] = screen_data_single
            screen_data_single_RGB = np.rot90(screen_data_single_RGB)
            
            if plt1 is None:
                ####
                # ax = plt.subplot(111)
                # plt1 = plt.imshow(buf, vmin=0.0, vmax=1.0, extent=[-50/scale,50/scale,-50/scale,50/scale])
                # ax.set_ylim(-50/scale,50/scale)
                # ax.set_xlim(-50/scale,50/scale)
                ####
                
                ax = plt.subplot(231)
                ax.set_title('Particle')
                ax.set_axis_off()
                plt1 = plt.imshow(crop.squeeze(), cmap='gray', vmin=0, vmax=255) 
                ax = plt.subplot(232)
                ax.set_title('Particle Neighbourhood Prediction')
                plt2 = plt.imshow(buf, vmin=0, vmax=1, extent=[-50/scale,50/scale,-50/scale,50/scale])
                ax.set_ylim(-50/scale,50/scale)
                ax.set_xlim(-50/scale,50/scale)
                ax = plt.subplot(233)
                ax.set_title('Network Velocity Probability')
                ax.set_axis_off()
                plt3 = plt.imshow(prob_hyp, vmin=0, vmax=1)
                ax = plt.subplot(234)
                ax.set_title('Screen Feature')
                ax.set_axis_off()
                plt4 = plt.imshow(screen_data_single_RGB)
                ax = plt.subplot(235)
                ax.set_title('GT Delta')
                ax.set_ylim(-50/scale,50/scale)
                ax.set_xlim(-50/scale,50/scale)
                plt5 = plt.imshow(gt*255, cmap='gray', vmin=0, vmax=255, extent=[-50/scale,50/scale,-50/scale,50/scale])
                ax = plt.subplot(236)
                ax.set_title('GT Velocity Probability')
                ax.set_axis_off()
                plt6 = plt.imshow(prob_gt, vmin=0, vmax=1)
            else:
                ####
                # plt.subplot(111)
                # plt1.set_data(buf*255)
                ####
                plt.subplot(231)
                plt1.set_data(crop.squeeze())
                plt.subplot(232)
                plt2.set_data(buf)
                plt.subplot(233)
                plt3.set_data(prob_hyp)
                plt.subplot(234)
                plt4.set_data(screen_data_single_RGB)
                plt.subplot(235)
                plt5.set_data(gt*255)
                plt.subplot(236)
                plt6.set_data(prob_gt)
            # plt.colorbar()
            plt.draw()
            plt.waitforbuttonpress(0)

        #####

    # https://stackoverflow.com/questions/9005659/compute-eigenvectors-of-image-in-python/9007249#9007249
    def raw_moment(self, data, iord, jord):
        nrows, ncols = data.shape
        y, x = np.mgrid[:nrows, :ncols]
        data = data * x**iord * y**jord
        return data.sum()

    # https://stackoverflow.com/questions/9005659/compute-eigenvectors-of-image-in-python/9007249#9007249
    def intertial_axis(self, data):
        """Calculate the x-mean, y-mean, and cov matrix of an image."""
        data_sum = data.sum()
        m10 = self.raw_moment(data, 1, 0)
        m01 = self.raw_moment(data, 0, 1)
        x_bar = m10 / data_sum
        y_bar = m01 / data_sum
        u11 = (self.raw_moment(data, 1, 1) - x_bar * m01) / data_sum
        u20 = (self.raw_moment(data, 2, 0) - x_bar * m10) / data_sum
        u02 = (self.raw_moment(data, 0, 2) - y_bar * m01) / data_sum
        cov = np.array([[u20, u11], [u11, u02]])
        return x_bar, y_bar, cov
    