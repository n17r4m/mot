
from keras.models import Model, Sequential
from keras.layers import Input, Activation, Flatten, Conv2D, Dense, MaxPooling2D, UpSampling2D, Concatenate, Dropout

class ClassyCoder:
    
    
    
    def __init__(self, input_shape=(256, 256, 1), num_categories=3 , verbose=False):
        """
        https://keras.io/getting-started/functional-api-guide/#multi-input-and-multi-output-models
        https://keras.io/getting-started/functional-api-guide/#shared-layers
        https://blog.keras.io/building-autoencoders-in-keras.html
        
        
        """
        
        input_img = Input(shape=input_shape, name="main_input")
        
        if verbose:
            print "Network input shape is", input_img.get_shape()
                
        x = Conv2D(16, (3, 3), activation='relu', padding='same')(input_img)
        print x.get_shape()
        x = MaxPooling2D((2, 2), padding='same')(x)
        print x.get_shape()
        x = Conv2D(8, (3, 3), activation='relu', padding='same')(x)
        print x.get_shape()
        x = MaxPooling2D((2, 2), padding='same')(x)
        print x.get_shape()
        x = Conv2D(8, (3, 3), activation='relu', padding='same')(x)
        print x.get_shape()
        encoded = MaxPooling2D((2, 2), padding='same', name="encoded")(x)
        
        
        
        encoding_shape = encoded.get_shape()
        encoding_dims = int(encoding_shape[1] * encoding_shape[2] * encoding_shape[3])
        
        if verbose:
            print "Encoding shape is", encoding_shape, "(", encoding_dims, "dimensions )"
        
        
        # at this point the representation is (n, n, 8) i.e. (n*n*8)-dimensional
        # this model maps an input to its encoded representation
        encoder = Model(input_img, encoded)
        
        # next, declare the auto_encoding output side
         
        n = 0;
        n +=1; ae = Conv2D(8, (3, 3), activation='relu', padding='same')(encoded)
        print ae.get_shape()
        n +=1; ae = UpSampling2D((2, 2))(ae)
        print ae.get_shape()
        n +=1; ae = Conv2D(8, (3, 3), activation='relu', padding='same')(ae)
        print ae.get_shape()
        n +=1; ae = UpSampling2D((2, 2))(ae)
        print ae.get_shape()
        n +=1; ae = Conv2D(16, (3, 3), activation='relu', padding='same')(ae)
        print ae.get_shape()
        n +=1; ae = UpSampling2D((2, 2))(ae)
        print ae.get_shape()
        n +=1; decoded = Conv2D(1, (3, 3), activation='sigmoid', padding='same')(ae)
        
        if verbose:
            print "Decoder output shape is", decoded.get_shape()
        
        autoencoder = Model(input_img, decoded)
        autoencoder.compile(optimizer='adadelta', loss='mean_squared_error', metrics=['mae'])
        
        # use right side of architecture encoded input to construct an image
        encoded_input = Input(shape=(int(encoding_shape[1]),int(encoding_shape[2]),int(encoding_shape[3])))
        
        deco = encoded_input
        for l in range(-n, 0):
            deco = autoencoder.layers[l](deco)
        
        decoder = Model(encoded_input, deco)
        
        
        # and then, the classifier
        n = 0
        n +=1; cl = Flatten()(encoded)
        n +=1; cl = Dense(encoding_dims, activation='relu')(cl)
        n +=1; cl = Dropout(0.3)(cl)
        n +=1; cl = Dense(64, activation='relu')(cl)
        n +=1; classified = Dense(num_categories, activation='softmax')(cl)
        
        if verbose:
            print "Classifier output shape is", classified.get_shape()
        
        # provide classification on images
        imageclassifier = Model(input_img, classified)
        imageclassifier.compile(optimizer='adadelta', loss='categorical_crossentropy', metrics=['mae'] )
        
        # and classifications of encoded representations
        fc = encoded_input
        for l in range(-n, 0):
            fc = imageclassifier.layers[l](fc)
        
        featureclassifier = Model(encoded_input, fc)
        featureclassifier.compile(optimizer='adadelta', loss='categorical_crossentropy', metrics=['acc'])
        
        
        # complete model (1 input, 2 outputs)
        classycoder = Model(inputs=[input_img], outputs=[decoded, classified])
        classycoder.compile(
            optimizer='adadelta', 
            loss=['mean_squared_error', 'categorical_crossentropy'],
            loss_weights=[0.8, 1.2],
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
        

