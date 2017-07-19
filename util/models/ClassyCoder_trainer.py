from ClassyCoder import ClassyCoder
from keras.datasets import mnist
from keras.utils import to_categorical
import matplotlib.pyplot as plt
import numpy as np
import os


from dataset_generator import dataset_generator

DG = dataset_generator()

CC = ClassyCoder((64, 64, 1), 5, True)

CATEGORIES = 5

def fetch_data(n = 128, training=True):
    (X, Y) = DG.fetch(n, training)
    X = X.astype('float32') / 255.
    X = X.reshape((len(X), 64, 64, 1))
    Y = to_categorical(Y, CATEGORIES)
    return (X, Y)


def train_labeled(CC, samples=1024, epochs=5, bs=32):
    for i in range(5):
        print "LLLLLLLLLLLLL"
    (x_train, y_train) = fetch_data(samples, True)
    (x_test, y_test) = fetch_data(512, True)
    CC.classycoder.fit(x_train, [x_train, y_train],
        epochs=epochs,
        batch_size=32,
        shuffle=True,
        validation_data=(x_test, [x_test, y_test]))

def train_unlabeled(CC, samples=8192, epochs=5, bs=32):
    for i in range(5):
        print "UUUUUUUUUUUUU"
    (x_auto, _) = fetch_data(samples, False)
    y_auto = CC.imageclassifier.predict(x_auto)
    y_auto = np.argmax(y_auto, axis=-1)
    y_auto = to_categorical(y_auto, CATEGORIES)
    (x_test, y_test) = fetch_data(512, True)
    CC.classycoder.fit(x_auto, [x_auto, y_auto],
        epochs=epochs,
        batch_size=32,
        shuffle=True,
        validation_data=(x_test, [x_test, y_test]))
        
        

train_labeled(CC, 4096, 5, 32)

for i in range(10):
    train_labeled(CC, 1024, 1, 128)
    train_unlabeled(CC, 512, 1, 128)

for i in range(2):
    train_labeled(CC, 4092, 2, 64)
    train_unlabeled(CC, 2048, 2, 64)

for i in range(2):
    train_labeled(CC, 2048, 3, 64)
    train_unlabeled(CC, 4092, 3, 64)

for i in range(2):
    train_labeled(CC, 2048, 1, 128)
    train_unlabeled(CC, 8192, 1, 128)
    train_labeled(CC, 2048, 1, 32)
    train_unlabeled(CC, 8192, 1, 32)

for i in range(2):
    train_labeled(CC, 2048, 2, 128)
    train_unlabeled(CC, 16384, 2, 128)

for i in range(2):
    train_labeled(CC, 2048, 5, 128)
    train_unlabeled(CC, 16384, 2, 128)
    train_labeled(CC, 2048, 2, 128)    

    
    
    



(x_test, y_test) = fetch_data(8000, True)

# encode and decode some crops
# note that we take them from the *validation* set TODO TODO
encoded_imgs = CC.encoder.predict(x_test)
decoded_imgs = CC.decoder.predict(encoded_imgs)
classif_imgs = CC.featureclassifier.predict(encoded_imgs)

score = CC.featureclassifier.evaluate(encoded_imgs, y_test, verbose=0)
print('Classifier Accuracy:', score[1])




(x_test, y_test) = fetch_data(200, False)

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




mypath = os.path.dirname(os.path.realpath(__file__))

CC.save(os.path.join(mypath, "ClassyCoder.h5"))


