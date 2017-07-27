import os

from keras.models import Model
from keras.layers import Input, Dense   
from keras.layers.normalization import BatchNormalization
from keras.layers import activations

class DeepVelocity(object):
    
    def __init__(self, input_shape=(3,), verbose=False):
        """
        https://keras.io/getting-started/functional-api-guide/#multi-input-and-multi-output-models
        https://keras.io/getting-started/functional-api-guide/#shared-layers
        https://blog.keras.io/building-autoencoders-in-keras.html        
        """
        input_features = Input(shape=input_shape, name='main_input')
        
        if verbose:
            print "Network input shape is", input_features.get_shape()

        x = Dense(128, activation='selu')(input_features)
        x = Dense(256, activation='selu')(x)
        x = Dense(512, activation='selu')(x)
        output_map = Dense(65536)(x)

        output_map_shape = output_map.get_shape()
        output_map_dims = int(output_map_shape[1])
        
        if verbose:
            print "Output map shape is", output_map_shape, "(", output_map_dims, "dimensions )"


        # complete model (1 input, 2 outputs)
        deep_velocity = Model(inputs=[input_features], outputs=[output_map])
        deep_velocity.compile(
            optimizer='adam', 
            loss=['mse'],            
            metrics=['mae', 'acc'])    
        
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