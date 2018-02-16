import os
import config

from scipy.interpolate import interp2d

import tensorflow as tf
import numpy as np


from tensorflow.python.keras import backend as K
from tensorflow.python.keras import metrics
from tensorflow.python.keras.models import Model, Sequential
from tensorflow.python.keras.layers import Activation, concatenate, Dropout, AlphaDropout, Reshape, Layer, Lambda, BatchNormalization, Input, Flatten, Conv2D, Conv2DTranspose, LocallyConnected2D, Dense, MaxPooling2D, AveragePooling2D, UpSampling2D, LeakyReLU
from tensorflow.python.keras.regularizers import l2
from tensorflow.python.keras.optimizers import Adam, Nadam
from tensorflow.python.keras.losses import binary_crossentropy

from lib.models.util.make_parallel import make_parallel


class Classifier(object):
    
    def __init__(self, input_shape=(64, 64, 1), num_categories=5, parallel_mode = False, verbose=False):
        """
        https://keras.io/getting-started/functional-api-guide/#multi-input-and-multi-output-models
        https://keras.io/getting-started/functional-api-guide/#shared-layers
        https://blog.keras.io/building-autoencoders-in-keras.html
        https://github.com/fchollet/keras/blob/master/examples/variational_autoencoder_deconv.py
        NEW: https://keunwoochoi.wordpress.com/2017/10/11/u-net-on-keras-2-0/
        NEW: https://github.com/yihui-he/u-net/blob/master/train.py
        NEW: https://github.com/zizhaozhang/unet-tensorflow-keras/blob/master/model.py
        """
        
        
        self.encoding_dims = latent_dim
        self.encoding_shape = encoding_shape
        
        
        
        # Recieve a image and encode it into its latent space representation
        if parallel_mode: self.encoder = make_parallel(encoder, config.GPUs)
        else: self.encoder = encoder
        
        # reconstructs an image from its encoded representation
        if parallel_mode: self.decoder = make_parallel(decoder, config.GPUs)
        else: self.decoder = decoder
        
        # direct pipe from input_image to its classification
        if parallel_mode: self.imageclassifier = make_parallel(imageclassifier, config.GPUs)
        else: self.imageclassifier = imageclassifier
        
        # direct pipe from encoded representation to classification
        if parallel_mode: self.featureclassifier = make_parallel(featureclassifier, config.GPUs)
        else: self.featureclassifier = featureclassifier
        
        # multiple output model, train this for the rest to work. # todo: make_parallel
        self.classycoder = classycoder
        
    def preproc(self, im):
        im = (im.astype("float32") / 255.0)
        w = im.shape[0]
        cx = w / 2.0
        xs = np.linspace(-0.98, 0.98, w)

        x = np.arctanh(xs)
        x /= np.max(x)
        x = x * cx + cx
        
        f = interp2d(np.arange(w), np.arange(w), im, kind="cubic")
        return f(x, x).reshape(w, w, 1)
        
    def deproc(self, im):
        w = im.shape[0]
        cx = w / 2.0
        
        xs = np.linspace(-2.0, 2.0, w)
        
        x = np.tanh(xs)
        x /= np.max(x)
        x = x * cx + cx
        
        f = interp2d(np.arange(w), np.arange(w), im, kind="cubic")
        return (f(x, x) * 255.0).reshape(w,w).astype("uint8")
        
        
    def save(self, path):
        loc = os.path.join(self.path(), path)
        print("Saving weights to", loc)
        self.classycoder.save_weights(loc)
        return self
    
    def load(self, path = "Classifier.h5"):
        loc = os.path.join(self.path(), path)
        print("Loading weights", loc)
        self.classycoder.load_weights(loc)
        return self

    def path(self):
        return os.path.dirname(os.path.realpath(__file__))
