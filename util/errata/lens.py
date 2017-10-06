#! /usr/bin/env python
"""
Experiment in applying a "lens", or tanh tansform to the crops.


Author: Martin Humphreys
"""



import cv2
import numpy as np
from scipy.interpolate import interp2d



a = cv2.imread("a.png", 0)
h, w = a.shape


cx, cy = w/2.0, h/2.0



xs = np.linspace(-0.98, 0.98, 512)
ys = np.linspace(-0.98, 0.98, 512)

s = 8.


k = 0
while k in [0, 82, 81, 84, 83, 97, 122]:
    if k == 82:
        cy -= 10
    if k == 81:
        cx -= 10
    if k == 84:
        cy += 10
    if k == 83:
        cx += 10
    if k == 97:
        s += 1
    if k == 122:
        s -= 1

    print cx, cy, s

    x = np.arctanh(xs)
    x /= np.max(x) * s
    x = x * cx + cx
    
    y = np.arctanh(ys)
    y /= np.max(y) * s
    y = y * cy + cy
    
    
    
    print "a", x
    
    print "shape", w, h, a.shape
    
    f = interp2d(np.arange(w), np.arange(h), a, kind="cubic")
    b = f(x, y).astype("uint8")
    
    """
    xs = np.linspace(-2.05, 2.05, w)
    
    x = np.tanh(xs)
    x /= np.max(x)
    x = x * cx + cx
    print "b", x
    
    
    f = interp2d(np.arange(w), np.arange(h), b, kind="cubic")
    c = f(x, x).astype("uint8")
    """
    cv2.imshow("ident", a)
    cv2.imshow("arctanh", b)
    #cv2.imshow("tanh", c)
    k = cv2.waitKey(0)
    
