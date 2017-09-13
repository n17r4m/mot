import os

from keras.models import Model
from keras.layers import Input, Dense 
from keras.layers.normalization import BatchNormalization
from keras.layers.convolutional import Conv2D
from keras.layers import activations, concatenate, add
from keras.layers.core import RepeatVector, Reshape, Flatten
from keras.optimizers import Nadam
class DeepVelocity(object):
    
    def __init__(self, input_shape=(18,), verbose=False):
        """
        https://keras.io/getting-started/functional-api-guide/#multi-input-and-multi-output-models
        https://keras.io/getting-started/functional-api-guide/#shared-layers
        https://blog.keras.io/building-autoencoders-in-keras.html        
        """
        input_features = Input(shape=input_shape, name='main_input')
        
        if verbose:
            print "Network input shape is", input_features.get_shape()

        x = Dense(64, activation='selu')(input_features)
        x = Dense(128, activation='selu')(x)
        x = Dense(256, activation='selu')(x)
        output_map = Dense(2,activation='softmax')(x)

        output_map_shape = output_map.get_shape()
        output_map_dims = int(output_map_shape[1])
        
        if verbose:
            print "Output map shape is", output_map_shape, "(", output_map_dims, "dimensions )"


        # complete model (1 input, 2 outputs)
        deep_velocity = Model(inputs=[input_features], outputs=[output_map])
        deep_velocity.compile(
            optimizer='adam', 
            loss=['binary_crossentropy'],
            metrics=['mae', 'acc'])    
        print 'binary!!'
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
    
    def __init__(self, structured_input_shape=(18,), screen_input_shape=(64,64,2), verbose=False):
        """
        https://keras.io/getting-started/functional-api-guide/#multi-input-and-multi-output-models
        https://keras.io/getting-started/functional-api-guide/#shared-layers
        https://blog.keras.io/building-autoencoders-in-keras.html        
        """
        structured_input = Input(shape=structured_input_shape, name='structured_input')
        screen_input = Input(shape=screen_input_shape, name='screen_input')
        n_features = int(structured_input.get_shape()[1])
        
        if verbose:
            print "Network structured input shape is", structured_input.get_shape()
            print "Network screen input shape is", screen_input.get_shape()
            print "Structured input features", n_features

        structured_output = structured_input
        
        x = Flatten()(screen_input)
        screen_output = Dense(64, activation='selu')(x)
        
        x = concatenate([structured_output, screen_output])
        x = Dense(128, activation='selu')(x)
        x = Dense(256, activation='selu')(x)
        print 'dense', x.get_shape()
        main_output = Dense(2,activation='softmax')(x)

        main_output_shape = main_output.get_shape()
        main_output_dims = int(main_output_shape[1])
        
        if verbose:
            print "Output map shape is", main_output_shape, "(", main_output_dims, "dimensions )"


        optimizer = Nadam(lr=0.002, beta_1=0.9, beta_2=0.999, epsilon=1e-08, schedule_decay=0.004)
        # complete model (1 input, 2 outputs)
        # deep_velocity = Model(inputs=[structured_input], outputs=[main_output])
        deep_velocity = Model(inputs=[structured_input, screen_input], outputs=[main_output])
        deep_velocity.compile(
            optimizer=optimizer, 
            loss=['squared_hinge'],
            metrics=['poisson', 'acc'])
        print 'poisson!!'
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