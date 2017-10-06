# %load_ext autoreload

import time

import matplotlib.pyplot as plt
import numpy as np
from keras import models

from DeepVelocity import DeepVelocityV2
from ClassyVCoder_1 import ClassyVCoder
from util.DataBag import DataBag
from keras.utils.np_utils import to_categorical
from util.FrameGrabber import FrameGrabber

import cv2

from scipy.stats import norm

MOTION_SCALE = 1.0
MAX_DELTA = 3000
# https://stackoverflow.com/questions/4601373/better-way-to-shuffle-two-numpy-arrays-in-unison
def shuffle_in_unison(a, b, c, d):
    rng_state = np.random.get_state()
    np.random.shuffle(a)
    np.random.set_state(rng_state)
    np.random.shuffle(b)
    np.random.set_state(rng_state)
    np.random.shuffle(c)
    np.random.set_state(rng_state)
    np.random.shuffle(d)    

def fetch_data(bag, CC):
    global MOTION_SCALE
    global MAX_DELTA
    # Retreive positive examples
    pos = bag.query('SELECT a1.crop, f1.bitmap, f2.bitmap, (a2.x - a1.x), (a2.y - a1.y) FROM particles p, assoc a1, assoc a2, frames f1, frames f2 WHERE a1.frame == a2.frame - 1 AND a1.particle == a2.particle AND p.id == a1.particle AND f1.frame == a1.frame AND f2.frame == a2.frame ORDER BY a1.frame')
    pos = zip(*pos)

    crops, f1s, f2s, xs, ys = pos

    xs = np.array(xs)
    xs /= MOTION_SCALE
    ys = np.array(ys)
    ys /= MOTION_SCALE

    #  Generate negative examples
    ## for each positive examples
    ### sample n examples from the gaussian about the positive example
    ### the n examples have position 
    # norm.pdf(1.1, loc=1)/norm.pdf(1, loc=1.0)
    structured_data = []
    screen_data = []
    y_data = []
    crop_data = []

    n = 2
    std_dev = 3.0 / MOTION_SCALE

    f1s = np.array([np.frombuffer(f1, dtype='uint8').reshape(64,64) for f1 in f1s], dtype='float64')
    f2s = np.array([np.frombuffer(f2, dtype='uint8').reshape(64,64) for f2 in f2s], dtype='float64')
    f1s /= 255.0
    f2s /= 255.0

    crops = np.array([np.frombuffer(crop, dtype="uint8").reshape(64, 64) for crop in crops])
    crops = crops.reshape(len(crops), 64, 64, 1).astype('float64')
    crops /= 255.0

    lats = CC.encoder.predict(crops)

    for i in range(len(xs)):
        x = xs[i]
        y = ys[i]
        lat = lats[i]
        f1 = f1s[i]
        f2 = f2s[i]
        crop = crops[i]

        # Generate nearby 'almost' groundtruths
        for j in range(n):
            x_buf = norm.rvs(loc=x, scale=std_dev)
            y_buf = norm.rvs(loc=y, scale=std_dev)

            x_prob = norm.pdf(x_buf, loc=x, scale=std_dev) / norm.pdf(x, loc=x, scale=std_dev)
            y_prob = norm.pdf(y_buf, loc=y, scale=std_dev) / norm.pdf(y, loc=y, scale=std_dev)
            
            structured_data.append(np.concatenate([lat, np.array([x_buf]), np.array([y_buf])]))            
            screen_data.append(np.array([f1,f2]).T)
            y_data.append([x_prob * y_prob, 1.0 - x_prob * y_prob])
            crop_data.append(crop)

        # Generate noise
        for j in range(n):
            x_buf = np.random.uniform(low=-MAX_DELTA, high=MAX_DELTA)
            y_buf = np.random.uniform(low=-MAX_DELTA, high=MAX_DELTA)
            x_prob = 0.0
            y_prob = 0.0

            structured_data.append(np.concatenate([lat, np.array([x_buf]), np.array([y_buf])]))
            screen_data.append(np.array([f1,f2]).T)
            y_data.append([x_prob * y_prob, 1.0 - x_prob * y_prob])
            crop_data.append(crop)            

        structured_data.append(np.concatenate([lat, np.array([x]), np.array([y])]))
        screen_data.append(np.array([f1,f2]).T)
        y_data.append([1.0,0.0])
        crop_data.append(crop)

    return screen_data, structured_data, y_data, crop_data


