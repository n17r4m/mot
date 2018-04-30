
from lib.Linescan import Linescan
import numpy as np
import time

#path = "/home/mot/data/source/Water and Test Sand/LineScan01069/"
#path = "/home/mot/data/source/Water, Clay and Test Sand/LineScan01075/"
path = "/home/mot/data/source/Water, NaOH and Oil Sand/LineScan01111/"

#start = ls[55000:75000, :, 0:3]   # l.ls[1000:2000]
#print(start)



from skimage import data, io, filters
from scipy.ndimage.morphology import binary_dilation, binary_erosion, grey_dilation, grey_erosion
from skimage.morphology import watershed, diamond
from skimage.segmentation import random_walker
from scipy.ndimage.measurements import watershed_ift
from skimage.feature import peak_local_max
from skimage import measure

from scipy import ndimage

from scipy.misc import imresize

import cv2

from uuid import uuid4


from lib.Database import Database, DBWriter

print("ready")

ls = Linescan(path, debug=False)
print("loaded")
start = time.time()

#sy, ey = 400, 2000    # display sample height
#sx, ex = 400, 2000   # display sample width

#sy, ey, sx, ex = 101750, 104250, 1000, 1700


sy, ey, sx, ex = 200000, 202000, 500, 1800

#sy, ey, sx, ex = 101750, 102250, 1000, 1700

vis = ls.vis[sy:ey, sx:ex]
nir = ls.nir[sy:ey, sx:ex]
im  = ls.im[sy:ey, sx:ex]



#dv  = ls.dv[sy:ey, sx:ex]
#dv2  = ls.dv2[sy:ey, sx:ex]
dv3  = ls.dv3[sy:ey, sx:ex]

im[1000,:,:] = 0


#dv  = ls.dv[sy:ey, sx:ex]
mk = ls.mk[sy:ey, sx:ex]
mk2 = ls.mk2[sy:ey, sx:ex]
labels = ls.labels[sy:ey, sx:ex]
props = ls.props


#labels = watershed_ift((255.0 * mk2).astype("uint8"), mk2.astype('int'))#, mask=bit4)


cv2.imshow("vis", vis)
cv2.imshow("nir", nir)
cv2.imshow("im", im)
#cv2.imshow("divided2", dv2)
cv2.imshow("divided3", dv3)
cv2.imshow("pre-mask", (mk).astype('uint8'))
cv2.imshow("mask", (mk2*255.).astype('uint8'))
print(np.min(labels), np.max(labels))
cv2.imshow("labels", labels.astype('uint8'))


"""

cv2.imshow("zz", ls.zz[sy:ey, sx:ex])
cv2.imshow("z2", ls.z2[sy:ey, sx:ex])
"""

"""
cv2.imshow("multiply in", 127 * np.sqrt(im*dv3).astype("uint8"))
cv2.imshow("divide 1", 127 * (im/dv3).astype("uint8"))
cv2.imshow("divide 2", 127 * (dv3/im).astype("uint8"))
"""

cv2.waitKey(0)



db = Database()
tx = db.transaction()


for p in props:
    bb = p.bbox
    print(bb)
    
    div = ls.dv3[bb[0]:bb[2], bb[1]:bb[3]]
    div = imresize(div, size=(64,64))#, mode="bicubic")
    
    vis = ls.vis[bb[0]:bb[2], bb[1]:bb[3]]
    vis = imresize(vis, size=(64,64))
    
    nir = ls.nir[bb[0]:bb[2], bb[1]:bb[3]]
    nir = np.dstack([imresize(nir, size=(64,64))] * 3)
    
    mk2 = 255 * ls.mk2[bb[0]:bb[2], bb[1]:bb[3]]
    mk2 = np.dstack([imresize(mk2, size=(64,64))] * 3)
    
    crop = np.concatenate([vis, nir, div, mk2])
    
    cv2.imshow("crop", crop)
    k = cv2.waitKey(1)
    
    
    
    
    
    if k == ord('x'):
        break;








"""
with open("/home/martin/Pictures/ls_im.data", 'wb') as im:
    im.write(ls.im.tobytes())

with open("/home/martin/Pictures/ls_bg.data", 'wb') as im:
    im.write(ls.bg.tobytes())

with open("/home/martin/Pictures/ls_dv.data", 'wb') as im:
    im.write(ls.dv.tobytes())
"""


"""
io.imsave("/home/martin/Pictures/ls_bg.png", ls.im, "imread")

print("got im")

io.imsave("/home/martin/Pictures/ls_bg.png", ls.bg, "imread")

print("got bg")

io.imsave("/home/martin/Pictures/ls_norm.png", ls.dv, "imread")

print("got dv")
"""

#cv2.imshow("title", ls.ls[:, :, 0:3].astype("float64"))
#quickcv2.waitKey(0)

"""
17312020 kB




"""
