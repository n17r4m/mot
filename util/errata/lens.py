#! /usr/bin/env python
"""
Experiment in applying a "lens", or tanh tansform to the crops.


Author: Martin Humphreys
"""



import cv2
import numpy as np
from scipy.interpolate import interp2d



a = cv2.imread("x.png", 0)
w, h = a.shape
cx, cy = w/2.0, h/2.0



xs = np.linspace(-0.98, 0.98, w)



x = np.arctanh(xs)
x /= np.max(x)
x = x * cx + cx

print "a", x

f = interp2d(np.arange(w), np.arange(h), a, kind="cubic")
b = f(x, x).astype("uint8")


xs = np.linspace(-2.05, 2.05, w)

x = np.tanh(xs)
x /= np.max(x)
x = x * cx + cx
print "b", x


f = interp2d(np.arange(w), np.arange(h), b, kind="cubic")
c = f(x, x).astype("uint8")

cv2.imshow("ident", a)
cv2.imshow("arctanh", b)
cv2.imshow("tanh", c)
cv2.waitKey(0)