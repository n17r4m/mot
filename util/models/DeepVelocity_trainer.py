import sys

from DeepVelocity import DeepVelocity
import matplotlib.pyplot as plt
import numpy as np
import os, time
from util.DataBag import DataBag
from keras import models

def gkern(l=5, sig=1.):
    """
    creates gaussian kernel with side length l and a sigma of sig
    https://stackoverflow.com/questions/29731726/how-to-calculate-a-gaussian-kernel-matrix-efficiently-in-numpy
    """

    ax = np.arange(-l // 2 + 1., l // 2 + 1.)
    xx, yy = np.meshgrid(ax, ax)

    kernel = np.exp(-(xx**2 + yy**2) / (2. * sig**2))

    return kernel / np.sum(kernel)

def fetch_data(bag):
    res = bag.query('SELECT a1.frame, p.intensity, p.area, a2.x - a1.x, a2.y - a1.y FROM particles p, assoc a1, assoc a2 WHERE a1.frame == a2.frame - 1 AND a1.particle == a2.particle AND p.id == a1.particle')
    return np.array(res)

def getOutputs(deltas):
    large_value = 100000
    shape = (256, 256)
    kernel = gkern(256, 0.8)

    x_data = []
    y_data = []

    # origin = (np.array(shape) - 1) / 2.0

    for frame, intensity, area, dx, dy in deltas:

        x_data.append([frame, intensity, area])
        
        # Transform for large range+ good sensitivity about origin
        # dx = 127 * np.tanh(dx/np.pi)
        # dy = 127 * np.tanh(dy/np.pi)

        # Transform for increased sensitivity about origin
        dx = dx * 3.0
        dy = dy * 3.0

        # x = int(round(origin[1] + dx))
        # y = int(round(origin[0] + dy))

        dx = int(round(dx))
        dy = int(round(dy))

        # buf = np.zeros(shape)
        # buf[y, x] = large_value

        buf = large_value * np.roll(kernel, (dy,dx), (0,1))

        y_data.append(buf.flatten())

    return np.array(x_data), np.array(y_data)


bags_path = '/local/scratch/kevingordon/cims/data/bags/'
batch_directory = 'Curated/'
data = []
series = '000'
start = time.time()
for file in os.listdir(bags_path + batch_directory):
    if not file.endswith("_tracking.db"):
        continue

    # if not '_tracking_manifoldExp_'+series+'.db' in file:
    #     continue

    bag = DataBag(bags_path + batch_directory + file)
    res = fetch_data(bag)
    data.extend(res)

data = np.array(data)
np.random.shuffle(data)
split = int(0.8 * len(data))
data_training = data[:split]
data_test = data[split:]
print "Dataset loaded", time.time() - start


DV = DeepVelocity()

epochs = 2
batch_size = 256

metrics = DV.deep_velocity.metrics_names
for i in range(epochs):

    # Train
    loss = []
    start = time.time()
    for j in range(0, len(data_training), batch_size):
        data_batch = data_training[j:j+batch_size]
        x_data, y_data = getOutputs(data_batch)                
        loss.append(DV.deep_velocity.train_on_batch(x_data, y_data))

    loss = np.mean(loss, axis=0)
    print "Training loss -  epoch", i+1, " - ", time.time() - start, "s - ", [metrics[k] +': '+ str(loss[k]) for k in range(len(metrics))]

    # Test
    loss = []
    start = time.time()
    for j in range(0, len(data_test), batch_size):
        data_batch = data_test[j:j+batch_size]
        x_data, y_data = getOutputs(data_batch) 
        loss.append(DV.deep_velocity.test_on_batch(x_data, y_data))

    loss = np.mean(loss, axis=0)
    print "Test loss     -  epoch", i+1, " - ", time.time() - start, "s - ", [metrics[k] +': '+ str(loss[k]) for k in range(len(metrics))]

models.save_model(DV.deep_velocity, (os.path.join(DV.path(), "DeepVelocity.h5")))