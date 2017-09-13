#! /usr/bin/env python

import cv2
import numpy as np
from numpy.fft import fft, ifft


a = cv2.imread("a.png", 0).astype("float64") / 255.0 - 0.5
b = cv2.imread("b.png", 0).astype("float64") / 255.0 - 0.5


c = np.zeros_like(a)

for i in range(len(c[0,:])):
    a[len(c) / 2, i] = 0.2
    
for i in range(len(c[0,:])):
    b[len(c) / 2, i] = 0.3


"""
a = [[0,0,0,1,1,0],
     [0,1,0,0,0,0],
     [0,0,0,0,0,0],
     [0,0,0,1,1,0],
     [0,0,0,0,0,0]]

b = [[0,0,0,0,0,0],
     [0,0,0,1,1,0],
     [0,0,0,0,0,0],
     [0,1,0,1,1,0],
     [0,0,0,0,0,0]]

a = np.array(a).astype("float64")
b = np.array(b).astype("float64")
"""



print a.shape

def transformRange(value, oldmin, oldmax, newmin, newmax):
    return (((value - oldmin) * (newmax - newmin)) / (oldmax - oldmin)) + newmin

def cor(a, b):
    return ifft(fft(a) * fft(b).conj()).real

def ccor(a, b):
    c = cor(a, b)
    #return c / 500
    return transformRange(c, np.min(c), np.max(c), 0, 1)

def con(a, b):
    return ifft(fft(a) * fft(b)).real

def nco(a, b):
    return np.correlate(a, b, mode="same")


for i in range(len(a[0,:])):
    """
        ga = fft(a[:, i])
        gb = fft(b[:, i])
        
        r = ga * gb.conj()
        n = np.linalg.norm(r.real)
        
        c[:, i] = ifft(r)/ 1000.0
    """
    c[:, i] = ccor(a[:, i], b[:, i])
    #c[np.argmax(ccor(a[:, i], b[:, i])), i] = 1
print np.max(c)


c = np.roll(c, (len(c) / 2, 0), axis=0)


for i in range(len(c[0,:])):
    c[len(c) / 2, i] = 0


c = np.flipud(c)

"""
ga = fft(a)
gb = fft(b)

r = ga * gb.conj()
n = np.linalg.norm(r)
d = ifft(r / 1000)
"""
print cv2.phaseCorrelate(a,b)
cv2.imshow(None, (c).real)
cv2.waitKey(0)
    
