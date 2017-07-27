from ClassyCoder import ClassyCoder
from keras.datasets import mnist
from keras.utils import to_categorical
import matplotlib.pyplot as plt
import numpy as np
import os


from dataset_generator import dataset_generator


CATEGORIES = 5

DG = dataset_generator()

CC = ClassyCoder((64, 64, 1), CATEGORIES, True)


def fetch_data(training=True, samples = 128):
    (X, Y) = DG.fetch(samples, training)
    X = X.astype('float32') / 255.
    X = X.reshape((len(X), 64, 64, 1))
    Y = [X, to_categorical(Y, CATEGORIES)]
    return (X, Y)

def fetch_data_generator(training=True, samples = 128):
    while True:
        yield fetch_data(training, samples)
        


#(x_train, y_train) = fetch_data(1024, True)

CC.classycoder.fit_generator(fetch_data_generator(True, 32), 1000,
    epochs=20,
    validation_data=fetch_data_generator(False, 128),
    validation_steps=5 )

        

(x_test, y_test) = fetch_data(False, 100)

# encode and decode some crops
# note that we take them from the *validation* set
encoded_imgs = CC.encoder.predict(x_test)
decoded_imgs = CC.decoder.predict(encoded_imgs)
classif_imgs = CC.featureclassifier.predict(encoded_imgs)

score = CC.featureclassifier.evaluate(encoded_imgs, y_test[1], verbose=0)
print('Classifier Accuracy:', score[1])


CC.save(os.path.join(CC.path(), "ClassyCoder.h5"))

print("weights saved")





(x_test, y_test) = fetch_data(False, 100)

# encode and decode some crops
# note that we take them from the *test* set
encoded_imgs = CC.encoder.predict(x_test)
decoded_imgs = CC.decoder.predict(encoded_imgs)
classif_imgs = CC.featureclassifier.predict(encoded_imgs)



n = 20  # how many crops we will display
plt.figure(figsize=(20, 4))
for i in range(n):
    # display original
    ax = plt.subplot(3, n, i + 1)
    plt.imshow(x_test[i].reshape(64, 64))
    plt.gray()
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)

    # display reconstruction
    ax = plt.subplot(3, n, i + 1 + n)
    plt.imshow(decoded_imgs[i].reshape(64, 64))
    plt.gray()
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    
    # display classification
    ax = plt.subplot(3, n, i + 1 + 2*n)
    plt.imshow(classif_imgs[i].reshape(1, 5))
    plt.gray()
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    
plt.show()





n = 20
plt.figure(figsize=(20, 8))
for i in range(n):
    ax = plt.subplot(1, n, i + 1)
    plt.imshow(encoded_imgs[i].reshape(8,64).T)
    plt.gray()
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
plt.show()

