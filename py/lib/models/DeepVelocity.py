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
from keras.layers import RepeatVector
from keras.layers import Reshape
from keras.layers import MaxPooling2D
from keras.layers.core import Flatten
from keras.optimizers import Nadam
from keras.optimizers import SGD
from keras.layers.advanced_activations import LeakyReLU
from keras import backend as K

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
        
        # Broadcast the structured information along
        # channel dimension.
        x = RepeatVector(screen_input_shape[0]*screen_input_shape[1])(structured_input)
        newShape = tuple(list(screen_input_shape)+list(structured_input_shape))
        x = Reshape(newShape)(x)
        newShape = tuple(list(screen_input_shape)+[1])
        y = Reshape(newShape)(screen_input)
        x = concatenate([y, x])
        
        x = Conv2D(16, (5,5))(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = Conv2D(32, (3,3))(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = MaxPooling2D(2)(x)
        x = Conv2D(32, (3,3))(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = Conv2D(32, (3,3))(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = MaxPooling2D(2)(x)
        x = Flatten()(x)

        x = concatenate([x, lat_input])
        x = Dense(256)(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = Dense(128)(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = BatchNormalization()(x)
        x = Dense(64)(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = Dense(32)(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        state_output = Dense(16)(x)
        
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
        x = Dense(128)(prob_input)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = Dense(64)(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = BatchNormalization()(x)
        x = Dense(32)(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        prob_output = Dense(2, activation='softmax', name="probOutput")(x)
        

            
        self.probabilityNetwork = Model(inputs=eng_state_a+eng_state_b, outputs=[prob_output])
    
    def compile(self):
        optimizer = Nadam(lr=self.lr, beta_1=0.9, beta_2=0.999, epsilon=1e-08, schedule_decay=0.004)
        # optimizer = SGD()
        self.probabilityNetwork.compile(
            optimizer=optimizer, 
            loss='contrastive_loss',
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
    

        
def contrastive_loss(y_true, y_pred):
    '''Contrastive loss from Hadsell-et-al.'06
    http://yann.lecun.com/exdb/publis/pdf/hadsell-chopra-lecun-06.pdf
    '''
    margin = 1
    return K.mean(y_true * K.square(y_pred) + (1 - y_true) * K.square(K.maximum(margin - y_pred, 0)))
    
from keras.utils.generic_utils import get_custom_objects

get_custom_objects().update({"contrastive_loss": contrastive_loss})