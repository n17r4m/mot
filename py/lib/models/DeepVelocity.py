"""
A model that was initially meant to learn motion probabilities
using input features, the model now learns the probabilities of
two states belonging to eachother.

"""

import os
# import numpy as np

from tensorflow.python.keras.models import Model, load_model
from tensorflow.python.keras.layers import Input, Dense, Activation
from tensorflow.python.keras.layers import BatchNormalization
from tensorflow.python.keras.layers import Conv2D
from tensorflow.python.keras.layers import concatenate
from tensorflow.python.keras.layers import RepeatVector
from tensorflow.python.keras.layers import Reshape
from tensorflow.python.keras.layers import MaxPooling2D
from tensorflow.python.keras.layers import AveragePooling2D
from tensorflow.python.keras.layers import LeakyReLU
from tensorflow.python.keras.layers import Flatten
from tensorflow.python.keras.optimizers import Nadam
from tensorflow.python.keras.optimizers import SGD
from tensorflow.python.keras import backend as K

from lib.models.util.make_parallel import make_parallel

# architecture now takes two states (time t, t+1), encodes them, and 
# computes their probability of matching
class DeepVelocity(object):
    
    def __init__(self, lr=0.00017654, lat_input_shape=(64,), screen_input_shape=(64,64,), structured_input_shape=(2,), verbose=False):
        """
        https://keras.io/getting-started/functional-api-guide/#multi-input-and-multi-output-models
        https://keras.io/gett ing-started/functional-api-guide/#shared-layers
        https://blog.keras.io/building-autoencoders-in-keras.html        
        """
        # Gross hack, change later?
        self.lr = lr

        if verbose:
            print("Network structured input shape is", structured_input.get_shape())
            print("Network screen input shape is", screen_input.get_shape())
            print("Network latent input shape is", lat_input.get_shape())
        
        # Create the two state encoding legs
        structured_input_a = Input(shape=structured_input_shape)
        lat_input_a = Input(shape=lat_input_shape)
        screen_input_a = Input(shape=screen_input_shape,)
        
        structured_input_b = Input(shape=structured_input_shape)
        lat_input_b = Input(shape=lat_input_shape)
        screen_input_b = Input(shape=screen_input_shape)
        
        eng_state_a = [structured_input_a, lat_input_a, screen_input_a]
        eng_state_b = [structured_input_b, lat_input_b, screen_input_b]     
        
        # We want to broadcast the structured input (x, y) into their own
        # channels, each with the same dimension as the screen input
        # We can then concatenate, then convolve over the whole tensor
        x = RepeatVector(64*64)(structured_input_a)
        x = Reshape((64,64,2))(x)
        structured_output_a = x
        
        x = RepeatVector(64*64)(structured_input_b)
        x = Reshape((64,64,2))(x)
        structured_output_b = x
        
        # Similar with the latent vector, except it will simply be repeated
        # column wise
        x = RepeatVector(64)(lat_input_a)
        x = Reshape((64,64,1))(x)
        lat_output_a = x
        
        x = RepeatVector(64)(lat_input_b)
        x = Reshape((64,64,1))(x)
        lat_output_b = x
        
        # The screen is the correct shape, just add a channel dimension
        x = Reshape((64,64,1))(screen_input_a)
        screen_output_a = x
        
        x = Reshape((64,64,1))(screen_input_b)
        screen_output_b= x
        
        x = concatenate([screen_output_a, structured_output_a, lat_output_a, screen_output_b, structured_output_b, lat_output_b], axis=-1)
        print("Hello, World!", x.shape)
        x = Conv2D(16, (3,3))(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        print("1", x.shape)
        
        x = Conv2D(32, (3,3))(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = MaxPooling2D(2)(x)
        print("2", x.shape)
        
        x = Conv2D(64, (3,3))(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        print("3", x.shape)
        
        x = Conv2D(128, (3,3))(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = MaxPooling2D(2)(x)
        print("4", x.shape)
        
        x = Conv2D(256, (3,3))(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        print("5", x.shape)

        x = Conv2D(512, (3,3))(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = MaxPooling2D(2)(x)
        print("6", x.shape)
        
        x = Conv2D(1024, (3,3))(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        print("7", x.shape)
        
        x = Conv2D(2, (1,1))(x)
        x = Activation('linear')(x)
        x = AveragePooling2D()(x)
        print("8", x.shape)
        
        x = Activation("softmax")(x)
        print("9", x.shape)
        
        prob_output = Reshape((2,))(x)
        print("10", prob_output.shape)
    
        self.probabilityNetwork = Model(inputs=eng_state_a+eng_state_b, outputs=[prob_output])
    
    def compile(self):
        # print("LR: ",self.lr)
        # self.lr = 10**np.random.uniform(-2.2, -3.8)
        optimizer = Nadam(lr=self.lr, beta_1=0.9, beta_2=0.999, epsilon=1e-08, schedule_decay=0.004)
        # optimizer = SGD()
        # self.probabilityNetwork = make_parallel(self.probabilityNetwork, 2)
        self.probabilityNetwork.compile(
            optimizer=optimizer, 
            loss='categorical_crossentropy',
            metrics=['acc', 'mse', 'categorical_crossentropy'])
        
    def save_weights(self, path):
        self.probabilityNetwork.save_weights(path)
    
    def load(self, path):
        loc = os.path.join(self.path(), path)
        print("Loading weights", loc)
        self.probabilityNetwork.load_weights(loc)
        return self

    def save_model(self, path):
        self.probabilityNetwork.save(path)
        
    def load_model(self, path):
        # loc = os.path.join(self.path(), path)
        # print("Loading model", path)
        self.probabilityNetwork = load_model(path)
        return self

    def path(self):
        return os.path.dirname(os.path.realpath(__file__))
    

        
def contrastive_loss(y_true, y_pred):
    '''Contrastive loss from Hadsell-et-al.'06
    http://yann.lecun.com/exdb/publis/pdf/hadsell-chopra-lecun-06.pdf
    '''
    margin = 1
    return K.mean(y_true * K.square(y_pred) + (1 - y_true) * K.square(K.maximum(margin - y_pred, 0)))
    
from tensorflow.python.keras.utils import get_custom_objects

get_custom_objects().update({"contrastive_loss": contrastive_loss})