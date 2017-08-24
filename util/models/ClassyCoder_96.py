import os

from keras.models import Model, Sequential
from keras.layers import Input, Activation, Flatten, Conv2D, Dense, MaxPooling2D, UpSampling2D, Concatenate, Dropout, AlphaDropout
from keras.layers.normalization import BatchNormalization
from keras.layers.advanced_activations import LeakyReLU
from keras.regularizers import l2




class ClassyCoder(object):
    
    def __init__(self, input_shape=(64, 64, 1), num_categories=5 , verbose=False):
        """
        https://keras.io/getting-started/functional-api-guide/#multi-input-and-multi-output-models
        https://keras.io/getting-started/functional-api-guide/#shared-layers
        https://blog.keras.io/building-autoencoders-in-keras.html
        
        
        """
        
        input_img = Input(shape=input_shape, name="main_input")
        self.verbose = verbose
        
        if self.verbose:
            print "Network input shape is", input_img.get_shape()
        
        x = Conv2D(32, (3, 3), padding='same', activity_regularizer=l2(10e-8))(input_img)
        x = LeakyReLU(alpha=0.05)(x)
        x = BatchNormalization()(x)
        x = MaxPooling2D((2, 2), padding='same')(x)
        x = Conv2D(16, (3, 3), padding='same', activity_regularizer=l2(10e-8))(x)
        x = LeakyReLU(alpha=0.05)(x)
        x = BatchNormalization()(x)
        x = MaxPooling2D((2, 2), padding='same')(x)
        x = Conv2D(8, (3, 3), padding='same', activity_regularizer=l2(10e-8))(x)
        x = LeakyReLU(alpha=0.05)(x)
        x = BatchNormalization()(x)
        encoded = MaxPooling2D((2, 2), padding='same', name="encoded")(x)
        
        
        
        encoding_shape = encoded.get_shape()
        encoding_dims = int(encoding_shape[1] * encoding_shape[2] * encoding_shape[3])
        
        if self.verbose:
            print "Encoding shape is", encoding_shape, "(", encoding_dims, "dimensions )"
        
        
        # at this point the representation is (n, n, 8) i.e. (n*n*8)-dimensional
        # this model maps an input to its encoded representation
        encoder = Model(input_img, encoded)
        
        # next, declare the auto_encoding output side
         
        n = 0;
        n +=1; ae = Conv2D(8, (3, 3), padding='same')(encoded)
        n +=1; ae = LeakyReLU(alpha=0.05)(ae)
        n +=1; ae = UpSampling2D((2, 2))(ae)
        n +=1; ae = Conv2D(16, (3, 3), padding='same')(ae)
        n +=1; ae = LeakyReLU(alpha=0.05)(ae)
        n +=1; ae = UpSampling2D((2, 2))(ae)
        n +=1; ae = Conv2D(32, (3, 3), padding='same')(ae)
        n +=1; ae = LeakyReLU(alpha=0.05)(ae)
        n +=1; ae = UpSampling2D((2, 2))(ae)
        n +=1; decoded = Conv2D(1, (3, 3), activation='sigmoid', padding='same')(ae)
        
        if self.verbose:
            print "Decoder output shape is", decoded.get_shape()
        
        autoencoder = Model(input_img, decoded)
        autoencoder.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        # use right side of architecture encoded input to construct an image
        encoded_input = Input(shape=(int(encoding_shape[1]),int(encoding_shape[2]),int(encoding_shape[3])))
        
        deco = encoded_input
        for l in range(-n, 0):
            deco = autoencoder.layers[l](deco)
        
        decoder = Model(encoded_input, deco)
        
        
        # and then, the classifier
        n = 0
        n +=1; cl = Flatten()(encoded)
        n +=1; cl = Dense(encoding_dims, activation='selu')(cl)
        n +=1; cl = AlphaDropout(0.1)(cl)
        n +=1; cl = Dense(512, activation='selu')(cl)
        n +=1; cl = AlphaDropout(0.1)(cl)
        n +=1; cl = Dense(256, activation='selu')(cl)
        n +=1; cl = AlphaDropout(0.1)(cl)
        n +=1; cl = Dense(128, activation='selu')(cl)
        n +=1; classified = Dense(num_categories, activation='softmax')(cl)
        
        if self.verbose:
            print "Classifier output shape is", classified.get_shape()
        
        # provide classification on images
        imageclassifier = Model(input_img, classified)
        imageclassifier.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['mae'] )
        
        # and classifications of encoded representations
        fc = encoded_input
        for l in range(-n, 0):
            fc = imageclassifier.layers[l](fc)
        
        featureclassifier = Model(encoded_input, fc)
        featureclassifier.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['acc'])
        
        
        # complete model (1 input, 2 outputs)
        classycoder = Model(inputs=[input_img], outputs=[decoded, classified])
        classycoder.compile(
            optimizer='adam', 
            loss=['mse', 'categorical_crossentropy'],
            loss_weights=[0.618, 0.618],
            metrics=['mae', 'acc'])
        
        
        
        #helpful to know this
        self.encoding_dims = encoding_dims
        self.encoding_shape = encoding_shape
        
        # Recieve a image and encode it into its latent space representation
        self.encoder = encoder
        
        # direct pipe from input_image to its reconstruction
        self.autoencoder = autoencoder
        
        # reconstructs an image from its encoded representation
        self.decoder = decoder
        
        # direct pipe from input_image to its classification
        self.imageclassifier = imageclassifier
        
        # direct pipe from encoded representation to classification
        self.featureclassifier = featureclassifier
        
        # multiple output model, train this for the rest to work.
        self.classycoder = classycoder
        
    def save(self, path):
        self.classycoder.save_weights(path)
    
    def load(self, path):
        if self.verbose:
            print "Loading weights", path
        self.classycoder.load_weights(path)

    def path(self):
        return os.path.dirname(os.path.realpath(__file__))