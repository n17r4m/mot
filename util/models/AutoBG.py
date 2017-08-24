#Doesn't work

import os

from keras.models import Model, Sequential
from keras.layers import Input, Activation, Flatten, Conv2D, Dense, MaxPooling2D, UpSampling2D, Concatenate, Dropout, AlphaDropout, Reshape
from keras.layers.normalization import BatchNormalization
from keras.layers.advanced_activations import LeakyReLU
from keras.regularizers import l2




class AutoBG(object):
    
    def __init__(self, input_shape=(2336, 1729, 1), verbose=False):
        """
        https://keras.io/getting-started/functional-api-guide/#multi-input-and-multi-output-models
        https://keras.io/getting-started/functional-api-guide/#shared-layers
        https://blog.keras.io/building-autoencoders-in-keras.html
        
        
        """
        
        input_img = Input(shape=input_shape, name="main_input")
        self.verbose = verbose
        
        if self.verbose:
            print "Network input shape is", input_img.get_shape()
        
        x = Flatten()(input_img)
        #x = Dense(1, activation="selu")(x)
        x = Dense(input_shape[0] * input_shape[1] * input_shape[2], activation="sigmoid")(x)
        x = Reshape(input_shape)(x)
        
        
        model = Model(inputs=input_img, outputs=x)
        model.compile(
            optimizer='adam', 
            loss='binary_crossentropy')
        
        
        
        # multiple output model, train this for the rest to work.
        self.model = model
        
    def save(self, path):
        self.model.save_weights(path)
    
    def load(self, path):
        if self.verbose:
            print "Loading weights", path
        self.model.load_weights(path)

    def path(self):
        return os.path.dirname(os.path.realpath(__file__))