def fetch_data_old(bag, CC):
    # Retreive positive examples
    pos = bag.query('SELECT a1.crop, a2.frame, p.id, (a2.x - a1.x)/200, (a2.y - a1.y)/200 FROM particles p, assoc a1, assoc a2 WHERE a1.frame == a2.frame - 1 AND a1.particle == a2.particle AND p.id == a1.particle ORDER BY a1.frame')
    pos = zip(*pos)
    crops, pos = pos[0], pos[1:]
    pos = zip(*pos)
    pos = np.array([np.array(i) for i in pos])

    #  Generate negative examples
    neg = []
    for frame, pid, dx, dy in pos:
        # res = bag.query('select SQRT(SQUARE(a2.x - a1.x) + SQUARE(a2.y - a1.y)) as delta, p.area, a2.x - a1.x, a2.y - a1.y FROM particles p, assoc a1, assoc a2 WHERE a1.frame == a2.frame - 1 AND a1.particle != a2.particle AND p.id == a2.particle AND a1.particle == '+str(pid)+' ORDER BY delta ASC LIMIT 1')
        res = bag.query('SELECT SQRT(SQUARE(a3.x - a2.x) + SQUARE(a3.y - a2.y)) as delta, (a3.x - a1.x)/200, (a3.y - a1.y)/200 FROM particles p, assoc a1, assoc a2, assoc a3 WHERE a1.frame == a2.frame - 1 AND a2.frame == a3.frame AND a1.particle == a2.particle AND a1.particle != a3.particle AND p.id == a3.particle AND a1.particle == '+str(pid)+' ORDER BY delta ASC LIMIT 1')
        neg.append(res[0])
    neg = np.array([np.array(i) for i in neg])

    N = pos.shape[0]

    pos = pos[:,2:]
    neg = neg[:,1:]
    pos = bag.query('SELECT a1.crop, f1.bitmap, f2.bitmap, (a2.x - a1.x)/200, (a2.y - a1.y)/200 FROM particles p, assoc a1, assoc a2, frames f1, frames f2 WHERE a1.frame == a2.frame - 1 AND a1.particle == a2.particle AND p.id == a1.particle AND f1.frame == a1.frame AND f2.frame == a2.frame ORDER BY a1.frame')
    pos = np.c_[pos, np.ones(N)]
    neg = np.c_[neg, np.zeros(N)]

    crops = np.array([np.frombuffer(crop, dtype="uint8").reshape(64, 64) for crop in crops])
    crops = crops.reshape(len(crops), 64, 64, 1).astype('float64')
    crops /= 255.0

    lat = CC.encoder.predict(crops)

    pos = np.concatenate((lat, pos), axis=1)
    neg = np.concatenate((lat, neg), axis=1)

    return np.concatenate((pos, neg))


bags = ['/local/scratch/mot/data/bags/Experimental/T02660_tracking.db',
        '/mnt/SIA/Experiments/bags/Curated/T02406_tracking_1.db']

# bags = ['/mnt/SIA/Experiments/bags/Curated/T02404_tracking20_300.db']

CC = ClassyVCoder()
CC.load("/local/scratch/mot/util/models/ClassyVCoder_1.h5")

screen_data, structured_data, y_data, crops = [], [], [], []
for bag_name in bags:
    bag = DataBag(bag_name)
    screen_data_buf, structured_data_buf, y_data_buf, crops_buf = fetch_data(bag, CC)
    screen_data.extend(screen_data_buf)
    structured_data.extend(structured_data_buf)
    y_data.extend(y_data_buf)
    crops.extend(crops_buf)

print 'number of data samples', len(y_data)    
shuffle_in_unison(screen_data, structured_data, y_data, crops)

# reduce dataset size
# N = 2000
# screen_data, structured_data, y_data, crops = screen_data[:N], structured_data[:N], y_data[:N], crops[:N]

split = int(0.8 * len(screen_data))
structured_data_training = structured_data[:split]
structured_data_test = structured_data[split:]
screen_data_training = screen_data[:split]
screen_data_test = screen_data[split:]
y_data_training = y_data[:split]
y_data_test = y_data[split:]
crops_training = crops[:split]
crops_test = crops[split:]
# data = np.load('val9_data')
DV = DeepVelocityV2(verbose=True)

