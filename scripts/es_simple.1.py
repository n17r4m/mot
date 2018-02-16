# From https://github.com/keras-team/keras/blob/master/examples/mnist_cnn.py


from tensorflow.python import keras
from tensorflow.python.keras.models import Sequential
from tensorflow.python.keras.layers import Dense, Dropout, Flatten, Input
from tensorflow.python.keras.layers import Conv2D, MaxPooling2D
from tensorflow.python.keras import backend as K

import numpy as np
import os, sys
os.environ["CUDA_VISIBLE_DEVICES"]="2"

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
    # print(y_true)
    # print(y_pred)
    return K.transpose(y_true) @ y_pred

batch_size = 256
num_classes = 1
epochs = 12

# input image dimensions
img_rows, img_cols = 28, 28

def f(x):
    return np.sin(x)
    
# the data, shuffled and split between train and test sets
x_train = 4*np.pi * np.random.random((60000,num_classes)) - 2*np.pi
x_test = 4*np.pi * np.random.random((60000,num_classes)) - 2*np.pi
y_train = np.apply_along_axis(f, 1, x_train)
y_test = np.apply_along_axis(f, 1, x_test)

# x_train = (x_train - np.mean(x_train)) / np.std(x_train)
# x_test = (x_test - np.mean(x_test)) / np.std(x_test)
# y_train = (y_train - np.mean(y_train)) / np.std(y_train)
# y_test = (y_test - np.mean(y_test)) / np.std(y_test)

print('x_train shape:', x_train.shape)
print('y_train shape:', y_train.shape)
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

model = Sequential()
# model.add(Input(shape=input_shape))
model.add(Dense(10, input_shape=(num_classes,), activation='relu'))
# model.add(Dense(10, activation='relu'))
model.add(Dense(1))
# model.add(Dense(num_classes, activation='softmax'))

opt = keras.optimizers.SGD(lr=1.0, momentum=0.0, decay=0.0, nesterov=False)
# opt = keras.optimizers.Adadelta()
model.compile(loss=overrideLoss,
              optimizer=opt,
              metrics=['mse'])
# print(model.model.summary())
# model.fit(x_train, y_train,
#           batch_size=batch_size,
#           epochs=epochs,
#           verbose=1,
#           validation_data=(x_test, y_test))

metrics = model.metrics_names
numBatches = len(x_train)//batch_size
batchSizeVector = np.ones((batch_size,1))
Nsamples = 50
alpha = 1E-3
std = 1E-1
es_params = np.zeros((1))
w_best = model.get_weights()
acc_best = 0.0

count = 0
update_count = 0
for i in range(epochs):
    for j in range(numBatches):
        for k in range(batch_size):
            count+=1
            # print("Iteration: "+str(count))
            # save a copy of the weights
            # mutated evaluate returns
            # es_params = np.zeros(num_classes)
            mutations = np.random.normal(scale=std, size=(Nsamples, 1))
            returns = []
            for m in range(Nsamples):
                model.set_weights(w_best)
                mutation = np.expand_dims(es_params+mutations[m],0)
                # optimize the network with the mutation 
                #   on 1, 2, .., m steps
                # print(mutation)
                model.train_on_batch(x_train[j+k:j+k+1], mutation)
                # Return is your score on the batch
                returns.append(-model.evaluate(x_train[j+k:j+k+1], 
                                               y_train[j+k:j+k+1], verbose=0)[1])
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
            model.train_on_batch(x_train[j+k:j+k+1], mutation)
            # get_gradients1(model)
            # print(opt.get_gradients(1.0, model.get_layer(index=6)))
            _ = model.evaluate(x_train[j:j+batch_size], y_train[j:j+batch_size], verbose=0)
            sys.stdout.write('\x1b[2K')
            sys.stdout.write(str(["Itr: " +str(i)+'.'+str(j)+'.'+str(k)]+[met + ', ' + str(_[n]) for n,met in enumerate(metrics)]))
            
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
            sys.stdout.write('\r')
            
        
        
        score = model.evaluate(x_test, y_test, verbose=0)
        sys.stdout.write('\x1b[2K')
        print("Epoch " + str(i) + " Batch: "+ str(j))
        print('Test mse:', score[1])

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

