

import numpy as np
from pathlib import Path
from PIL import Image

from skimage import data, io, filters
from scipy.ndimage.morphology import binary_dilation, binary_erosion, grey_dilation, grey_erosion
from skimage.morphology import watershed, diamond
from skimage.segmentation import random_walker
from scipy.ndimage.measurements import watershed_ift
from skimage.feature import peak_local_max
from scipy import ndimage
from skimage import measure

from mpyx import EZ, As, F, Iter, Seq, Stamp

import time


class Linescan:
    
    NIR_GLOB = "LS.NIR*.tif"
    VIS_GLOB = "LS.VIS*.tif"
    
    
    def __init__(self, path, crop = 48, debug = False):
        
        p = Path(path)
        
        vis_files = list(sorted(p.glob(self.VIS_GLOB)))
        nir_files = list(sorted(p.glob(self.NIR_GLOB)))
        
        if debug: # - decrese data size # approx 100000 tall slice from center of LS
            vis_files = vis_files[100:110]
            nir_files = nir_files[100:110]
        
        if len(nir_files) != len(vis_files):
            raise RuntimeError("Number of NIR files does not equal number of VIS files in target directory")
            
        paired = list(zip(vis_files, nir_files))
        
        
        self.im = []
        self.bg = []
        self.dv = []
        self.mk = []
        self.mk2 = []
        self.markers = []
        
        
        def load_n_combine(pair):
            # visible light RGB
            vis = np.array(Image.open(pair[0]))[:, crop : -crop, :]
            
            #Near infrared
            nir = np.array(Image.open(pair[1]))[:, crop : -crop, np.newaxis]
            
            im  = np.concatenate((vis, nir), axis=2)
            bg  = np.median(im, axis=0)[np.newaxis, :, :] + 0.00001
            
            dv  = im/bg

            mk = np.zeros(dv.shape)
            mk[dv > 1.4] = 1
            mk[dv < 0.6] = 1
            
            mk2 = np.sum(mk, axis=2) / 4.0
            mk2[mk2 > 0] = 1
            
            
            """
            d = ndimage.distance_transform_cdt(mk2)
            d = (d - np.min(d)) / (np.max(d) - np.min(d))
            
            lb = ndimage.label(mk2.astype('bool'))
            
            local_maxi = peak_local_max(d, indices=False, footprint=np.ones((1,1)))
            markers = ndimage.label(local_maxi)[0]
            """
            
            
            #return (im, bg, dv, mk, mk2) #, markers)
            return (im, mk2)
        
        for part in EZ(Iter(paired), Seq(
                (load_n_combine, load_n_combine, load_n_combine, 
                 load_n_combine, load_n_combine, load_n_combine, 
                 load_n_combine, load_n_combine, load_n_combine, 
                 load_n_combine, load_n_combine, load_n_combine),
                 Stamp()
            )).daemonize().items():
                
            self.im.append(part[0])    
            self.mk2.append(part[1])    
                
            """
            self.im.append(part[0])
            self.bg.append(part[1])
            self.dv.append(part[2])
            self.mk.append(part[3])
            self.mk2.append(part[4])
            #self.markers.append(part[5])
            """
            
        
        
        start = time.time()
        
        self.im = np.concatenate(self.im)
        #self.bg = np.concatenate(self.bg)
        #self.dv = np.concatenate(self.dv)
        #self.mk = np.concatenate(self.mk)
        self.mk2 = np.concatenate(self.mk2)
        print("concat took", time.time() - start, "seconds")
        
        start = time.time()
        self.mk2 = np.array(
            binary_dilation(
            binary_erosion(    self.mk2, iterations=5), 
                                         iterations=5)
            , dtype='bool')
        print("dialation took", time.time() - start, "seconds")
        
        
        start = time.time()
        self.labels = measure.label(self.mk2, background=0)
        
        print("labels took", time.time() - start, "seconds")
        
        
        start = time.time()
        self.props = measure.regionprops(self.labels, self.im[:,:,0])
        
        print("props took", time.time() - start, "seconds")







def equalize(f):
    #doesn't work very well..
    h = np.histogram(f, bins=np.arange(256))[0]
    H = np.cumsum(h) / float(np.sum(h))
    e = np.floor(H[f.flatten().astype('int')] * 255.).astype('uint8')
    return e.reshape(f.shape) 

# NumPy / SciPy Recipes for Image Processing: Intensity Normalization and Histogram Equalization (PDF Download Available). Available from: https://www.researchgate.net/publication/281118372_NumPy_SciPy_Recipes_for_Image_Processing_Intensity_Normalization_and_Histogram_Equalization [accessed Mar 02 2018].


