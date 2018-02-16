# From https://github.com/keras-team/keras/blob/master/examples/mnist_cnn.py


from tensorflow.python import keras
from tensorflow.python.keras.datasets import mnist
from tensorflow.python.keras.models import Sequential
from tensorflow.python.keras.layers import Dense, Dropout, Flatten
from tensorflow.python.keras.layers import Conv2D, MaxPooling2D
from tensorflow.python.keras import backend as K

import numpy as np
import os, sys
os.environ["CUDA_VISIBLE_DEVICES"]="0"

def get_gradients1(model):
    """Return the gradient of every trainable weight in model

    Parameters
    -----------
    model : a keras model instance

    First, find all tensors which are trainable in the model. Surprisingly,
    `model.trainable_weights` will return tensors for which
    trainable=False has been set on their layer (last time I checked), hence the extra check.
    Next, get the gradients of the loss with respect to the weights.

    """
    # print([i for i in model.trainable_weights if model.get)
    # indexes =  [i for i,tensor in enumerate(model.trainable_weights) if model.get_layer(index=i).trainable]
    weights = model.trainable_weights # weight tensors
    weights = [weight for i,weight in enumerate(weights) if model.get_layer(index=i).trainable] # filter down weights tensors to only ones which are trainable
    gradients = model.optimizer.get_gradients(model.total_loss, weights) # gradient tensors
    
    input_tensors = [model.inputs[0], # input data
                     model.sample_weights[0], # how much to weight each sample by
                     model.targets[0], # labels
                     K.learning_phase(), # train or test mode
    ]
    
    get_gradients = K.function(inputs=input_tensors, outputs=gradients)
    
    inputs = [[np.ones_like(x_train[0])], # X
          [1], # sample weights
          [y_train[0]], # y
        #   mutation,
          0 # learning phase in TEST mode
    ]
    
    print(get_gradients(inputs)[-1])

def overrideLoss(y_true, y_pred):
    """
    Desire:
    Manually generate derivative of the loss function.
    
    Approach:
    If loss = y_true * y_pred
    Then dLoss / dy_pred = y_true
    
    Notes:
    Normally pass y_pred into the compiled network, and the loss function
    does it's magic (computes derivatives, outputs a loss). 
    
    However, we can pass in an arbitrary y_true to be used as derivaties, 
    handling evaluation of the performance elsewhere.
    
    Warning:
    Does this make sense? I don't know yet...
    
    
    """
    return y_true * y_pred

batch_size = 256
num_classes = 10
epochs = 12

# input image dimensions
img_rows, img_cols = 28, 28

# the data, shuffled and split between train and test sets
(x_train, y_train), (x_test, y_test) = mnist.load_data()

if K.image_data_format() == 'channels_first':
    x_train = x_train.reshape(x_train.shape[0], 1, img_rows, img_cols)
    x_test = x_test.reshape(x_test.shape[0], 1, img_rows, img_cols)
    input_shape = (1, img_rows, img_cols)
else:
    x_train = x_train.reshape(x_train.shape[0], img_rows, img_cols, 1)
    x_test = x_test.reshape(x_test.shape[0], img_rows, img_cols, 1)
    input_shape = (img_rows, img_cols, 1)

x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255
print('x_train shape:', x_train.shape)
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

model = Sequential()
model.add(Conv2D(32, kernel_size=(3, 3),
                 activation='relu',
                 input_shape=input_shape))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))
