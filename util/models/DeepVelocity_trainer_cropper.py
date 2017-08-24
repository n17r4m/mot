import os, time
import cv2

from DeepVelocity import DeepVelocity
from ClassyCoder import ClassyCoder
from util.Cropper import Cropper
import matplotlib.pyplot as plt
import numpy as np

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
    res = bag.query('SELECT a1.particle, a1.frame, p.intensity, p.area, a2.x - a1.x, a2.y - a1.y FROM particles p, assoc a1, assoc a2 WHERE a1.frame == a2.frame - 1 AND a1.particle == a2.particle AND p.id == a1.particle ORDER BY a1.frame')
    return np.array(res)

def getOutputs(cropper, classyCoder, deltas):
    large_value = 100000
    shape = (256, 256)
    kernel = gkern(256, 0.8)

    x_data = []
    y_data = []

    # origin = (np.array(shape) - 1) / 2.0

    for particle, frame, intensity, area, dx, dy in deltas:
        if area < 50:
            continue
        buf = cropper.isolate(frame, particle)
        buf = cv2.resize(buf, (cropper.size, cropper.size), interpolation = cv2.INTER_CUBIC)
        buf = buf.astype('float32') / 255.
        buf = buf.reshape((1, 64, 64, 1))
        enc = classyCoder.encoder.predict(buf)
        # pred = classyCoder.featureclassifier.predict(enc)
        # pred /= np.max(pred)
        # print pred.astype(int)
        
        enc = enc.reshape((512,))
        x_data.append(enc)
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
    
    x_data = np.array(x_data)

    return x_data, np.array(y_data)


bags_path = '/local/scratch/kevingordon/cims/data/bags/'
backgrounds_path = '/local/scratch/mot/data/backgrounds/'
videos_path = '/mnt/SIA/'
batch_directory = 'Curated/'
data = []
cropper = None
		
start = time.time()
for file in os.listdir(bags_path + batch_directory):
    if not file.endswith("_tracking.db"):
        continue

    # if not '_tracking_manifoldExp_'+series+'.db' in file:
    #     continue
    name = file.split('.')[-2].split('_')[0]

    bag = DataBag(bags_path + batch_directory + file)
    res = fetch_data(bag)
    data.extend(res)
    video_path = videos_path + batch_directory + name + '.avi'
    print video_path
    background = cv2.imread(backgrounds_path+ 'tmp/T02402_simple.png', 0)

    opts = {'output_dir': 0,
		    'size': 64,
		    'pad': 0,
		    'background': background,
		    'normalize': 1,
		    'verbose': 0}
    
    cropper = Cropper(video_path, bag, opts)
    break

data = np.array(data)
print data.shape
# np.random.shuffle(data)
split = int(0.8 * len(data))
data_training = data[:split]
data_test = data[split:]
print "Dataset loaded", name, time.time() - start


DV = DeepVelocity(input_shape=(512,))
CATEGORIES = 5
CC = ClassyCoder((64, 64, 1), CATEGORIES, False)
CC.load('/local/scratch/mot/util/models/ClassyCoder.h5')
epochs = 10
batch_size = 128

metrics = DV.deep_velocity.metrics_names
for i in range(epochs):

    # Train
    loss = []
    start = time.time()
    for j in range(0, len(data_training), batch_size):
        data_batch = data_training[j:j+batch_size]
        x_data, y_data = getOutputs(cropper, CC, data_batch)
        loss.append(DV.deep_velocity.train_on_batch(x_data, y_data))

    loss = np.mean(loss, axis=0)
    print "Training loss -  epoch", i+1, " - ", time.time() - start, "s - ", [metrics[k] +': '+ str(loss[k]) for k in range(len(metrics))]

    # Test
    loss = []
    start = time.time()
    for j in range(0, len(data_test), batch_size):
        data_batch = data_test[j:j+batch_size]
        x_data, y_data = getOutputs(cropper, CC, data_batch) 
        loss.append(DV.deep_velocity.test_on_batch(x_data, y_data))

    loss = np.mean(loss, axis=0)
    print "Test loss     -  epoch", i+1, " - ", time.time() - start, "s - ", [metrics[k] +': '+ str(loss[k]) for k in range(len(metrics))]

models.save_model(DV.deep_velocity, (os.path.join(DV.path(), "DeepVelocity.h5")))