epochs = 50
batch_size = 128

metrics = DV.deep_velocity.metrics_names
for i in range(epochs):

    # Train
    loss = []
    start = time.time()
    for j in range(0, len(structured_data_training), batch_size):
        if len(structured_data_training) - j < batch_size:
            continue

        structured_data_batch = np.array(structured_data_training[j:j+batch_size])
        screen_data_batch = np.array(screen_data_training[j:j+batch_size])
        y_data_batch = y_data_training[j:j+batch_size]

        loss.append(DV.deep_velocity.train_on_batch([structured_data_batch, screen_data_batch], y_data_batch))
        # loss.append(DV.deep_velocity.train_on_batch([np.array(x_data)], y_data))

    loss = np.mean(loss, axis=0)
    print "Training loss -  epoch", i+1, " - ", time.time() - start, "s - ", [metrics[k] +': '+ str(loss[k]) for k in range(len(metrics))]

    # Test
    loss = []
    start = time.time()
    for j in range(0, len(structured_data_test), batch_size):
        if len(structured_data_test) - j < batch_size:
            continue

        structured_data_batch = np.array(structured_data_test[j:j+batch_size])
        screen_data_batch = np.array(screen_data_test[j:j+batch_size])
        y_data_batch = y_data_test[j:j+batch_size]

        loss.append(DV.deep_velocity.test_on_batch([structured_data_batch, screen_data_batch], y_data_batch))

    loss = np.mean(loss, axis=0)
    print "Test loss     -  epoch", i+1, " - ", time.time() - start, "s - ", [metrics[k] +': '+ str(loss[k]) for k in range(len(metrics))]

models.save_model(DV.deep_velocity, "/local/scratch/mot/util/models/DeepVelocity.h5")



####
# Cycle through real training or test examples and view network performance
scale = 0.5
plt1 = None
for n in range(100):
    idx = np.random.randint(0, len(structured_data_test))
    structured_data_single = structured_data_test[idx]
    screen_data_single = screen_data_test[idx]
    y_data_single = y_data_test[idx]
    crop = crops_test[idx]



    structured_data_vis = []
    screen_data_vis = []

    

    gt_x = int(structured_data_single[16] * MOTION_SCALE * scale + 50)
    gt_y = int(structured_data_single[17] * MOTION_SCALE * scale + 50)

    for i in range(101):
        for j in range(101):
            dx = (i-50) / (MOTION_SCALE * scale)
            dy = (j-50) / (MOTION_SCALE * scale)
            vec = structured_data_single[:16]
            structured_vec = np.concatenate([vec, np.array([dx]), np.array([dy])])
            screen_vec = screen_data_single
            structured_data_vis.append(structured_vec)
            screen_data_vis.append(screen_data_single)

    print 'vis data generated'
    structured_data_vis = np.array(structured_data_vis)
    screen_data_vis = np.array(screen_data_vis)

    # buf1 = np.array([np.array([screen1, screen2]).T])
    # screen_inputs = np.zeros((len(inputs),64,64,2))
    # screen_inputs[:,:,:,:] = buf1
    probs = DV.deep_velocity.predict([structured_data_vis, screen_data_vis])[:,0]
    print 'vis data predicted'

    buf = np.zeros((101,101))
    count = 0
    for i in range(101):
        for j in range(101):
            buf[j,i] = probs[count]
            count += 1

    gt = np.zeros((101,101))

    try:
        for i in [-1,0,1]:
            for j in [-1,0,1]:
                gt[gt_y+i, gt_x+j] = 1
    except IndexError:
        print 'gt error'

    print 'ground truth', gt_x-50, gt_y-50, 'scale:', scale

    prob_gt = np.zeros((101,101))
    prob_gt.fill(y_data_single[0])

    try:
        prob_hyp = np.zeros((101,101))
        prob_hyp.fill(buf[gt_y, gt_x])
    except IndexError:
        print 'prob_hyp error'

    print 'visualization prepared'

    if plt1 is None:        
        ax = plt.subplot(231)
        ax.set_title('Particle')
        ax.set_axis_off()
        plt1 = plt.imshow(crop.squeeze()*255, cmap='gray', vmin=0, vmax=255) 
        ax = plt.subplot(232)
        ax.set_title('Particle Neighbourhood Prediction')
        plt2 = plt.imshow(buf*255, vmin=0, vmax=255, extent=[-50/scale,50/scale,-50/scale,50/scale])
        ax.set_ylim(-50/scale,50/scale)
        ax.set_xlim(-50/scale,50/scale)
        ax = plt.subplot(233)
        ax.set_title('Network Velocity Probability')
        ax.set_axis_off()
        plt3 = plt.imshow(prob_hyp*255, vmin=0, vmax=255)
        ax = plt.subplot(234)
        ax.set_title('Screen Feature')
        ax.set_axis_off()
        plt4 = plt.imshow(screen_data_single[:,:,0]*255, cmap='gray')
        ax = plt.subplot(235)
        ax.set_title('GT Delta')
        ax.set_ylim(-50/scale,50/scale)
        ax.set_xlim(-50/scale,50/scale)
        plt5 = plt.imshow(gt*255, cmap='gray', vmin=0, vmax=255, extent=[-50/scale,50/scale,-50/scale,50/scale])
        ax = plt.subplot(236)
        ax.set_title('GT Velocity Probability')
        ax.set_axis_off()
        plt6 = plt.imshow(prob_gt*255, vmin=0, vmax=255)
    else:
        plt.subplot(231)
        plt1.set_data(crop.squeeze()*255)
        plt.subplot(232)
        plt2.set_data(buf*255)
        plt.subplot(233)
        plt3.set_data(prob_hyp*255)
        plt.subplot(234)
        plt4.set_data(screen_data_single[:,:,0]*255)
        plt.subplot(235)
        plt5.set_data(gt*255)
        plt.subplot(236)
        plt6.set_data(prob_gt*255)
    plt.draw()
    plt.waitforbuttonpress(0)

