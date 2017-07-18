from ClassyCoder import ClassyCoder
from keras.datasets import mnist
from keras.utils import to_categorical
import numpy as np

from dataset_generator import dataset_generator

DG = dataset_generator()

CC = ClassyCoder((64, 64, 1), 5, True)

categories = 5

def fetch_data(n = 128, training=True):
    (X, Y) = DG.fetch(n, training)
    X = X.astype('float32') / 255.
    X = X.reshape((len(X), 64, 64, 1))
    Y = to_categorical(Y, categories)
    return (X, Y)



for i in range(5):
    (x_train, y_train) = fetch_data(2000, True)
    (x_test, y_test) = fetch_data(300, True)

    CC.classycoder.fit(x_train, [x_train, y_train],
        epochs=5,
        batch_size=32,
        shuffle=True,
        validation_data=(x_test, [x_test, y_test]))
    
    
    (x_auto, _) = fetch_data(8000, False)
    y_auto = CC.imageclassifier.predict(x_auto)
    y_auto = np.argmax(y_auto, axis=-1)
    y_auto = to_categorical(y_auto, categories)
    (x_test, y_test) = fetch_data(300, True)

    CC.classycoder.fit(x_train, [x_train, y_train],
        epochs=5,
        batch_size=32,
        shuffle=True,
        validation_data=(x_test, [x_test, y_test]))





(x_test, y_test) = fetch_data(200, False)

# encode and decode some crops
# note that we take them from the *test* set
encoded_imgs = CC.encoder.predict(x_test)
decoded_imgs = CC.decoder.predict(encoded_imgs)
classif_imgs = CC.featureclassifier.predict(encoded_imgs)

# use Matplotlib (don't ask)
import matplotlib.pyplot as plt

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
    plt.imshow(encoded_imgs[i].reshape(4, 128).T)
    plt.gray()
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
plt.show()



score = CC.featureclassifier.evaluate(encoded_imgs, y_test, verbose=0)
print('Classifier Accuracy:', score[1])


