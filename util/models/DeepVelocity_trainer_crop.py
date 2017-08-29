%load_ext autoreload

import time

import matplotlib.pyplot as plt
import numpy as np
from keras import models

from DeepVelocity import DeepVelocity
from ClassyVCoder_1 import ClassyVCoder
from util.DataBag import DataBag
from keras.utils.np_utils import to_categorical



def fetch_data(bag):
    # Retreive positive examples
    pos = bag.query('SELECT a2.frame, p.id, p.area, a2.x - a1.x, a2.y - a1.y FROM particles p, assoc a1, assoc a2 WHERE a1.frame == a2.frame - 1 AND a1.particle == a2.particle AND p.id == a1.particle ORDER BY a1.frame')
    pos = np.array([np.array(i) for i in pos])

    #  Generate negative examples
    neg = []
    for frame, pid, a, dx, dy in pos:
        # res = bag.query('select SQRT(SQUARE(a2.x - a1.x) + SQUARE(a2.y - a1.y)) as delta, p.area, a2.x - a1.x, a2.y - a1.y FROM particles p, assoc a1, assoc a2 WHERE a1.frame == a2.frame - 1 AND a1.particle != a2.particle AND p.id == a2.particle AND a1.particle == '+str(pid)+' ORDER BY delta ASC LIMIT 1')
        res = bag.query('select SQRT(SQUARE(a3.x - a2.x) + SQUARE(a3.y - a2.y)) as delta, p.area, a3.x - a1.x, a3.y - a1.y FROM particles p, assoc a1, assoc a2, assoc a3 WHERE a1.frame == a2.frame - 1 AND a2.frame == a3.frame AND a1.particle == a2.particle AND a1.particle != a3.particle AND p.id == a3.particle AND a1.particle == '+str(pid)+' ORDER BY delta ASC LIMIT 1')
        neg.append(res[0])
    neg = np.array([np.array(i) for i in neg])

    N = pos.shape[0]

    pos = pos[:,2:]
    neg = neg[:,1:]

    pos = np.c_[pos, np.ones(N)]
    neg = np.c_[neg, np.zeros(N)]

    return np.concatenate((pos, neg))

bags_path = '/mnt/SIA/Experiments/bags/'
backgrounds_path = '/local/scratch/mot/data/backgrounds/'
videos_path = '/mnt/SIA/'
batch_directory = 'validation/'

magic_size_norm = 2000.0
magic_vel_norm = 200.0
magic_norm = [magic_size_norm, magic_vel_norm, magic_vel_norm, 1]
bag = DataBag(bags_path + batch_directory + 'val9.db')
data = fetch_data(bag)
data /= magic_norm
print np.max(data, axis=0)
print data.shape
np.random.shuffle(data)
split = int(0.8 * len(data))
data_training = data[:split]
data_test = data[split:]

DV = DeepVelocity(input_shape=(3,))

# CC = ClassyVCoder()
# CC.load("/local/scratch/mot/util/models/ClassyVCoder_1.h5")

epochs = 30
batch_size = 128

metrics = DV.deep_velocity.metrics_names
for i in range(epochs):

    # Train
    loss = []
    start = time.time()
    for j in range(0, len(data_training), batch_size):
        data_batch = data_training[j:j+batch_size]
        x_data, y_data = data_batch[:,:3], to_categorical(data_batch[:,3:])
        loss.append(DV.deep_velocity.train_on_batch(x_data, y_data))

    loss = np.mean(loss, axis=0)
    print "Training loss -  epoch", i+1, " - ", time.time() - start, "s - ", [metrics[k] +': '+ str(loss[k]) for k in range(len(metrics))]

    # Test
    loss = []
    start = time.time()
    for j in range(0, len(data_test), batch_size):
        data_batch = data_test[j:j+batch_size]
        x_data, y_data = data_batch[:,:3], to_categorical(data_batch[:,3:])
        loss.append(DV.deep_velocity.test_on_batch(x_data, y_data))

    loss = np.mean(loss, axis=0)
    print "Test loss     -  epoch", i+1, " - ", time.time() - start, "s - ", [metrics[k] +': '+ str(loss[k]) for k in range(len(metrics))]

models.save_model(DV.deep_velocity, "/local/scratch/mot/util/models/DeepVelocity.h5")

import numpy as np
from util.functions_cv3 import *
%matplotlib tk

count = 0
res1 = np.zeros((101,101))
res1.fill(127)
res2 = np.zeros((101,101))
res2.fill(127)

for a, dx, dy, V in data:
    dx = int(round(dx*200))
    dy = int(round(dy*200))
    if abs(dx) > 50 or abs(dy) > 50:
        print dx, dy
        count += 1
        continue

    if V:
        buf = res1
    else:
        buf = res2

    if a*2000 > 200:
        buf[50+dy, 50+dx] = 255 - 0.5 * (255 - buf[50+dy, 50+dx])
    else:
        buf[50+dy, 50+dx] = buf[50+dy, 50+dx] * 0.5
print count

disp_two(res1, res2)

results = []
for k in range(50,1000, 10):
    print k
    buf = np.zeros((101,101))

    inputs = []
    for i in range(101):
        for j in range(101):
            dx = i-50
            dy = j-50
            vec = np.array([k / magic_size_norm, dx / magic_vel_norm, dy / magic_vel_norm])
            inputs.append(vec)

    inputs = np.array(inputs)
    probs = DV.deep_velocity.predict(inputs)[:,1]

    count = 0
    for i in range(101):
        for j in range(101):
            buf[j,i] = probs[count]
            count += 1

    results.append(buf)
import cv2
vw = cv2.VideoWriter('DeepVelView.avi', 0, 15, (101,101), False)

for frame in results:
    vw.write(np.uint8(255*frame))
vw.release()