#####

# ####
# # Compare maps from frame 100 to frame 200
# scale = 0.5
# plt1 = None

# idx = np.random.randint(0, len(structured_data_test))
# structured_data_single = structured_data_test[idx]
# screen_data_single = screen_data_test[idx]
# y_data_single = y_data_test[idx]
# crop = crops_test[idx]

# f1s = bag.query('SELECT DISTINCT f1.bitmap FROM frames f1 WHERE frame >= 20 and frame < 300 ORDER BY f1.frame ASC')
# frames = range(20,60)
# f1s = np.array([np.frombuffer(f1[0], dtype='uint8').reshape(64,64) for f1 in f1s], dtype='float64')
# f1s/=255.0
# vw = cv2.VideoWriter('DeepVel_std.avi', 0, 10, (202,101), False)

# for n in frames:
#     if not n%10:
#         continue

#     screen_data_single = np.array([f1s[n-1], f1s[n]]).T

#     structured_data_vis = []
#     screen_data_vis = []

#     gt_x = int(structured_data_single[16] * MOTION_SCALE * scale + 50)
#     gt_y = int(structured_data_single[17] * MOTION_SCALE * scale + 50)

#     for i in range(101):
#         for j in range(101):
#             dx = (i-50) / (MOTION_SCALE * scale)
#             dy = (j-50) / (MOTION_SCALE * scale)
#             vec = structured_data_single[:16]
#             structured_vec = np.concatenate([vec, np.array([dx]), np.array([dy])])
#             screen_vec = screen_data_single
#             structured_data_vis.append(structured_vec)
#             screen_data_vis.append(screen_data_single)

#     print 'vis data generated'
#     structured_data_vis = np.array(structured_data_vis)
#     screen_data_vis = np.array(screen_data_vis)

#     # buf1 = np.array([np.array([screen1, screen2]).T])
#     # screen_inputs = np.zeros((len(inputs),64,64,2))
#     # screen_inputs[:,:,:,:] = buf1
#     probs = DV.deep_velocity.predict([structured_data_vis, screen_data_vis])[:,0]
#     print 'vis data predicted'

#     buf = np.zeros((101,101))
#     count = 0
#     for i in range(101):
#         for j in range(101):
#             buf[j,i] = probs[count]
#             count += 1

#     temp = np.uint8(255*cv2.resize(f1s[n], (101,101)))
#     temp = np.concatenate((temp, np.uint8(255*buf)), axis=1)
#     vw.write(temp)

#     print 'frame', n, 'complete'
# vw.release()
# #####

# #####
# # Cycle through the slow to fastest moving particle
# # Fast: 321, 90, 311, 367, 261, 373, 287
# # Slow: 435, 497, 500, 490, 420, 408, 502

