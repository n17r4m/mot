
from keras.models import Model, Sequential
from keras.layers import Input, Activation, Flatten, Conv2D, Dense, MaxPooling2D, UpSampling2D, Concatenate, Dropout

class ClassyCoder:
    
    
    
    def __init__(self, input_shape=(256, 256, 1), num_categories=3 , verbose=False):
        """
        https://keras.io/getting-started/functional-api-guide/#multi-input-and-multi-output-models
        https://keras.io/getting-started/functional-api-guide/#shared-layers
        https://blog.keras.io/building-autoencoders-in-keras.html
        
        TEMP: Crops at /k_scratch/VEAGAN/drops/grey_32
        
        """
        
        input_img = Input(shape=input_shape, name="main_input")
        
                
        x = Conv2D(16, (3, 3), activation='relu', padding='same')(input_img)
        x = MaxPooling2D((2, 2), padding='same')(x)
        x = Conv2D(8, (3, 3), activation='relu', padding='same')(x)
        x = MaxPooling2D((2, 2), padding='same')(x)
        x = Conv2D(8, (3, 3), activation='relu', padding='same')(x)
        encoded = MaxPooling2D((2, 2), padding='same', name="encoded")(x)
        
        # at this point the representation is (4, 4, 8) i.e. 128-dimensional
        # this model maps an input to its encoded representation
        encoder = Model(input_img, encoded)
        
        # next, declare the auto_encoding output side
         
        n = 0;
        n +=1; ae = Conv2D(8, (3, 3), activation='relu', padding='same')(encoded)
        n +=1; ae = UpSampling2D((2, 2))(ae)
        n +=1; ae = Conv2D(8, (3, 3), activation='relu', padding='same')(ae)
        n +=1; ae = UpSampling2D((2, 2))(ae)
        n +=1; ae = Conv2D(16, (3, 3), activation='relu')(ae)
        n +=1; ae = UpSampling2D((2, 2))(ae)
        n +=1; decoded = Conv2D(1, (3, 3), activation='sigmoid', padding='same')(ae)
        
        autoencoder = Model(input_img, decoded)
        autoencoder.compile(optimizer='adadelta', loss='mean_squared_error')
        
        # use right side of architecture encoded input to construct an image
        encoded_input = Input(shape=(4, 4, 8))
        deco = encoded_input
        for l in range(-n, 0):
            deco = autoencoder.layers[l](deco)
        
        decoder = Model(encoded_input, deco)
        
        
        # and then, the classifier output
        
        cl = Flatten()(encoded)
        cl = Dense(128, activation='relu')(cl)
        cl = Dropout(0.5)(cl)
        classified = Dense(num_categories, activation='softmax')(cl)
        
        classifier = Model(input_img, classified)
        classifier.compile(optimizer='adadelta', loss='categorical_crossentropy')
        
        classycoder = Model(inputs=[input_img], outputs=[decoded, classified])
        classycoder.compile(
            optimizer='adadelta', 
            loss=['mean_squared_error', 'categorical_crossentropy'],
            loss_weights=[1.0, 0.68])
        
        
        
        
        # Recieve a image and encode it into its latent space representation
        self.encoder = encoder
        
        # direct pipe from input_image to its reconstruction
        self.autoencoder = autoencoder
        
        # reconstructs an image from its encoded representation
        self.decoder = decoder
        
        # direct pipe from input_image to its classification
        self.classifier = classifier
        
        # multiple output model, train this for the rest to work.
        self.classycoder = classycoder
        

