import os


from keras import backend as K
from keras import metrics
from keras.models import Model, Sequential
from keras.layers import Input, Flatten, Conv2D, Conv2DTranspose, Dense, MaxPooling2D, UpSampling2D
from keras.layers import Activation, Concatenate, Dropout, AlphaDropout, Reshape, Layer, Lambda

from keras.layers.normalization import BatchNormalization
from keras.layers.advanced_activations import LeakyReLU
from keras.regularizers import l2
from keras.objectives import binary_crossentropy




class ClassyVCoder(object):
    
    def __init__(self, input_shape=(64, 64, 1), num_categories=5, verbose=False):
        """
        https://keras.io/getting-started/functional-api-guide/#multi-input-and-multi-output-models
        https://keras.io/getting-started/functional-api-guide/#shared-layers
        https://blog.keras.io/building-autoencoders-in-keras.html
        https://github.com/fchollet/keras/blob/master/examples/variational_autoencoder_deconv.py
        
        """
        
        
        
        
        # number of filters
        
        # convolution kernel size
        filters = 40
        
        latent_dim = 16
        epsilon_std = 1.0
        noise_std = .01


        img_rows, img_cols, img_chns = input_shape
        input_img = Input(shape=input_shape, name="main_input")
        
        if verbose:
            print "Network input shape is", input_img.get_shape()
        
        
        x = Conv2D(filters, (3, 3), padding='same', activity_regularizer=l2(10e-8))(input_img)
        x = LeakyReLU(alpha=0.05)(x)
        x = BatchNormalization()(x)
        x = MaxPooling2D((2, 2), padding='same')(x)
        x = Conv2D(filters, (3, 3), padding='same', activity_regularizer=l2(10e-8))(x)
        x = LeakyReLU(alpha=0.05)(x)
        x = BatchNormalization()(x)
        x = MaxPooling2D((2, 2), padding='same')(x)
        x = Conv2D(filters, (3, 3), padding='same', activity_regularizer=l2(10e-8))(x)
        x = LeakyReLU(alpha=0.05)(x)
        x = BatchNormalization()(x)
        x = MaxPooling2D((2, 2), padding='same', name="encoded")(x)
        
        
        conv_output_shape = K.int_shape(x)
        
        intermediate_dim = conv_output_shape[1] * conv_output_shape[2] * conv_output_shape[3]
        
        if verbose:
            print "Convolution output shape is", conv_output_shape
        
        x = Flatten()(x)
        
        hidden = Dense(intermediate_dim, activation='selu')(x)
        
        
        z_mean = Dense(latent_dim)(hidden)
        z_log_var = Dense(latent_dim)(hidden)
        
        
        def sampling(args):
            z_mean, z_log_var = args
            x = K.placeholder(shape=(None, latent_dim))
            epsilon = K.random_normal(shape=K.int_shape(x)[1:], mean=0., stddev=noise_std)
            epsilon *= K.exp(.5 * z_log_var)
            epsilon += z_mean
            return epsilon
        z = Lambda(sampling, output_shape=(latent_dim,))([z_mean, z_log_var])  
        
        encoding_shape = K.int_shape(z)
        
        if verbose:
            print "Encoding shape is", encoding_shape, "(", latent_dim, "dimensions )"
        
        
        
        # this model maps an input to its encoded representation
        encoder = Model(input_img, z)
        
        
        
        # next, declare the auto_encoding output side
         
        n = 0; 
        n +=1; ae = Dense(intermediate_dim, activation='selu')(z)
        n +=1; ae = Reshape(conv_output_shape[1:])(ae)
        n +=1; ae = Conv2D(filters, (3, 3), padding='same')(ae)
        n +=1; ae = LeakyReLU(alpha=0.05)(ae)
        n +=1; ae = UpSampling2D((2, 2))(ae)
        n +=1; ae = Conv2D(filters, (3, 3), padding='same')(ae)
        n +=1; ae = LeakyReLU(alpha=0.05)(ae)
        n +=1; ae = UpSampling2D((2, 2))(ae)
        n +=1; ae = Conv2D(filters, (3, 3), padding='same')(ae)
        n +=1; ae = LeakyReLU(alpha=0.05)(ae)
        n +=1; ae = UpSampling2D((2, 2))(ae)
        n +=1; decoded = Conv2D(1, (3, 3), activation='sigmoid', padding='same')(ae)
        
        if verbose:
            print "Decoder output shape is", decoded.get_shape()
        
        # this is a pipe from the input image to the reconstructed output
        autoencoder = Model(input_img, decoded)
        
        
        
        # use right side of architecture encoded input to construct an image
        encoded_input = Input(shape=encoding_shape[1:])
        deco = encoded_input
        for l in range(-n, 0):
            deco = autoencoder.layers[l](deco)
        decoder = Model(encoded_input, deco)
        
        
        
        # and then, the classifier
        n = 0
        n +=1; cl = Dense(64, activation='selu')(z)
        n +=1; cl = AlphaDropout(0.1)(cl)
        #n +=1; cl = Dense(64, activation='selu')(cl)
        #n +=1; cl = AlphaDropout(0.1)(cl)
        n +=1; cl = Dense(64, activation='selu')(cl)
        n +=1; classified = Dense(num_categories, activation='softmax')(cl)
        
        if verbose:
            print "Classifier output shape is", classified.get_shape()
        
        # provide classification on images
        imageclassifier = Model(input_img, classified)
        imageclassifier.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['acc'])
        
        # and classifications on encoded representations
        encoded_input = Input(shape=(encoding_shape[1:]))
        fc = encoded_input
        for l in range(-n, 0):
            fc = imageclassifier.layers[l](fc)
        featureclassifier = Model(encoded_input, fc)
        featureclassifier.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['acc'])
        
        
        # complete model (1 input, 2 outputs)

        def vae_objective(x, x_decoded):
            xent_loss = img_rows * img_cols * metrics.binary_crossentropy(x, x_decoded)
            kl_loss = - 0.5 * K.mean(1 + z_log_var - K.square(z_mean) - K.exp(z_log_var), axis=-1)
            """
            loss = K.sum(binary_crossentropy(x, x_decoded), axis=1)
            kl_regu = -.5 * K.sum(1. + z_log_var - K.square(z_mean) - K.exp(z_log_var), axis=1)
            """
            return xent_loss + kl_loss


        classycoder = Model(inputs=[input_img], outputs=[decoded, classified])
        classycoder.compile(
            optimizer='adam', 
            loss=[vae_objective, 'categorical_crossentropy'],
            loss_weights=[0.66, 0.33],
            metrics=['acc'])
        
        
        
        #helpful to know this
        
        self.encoding_dims = latent_dim
        self.encoding_shape = encoding_shape
        
        # Recieve a image and encode it into its latent space representation
        self.encoder = encoder
        
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
        print "Loading weights", path
        self.classycoder.load_weights(path)

    def path(self):
        return os.path.dirname(os.path.realpath(__file__))