# scale = 1.0
# plt1 = None

# idx = np.random.randint(0, len(structured_data_test))
# structured_data_single = structured_data_test[idx]
# screen_data_single = screen_data_test[idx]
# y_data_single = y_data_test[idx]
# crop = crops_test[idx]

# crops_slow = bag.query("select a1.crop from assoc a1 where a1.particle in (523, 401, 444, 493, 534, 442, 464)")
# crops_fast = bag.query("select a1.crop from assoc a1 where a1.particle in (3676, 3959, 1291, 641, 1405, 597, 599)")
# crops_slow = np.array([np.frombuffer(crop[0], dtype="uint8").reshape(64, 64) for crop in crops_slow])
# crops_fast = np.array([np.frombuffer(crop[0], dtype="uint8").reshape(64, 64) for crop in crops_fast])

# crops_slow = crops_slow.reshape(len(crops_slow), 64, 64, 1).astype('float64')
# crops_fast = crops_fast.reshape(len(crops_fast), 64, 64, 1).astype('float64')

# crops_slow /= 255.0
# crops_fast /= 255.0

# lats_slow = CC.encoder.predict(crops_slow)
# lats_fast = CC.encoder.predict(crops_fast)

# vw = cv2.VideoWriter('DeepVel_crops.avi', 0, 2, (101,101), False)

# for n in range(7):
#     lat = lats_slow[n]
#     structured_data_vis = []
#     screen_data_vis = []

#     gt_x = int(structured_data_single[16] * MOTION_SCALE * scale + 50)
#     gt_y = int(structured_data_single[17] * MOTION_SCALE * scale + 50)

#     for i in range(101):
#         for j in range(101):
#             dx = (i-50) / (MOTION_SCALE * scale)
#             dy = (j-50) / (MOTION_SCALE * scale)
#             structured_vec = np.concatenate([lat, np.array([dx]), np.array([dy])])
#             screen_vec = screen_data_single
#             structured_data_vis.append(structured_vec)
#             screen_data_vis.append(screen_data_single)


#     print 'vis data generated'
#     structured_data_vis = np.array(structured_data_vis)
#     screen_data_vis = np.array(screen_data_vis)

#     # buf1 = np.array([np.array([screen1, screen2]).T])
#     # screen_inputs = np.zeros((len(inputs),64,64,2))
#     # screen_inputs[:,:,:,:] = buf1
#     probs = DV.deep_velocity.predict([structured_data_vis, screen_data_vis])[:,0]
#     print 'vis data predicted'

#     buf = np.zeros((101,101))
#     count = 0
#     for i in range(101):
#         for j in range(101):
#             buf[j,i] = probs[count]
#             count += 1

#     temp =  np.uint8(255*buf)
#     vw.write(temp)

# for n in range(7):
#     lat = lats_fast[n]
#     structured_data_vis = []
#     screen_data_vis = []

#     gt_x = int(structured_data_single[16] * MOTION_SCALE * scale + 50)
#     gt_y = int(structured_data_single[17] * MOTION_SCALE * scale + 50)

#     for i in range(101):
#         for j in range(101):
#             dx = (i-50) / (MOTION_SCALE * scale)
#             dy = (j-50) / (MOTION_SCALE * scale)
#             structured_vec = np.concatenate([lat, np.array([dx]), np.array([dy])])
#             screen_vec = screen_data_single
#             structured_data_vis.append(structured_vec)
#             screen_data_vis.append(screen_data_single)


#     print 'vis data generated'
#     structured_data_vis = np.array(structured_data_vis)
#     screen_data_vis = np.array(screen_data_vis)

#     # buf1 = np.array([np.array([screen1, screen2]).T])
#     # screen_inputs = np.zeros((len(inputs),64,64,2))
#     # screen_inputs[:,:,:,:] = buf1
#     probs = DV.deep_velocity.predict([structured_data_vis, screen_data_vis])[:,0]
#     print 'vis data predicted'

#     buf = np.zeros((101,101))

#     count = 0
#     for i in range(101):
#         for j in range(101):
#             buf[j,i] = probs[count]
#             count += 1
    
#     buf[:5,:5] = 1
#     temp =  np.uint8(255*buf)
#     vw.write(temp)    

#     print 'frame', n, 'complete'
# vw.release()
# #####