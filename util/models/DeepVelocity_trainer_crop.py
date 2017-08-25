import time

import matplotlib.pyplot as plt
import numpy as np
from keras import models

from DeepVelocity import DeepVelocity
from ClassyVCoder_1 import ClassyVCoder
from util.DataBag import DataBag
from keras.utils.np_utils import to_categorical



def fetch_data(bag):\
    # Retreive positive examples
    pos = bag.query('SELECT a2.frame, p.area, a2.x - a1.x, a2.y - a1.y FROM particles p, assoc a1, assoc a2 WHERE a1.frame == a2.frame - 1 AND a1.particle == a2.particle AND p.id == a1.particle ORDER BY a1.frame')
    pos = np.array([np.array(i) for i in pos])

    N = pos.shape[0]
    pos = np.c_[pos, np.ones(N)]
    



    # Generate negative examples
    neg = []
    for frame, a, dx, dy, V in pos:
        bag.query('select p.area,  a2.x - a1.x, a2.y - a1.y FROM particles p, assoc a1, assoc a2 WHERE a1.frame == a2.frame - 1 AND a1.particle == a2.particle AND p.id == a1.particle ORDER BY a1.frame')



    # neg = []
    # for a, dx, dy, V in pos:
    #     jx = np.random.normal()
    #     jy = np.random.normal()
    #     neg.append((a, dx+jx, dy+jy))

    # neg = np.array([np.array(i) for i in neg])
    # neg = np.c_[neg, np.zeros(N)]

    return np.concatenate((pos, neg))

bags_path = '/mnt/SIA/Experiments/bags/'
backgrounds_path = '/local/scratch/mot/data/backgrounds/'
videos_path = '/mnt/SIA/'
batch_directory = 'validation/'
        
bag = DataBag(bags_path + batch_directory + 'val9.db')
data = fetch_data(bag)
    
print data.shape
np.random.shuffle(data)
split = int(0.8 * len(data))
data_training = data[:split]
data_test = data[split:]

DV = DeepVelocity(input_shape=(3,))

CC = ClassyVCoder()
CC.load("/local/scratch/mot/util/models/ClassyVCoder_1.h5")

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

