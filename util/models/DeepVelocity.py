import os

from keras.models import Model
from keras.layers import Input, Dense, Activation
from keras.layers.normalization import BatchNormalization
from keras.layers.convolutional import Conv2D
from keras.layers import concatenate
from keras.layers.core import Flatten
from keras.optimizers import Nadam
from keras.layers.advanced_activations import LeakyReLU

class DeepVelocity(object):
    
    def __init__(self, input_shape=(18,), verbose=False):
        """
        https://keras.io/getting-started/functional-api-guide/#multi-input-and-multi-output-models
        https://keras.io/getting-started/functional-api-guide/#shared-layers
        https://blog.keras.io/building-autoencoders-in-keras.html        
        """
        input_features = Input(shape=input_shape, name='main_input')
        
        if verbose:
            print("Network input shape is", input_features.get_shape())

        x = Dense(64, activation='selu')(input_features)
        x = Dense(128, activation='selu')(x)
        x = Dense(256, activation='selu')(x)
        output_map = Dense(2,activation='softmax')(x)

        output_map_shape = output_map.get_shape()
        output_map_dims = int(output_map_shape[1])
        
        if verbose:
            print("Output map shape is", output_map_shape, "(", output_map_dims, "dimensions )")


        # complete model (1 input, 2 outputs)
        deep_velocity = Model(inputs=[input_features], outputs=[output_map])
        deep_velocity.compile(
            optimizer='adam', 
            loss=['binary_cross_entropy'],
            metrics=['mae', 'acc'])    
        print('binary!!')
        #helpful to know this
        self.output_map_dims = output_map_dims
        self.output_map_shape = output_map_shape        
        
        # multiple output model, train this for the rest to work.
        self.deep_velocity = deep_velocity

    def save(self, path):
        self.deep_velocity.save_weights(path)
    
    def load(self, path):
        self.deep_velocity.load_weights(path)

    def path(self):
        return os.path.dirname(os.path.realpath(__file__))
        
# Will also use two video frames to help determine entrained fluid flow
class DeepVelocityV2(object):
    
    def __init__(self, lr=0.005, structured_input_shape=(68,), screen_input_shape=(64,64,2), verbose=False):
        """
        https://keras.io/getting-started/functional-api-guide/#multi-input-and-multi-output-models
        https://keras.io/getting-started/functional-api-guide/#shared-layers
        https://blog.keras.io/building-autoencoders-in-keras.html        
        """
        structured_input = Input(shape=structured_input_shape, name='structured_input')
        screen_input = Input(shape=screen_input_shape, name='screen_input')
        n_features = int(structured_input.get_shape()[1])
        
        if verbose:
            print("Network structured input shape is", structured_input.get_shape())
            print("Network screen input shape is", screen_input.get_shape())
            print("Structured input features", n_features)

        x = Dense(32)(structured_input)
        structured_output = Activation('selu')(x)
        
        x = Flatten()(screen_input)
        x = Dense(32)(x)
        x = BatchNormalization()(x)
        x = Activation('selu')(x)
        x = BatchNormalization()(x)
        x = Dense(64)(x)
        x = BatchNormalization()(x)
        screen_output = Activation('selu')(x)

        x = concatenate([structured_output, screen_output])
        x = Dense(128)(x)
        x = BatchNormalization()(x)
        x = Activation('selu')(x)
        
        x = Dense(256)(x)
        x = BatchNormalization()(x)
        x = Activation('selu')(x)
        main_output = Dense(2, activation='softmax')(x)

        main_output_shape = main_output.get_shape()
        main_output_dims = int(main_output_shape[1])
        
        if verbose:
            print("Output map shape is", main_output_shape, "(", main_output_dims, "dimensions )")


        optimizer = Nadam(lr=lr, beta_1=0.9, beta_2=0.999, epsilon=1e-08, schedule_decay=0.004)
        # complete model (1 input, 2 outputs)
        # deep_velocity = Model(inputs=[structured_input], outputs=[main_output])
        deep_velocity = Model(inputs=[structured_input, screen_input], outputs=[main_output])
        deep_velocity.compile(
            optimizer=optimizer, 
            loss=['mse'],
            metrics=['acc', 'mse'])
        print('mse!!')
        #helpful to know this
        self.main_output_dims = main_output_dims
        self.main_output_shape = main_output_shape        
        
        # multiple output model, train this for the rest to work.
        self.deep_velocity = deep_velocity

    def save(self, path):
        self.deep_velocity.save_weights(path)
    
    def load(self, path):
        self.deep_velocity.load_weights(path)

    def path(self):
        return os.path.dirname(os.path.realpath(__file__))
        
# architecture now takes two states (time t, t+1), encodes them, and 
# computes their probability of matching
class DeepVelocityV3(object):
    
    def __init__(self, lr=0.005, lat_input_shape=(64,), screen_input_shape=(64,64,), structured_input_shape=(2,), verbose=False):
        """
        https://keras.io/getting-started/functional-api-guide/#multi-input-and-multi-output-models
        https://keras.io/getting-started/functional-api-guide/#shared-layers
        https://blog.keras.io/building-autoencoders-in-keras.html        
        """
        structured_input = Input(shape=structured_input_shape, name='structured input')
        lat_input = Input(shape=lat_input_shape, name='latent vector input')
        screen_input = Input(shape=screen_input_shape, name='screen input')
        
        if verbose:
            print("Network structured input shape is", structured_input.get_shape())
            print("Network screen input shape is", screen_input.get_shape())
            print("Network latent input shape is", lat_input.get_shape())

        # Let's unify the inputs
        screen_ouput = Flatten()(screen_input)
        structured_output = structured_input
        lat_output = lat_input
        
        # Create the state encoding network
        x = concatenate([screen_output, lat_output, structured_output])
        x = Dense(32)(x)
        x = BatchNormalization()(x)
        x = Activation('selu')(x)
        x = Dense(64)(x)
        x = BatchNormalization()(x)
        x = Activation('selu')(x)
        x = BatchNormalization()(x)
        x = Dense(128)(x)
        x = BatchNormalization()(x)
        x = Activation('selu')(x)
        x = Dense(256)(x)
        x = BatchNormalization()(x)
        x = Activation('selu')(x)
        state_output = Dense(8)(x)
        
        state_network = Model(inputs=[structured_input, lat_input, screen_input], outputs=[state_output])
        
        # Create the probability network
        prob_input = concatenate([state_output, state_output])
        x = Dense(32)(x)
        x = BatchNormalization()(x)
        x = Activation('selu')(x)
        x = Dense(64)(x)
        x = BatchNormalization()(x)
        x = Activation('selu')(x)
        x = BatchNormalization()(x)
        x = Dense(128)(x)
        x = BatchNormalization()(x)
        x = Activation('selu')(x)
        prob_output = Dense(2, activation='softmax')(x)

        prob_network = Model(inputs=[structured_input, lat_input, screen_input], outputs=[prob_output])
        
        # Compile the model
        optimizer = Nadam(lr=lr, beta_1=0.9, beta_2=0.999, epsilon=1e-08, schedule_decay=0.004)
        prob_network.compile(
            optimizer=optimizer, 
            loss=['mse'],
            metrics=['acc', 'poisson'])
        print('mse!!')

        self.prob_network = prob_network

    def save(self, path):
        self.prob_network.save_weights(path)
    
    def load(self, path):
        self.prob_network.load_weights(path)

    def path(self):
        return os.path.dirname(os.path.realpath(__file__))