model.add(Flatten())
model.add(Dense(128, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(num_classes, activation='softmax'))

opt = keras.optimizers.SGD(lr=1.0/batch_size, momentum=0.0, decay=0.0, nesterov=False)
# opt = keras.optimizers.SGD()
model.compile(loss=overrideLoss,
              optimizer=opt,
              metrics=['accuracy', 'mse'])

tf_session = K.get_session()

# model.fit(x_train, y_train,
#           batch_size=batch_size,
#           epochs=epochs,
#           verbose=1,
#           validation_data=(x_test, y_test))

metrics = model.metrics_names
numBatches = len(x_train)//batch_size
batchSizeVector = np.ones((batch_size,1))
Nsamples = 50
alpha = 1E-0
std = 1E-1
es_params = np.zeros(num_classes)
w_best = model.get_weights()
acc_best = 0.0
with open('es_training.txt', 'w+') as f:
    count = 0
    update_count = 0
    for i in range(epochs):
        for j in range(numBatches):
            count+=1
            # print("Iteration: "+str(count))
            # save a copy of the weights
            # mutated evaluate returns
            # es_params = np.zeros(num_classes)
            mutations = np.random.normal(scale=std, size=(Nsamples, num_classes))
            returns = []
            for k in range(Nsamples):
                model.set_weights(w_best)
                mutation = np.expand_dims(es_params+mutations[k],0)
                # optimize the network with the mutation 
                #   on 1, 2, .., m steps
                # print(mutation)
                model.train_on_batch(x_train[j:j+batch_size], batchSizeVector @ mutation)
                # Return is your score on the batch
                returns.append(-model.evaluate(x_train[j:j+batch_size], 
                                              y_train[j:j+batch_size], verbose=0)[2])
            # print(es_params+np.mean(mutations,0))
            # es_params += alpha * (1/(Nsamples*std)) * np.sum(mutations.T * returns,-1)
            # Normalize our returns
            returns = (returns - np.mean(returns)) / (np.std(returns)+0.0000001)
            es_params += alpha * (1/(Nsamples*std)) * np.squeeze(np.dot(mutations.T, returns))
            
            # make actual step
            model.set_weights(w_best)
            mutation = np.expand_dims(es_params,0)
            
            
            # print(w0[-1])
            # print('foo')
            # print(mutation)
            model.train_on_batch(x_train[j:j+batch_size], batchSizeVector @ mutation)
            # get_gradients1(model)
            # print(opt.get_gradients(1.0, model.get_layer(index=6)))
            _ = model.evaluate(x_train[j:j+batch_size], y_train[j:j+batch_size], verbose=0)
            
            sys.stdout.write(str(["Itr: " +str(i)+'.'+str(j)]+[m + ', ' + str(_[i]) for i,m in enumerate(metrics)]))
            
            use_best_weights = False
            if use_best_weights and _[2] > acc_best:
                w_best = model.get_weights()
                sys.stdout.write("...weight update "+str(update_count))
                update_count += 1
                acc_best = _[2]
            elif not use_best_weights:
                w_best = model.get_weights()
                sys.stdout.write("...weight update "+str(update_count))
                update_count += 1
            sys.stdout.write('       \r')
            
            f.write(str(_)+'\n')
        
            if count % 50 == 0:
                score = model.evaluate(x_test, y_test, verbose=0)
                print("Iteration: ", str(count))
                print('Test accuracy:', score[1])
    
score = model.evaluate(x_test, y_test, verbose=0)



print('Test loss:', score[0])
print('Test accuracy:', score[1])


# --------------- ES Section --------------- #
import numpy as np
Nparams = 3
Nepisodes = 300
Nsamples = 50

alpha = 1E-3
std = 1E-2

gt_params = np.random.normal(size=Nparams)
es_params = np.random.normal(size=Nparams)
solution = gt_params

# Mapping Function params->output
def foo1(params):
	return np.sum([(i+1)*p for i, p in enumerate(params)])

def F(w): return -np.sum((w - solution)**2)

# Score function
# def F(params):
# 	global gt_params
# 	return -1 * np.sum(np.abs(foo(gt_params)-foo(params)))

for i in range(Nepisodes):
	mutation = np.random.normal(size=(Nsamples, Nparams))
	returns = np.expand_dims([F(es_params+mutation[i]*std) for i in range(Nsamples)], -1)
# 	returns = (returns - np.mean(returns)) / np.std(returns)
	a =  np.dot(mutation.T, returns)
	b = alpha * (1/(Nsamples*std))
# 	print(a.shape)
# 	print(b)
# 	print(es_params.shape)
# 	es_params += alpha * (1/(Nsamples*std)) * np.squeeze(np.dot(mutation.T, returns))
	es_params += alpha * (1/(Nsamples*std)) * np.squeeze(np.sum(mutation * returns))

# print("GT PARAMS: "+str(gt_params))
# print("ES PARAMS: "+str(es_params))

