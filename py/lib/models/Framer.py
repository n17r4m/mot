import os
import config

from scipy.interpolate import interp2d

import tensorflow as tf
import numpy as np


from tensorflow.python.keras import backend as K
from tensorflow.python.keras import metrics
from tensorflow.python.keras.models import Model, Sequential
from tensorflow.python.keras.layers import Activation, Concatenate, Dropout, AlphaDropout, Reshape, Layer, Lambda, BatchNormalization, Input, Flatten, Conv2D, Conv2DTranspose, LocallyConnected2D, Dense, MaxPooling2D, AveragePooling2D, UpSampling2D, LeakyReLU
from tensorflow.python.keras.regularizers import l2
from tensorflow.python.keras.optimizers import Adam, Nadam
from tensorflow.python.keras.losses import binary_crossentropy

from lib.models.util.make_parallel import make_parallel


class Framer(object):
    
    def __init__(self, input_shape=(778, 576, 1), num_categories=5, parallel_mode = False, verbose=False):
        """
        https://keras.io/getting-started/functional-api-guide/#multi-input-and-multi-output-models
        https://keras.io/getting-started/functional-api-guide/#shared-layers
        https://blog.keras.io/building-autoencoders-in-keras.html
        https://github.com/fchollet/keras/blob/master/examples/variational_autoencoder_deconv.py
        
        """
        
        
        self.num_categories = num_categories
        
        filters = 128


        img_rows, img_cols, img_chns = input_shape
        input_img = Input(shape=input_shape, name="main_input")
        
        if verbose:
            print("Network input shape is", input_img.get_shape())
        
        
        x = Conv2D(filters, (3, 3), padding='same', activity_regularizer=l2(10e-8))(input_img)
        x = BatchNormalization()(x)
        x = LeakyReLU(alpha=0.05)(x)
        
        x = Conv2D(filters, (3, 3), padding='same', activity_regularizer=l2(10e-8))(x)
        x = BatchNormalization()(x)
        x = LeakyReLU(alpha=0.05)(x)
        
        x = Conv2D(filters, (3, 3), padding='same', activity_regularizer=l2(10e-8))(x)
        x = BatchNormalization()(x)
        x = LeakyReLU(alpha=0.05)(x)
        
        
        self.framer = Model(input_img, x)
        optimizer = Nadam(lr=0.0002, beta_1=0.9, beta_2=0.999, epsilon=1e-08, schedule_decay=0.004, clipnorm=0.618)
        
        self.framer.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['acc'])
    
            
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
