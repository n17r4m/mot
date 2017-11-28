"""
A model that was initially meant to learn motion probabilities
using input features, the model now learns the probabilities of
two states belonging to eachother.

"""

import os

from keras.models import Model, load_model
from keras.layers import Input, Dense, Activation
from keras.layers.normalization import BatchNormalization
from keras.layers.convolutional import Conv2D
from keras.layers import concatenate
from keras.layers.core import Flatten
from keras.optimizers import Nadam
from keras.layers.advanced_activations import LeakyReLU

# architecture now takes two states (time t, t+1), encodes them, and 
# computes their probability of matching
class DeepVelocity(object):
    
    def __init__(self, lr=0.002, lat_input_shape=(64,), screen_input_shape=(64,64,), structured_input_shape=(2,), verbose=False):
        """
        https://keras.io/getting-started/functional-api-guide/#multi-input-and-multi-output-models
        https://keras.io/getting-started/functional-api-guide/#shared-layers
        https://blog.keras.io/building-autoencoders-in-keras.html        
        """
        self.lr = lr
        structured_input = Input(shape=structured_input_shape, name='structured_input')
        lat_input = Input(shape=lat_input_shape, name='latent_vector_input')
        screen_input = Input(shape=screen_input_shape, name='screen_input')
        eng_state = [structured_input, lat_input, screen_input]
        
        if verbose:
            print("Network structured input shape is", structured_input.get_shape())
            print("Network screen input shape is", screen_input.get_shape())
            print("Network latent input shape is", lat_input.get_shape())

        # Let's unify the inputs
        screen_output = Flatten()(screen_input)
        structured_output = structured_input
        lat_output = lat_input
        
        # Create the state encoding network
        x = concatenate([screen_output, lat_output, structured_output])
        x = Dense(32)(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = Dense(64)(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = BatchNormalization()(x)
        x = Dense(128)(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = Dense(256)(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        state_output = Dense(8)(x)
        
        state_network = Model(inputs=eng_state, outputs=[state_output])
        
        # Create the two state encoding legs
        structured_input_a = Input(shape=structured_input_shape, name='structured_input_a')
        lat_input_a = Input(shape=lat_input_shape, name='latent_vector_input_a')
        screen_input_a = Input(shape=screen_input_shape, name='screen_input_a')
        eng_state_a = [structured_input_a, lat_input_a, screen_input_a]
        
        structured_input_b = Input(shape=structured_input_shape, name='structured_input_b')
        lat_input_b = Input(shape=lat_input_shape, name='latent_vector_input_b')
        screen_input_b = Input(shape=screen_input_shape, name='screen_input_b')
        eng_state_b = [structured_input_b, lat_input_b, screen_input_b]

        enc_state_a = state_network(eng_state_a)
        enc_state_b = state_network(eng_state_b)
        
        # Create the probability network
        prob_input = concatenate([enc_state_a, enc_state_b])
        x = Dense(32)(prob_input)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = Dense(64)(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = BatchNormalization()(x)
        x = Dense(128)(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        prob_output = Dense(2, activation='softmax')(x)
        

            
        self.probabilityNetwork = Model(inputs=eng_state_a+eng_state_b, outputs=[prob_output])
        
        optimizer = Nadam(lr=self.lr, beta_1=0.9, beta_2=0.999, epsilon=1e-08, schedule_decay=0.004)
        
        self.probabilityNetwork.compile(
            optimizer=optimizer, 
            loss=['mse'],
            metrics=['acc', 'mse'])  
        
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