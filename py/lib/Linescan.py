

import numpy as np
from pathlib import Path
from PIL import Image

from skimage import data, io, filters
from scipy.ndimage.morphology import binary_dilation, binary_erosion, grey_dilation, grey_erosion
from skimage.morphology import opening
from skimage.morphology import watershed, diamond
from skimage.segmentation import random_walker
from skimage.filters import threshold_yen, threshold_otsu, threshold_triangle, threshold_mean
from scipy.ndimage.measurements import watershed_ift
from skimage.feature import peak_local_max
from scipy import ndimage
from skimage import measure, exposure

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
        
        
        self.vis = []
        self.nir = []
        self.im = []
        self.bg = []
        self.dv = []
        self.dv2 = []
        self.dv3 = []
        self.mk = []
        self.mk2 = []
        self.markers = []
        
        
        def load_n_combine(filename_pair):
            
            # load visual / near-infrared image pair
            vis = np.array(Image.open(filename_pair[0]), dtype="float64")[:, crop : -crop, :]
            nir = np.array(Image.open(filename_pair[1]), dtype="float64")[:, crop : -crop, np.newaxis][:,:,0]
            
            
            """
            print("R pre", np.min(vis[:,:,0]), np.max(vis[:,:,0]))
            print("G pre", np.min(vis[:,:,1]), np.max(vis[:,:,1]))
            print("B pre", np.min(vis[:,:,2]), np.max(vis[:,:,2]))    
            """
            
            
            im = vis.copy()
            # visible light RGB gets compressed into to green/blue space
            # blue has some unique differentations,/.?
            #im[:,:,2] = (vis[:,:,1] + vis[:,:,2]) / 2.0
            im[:,:,1] = (vis[:,:,0] + vis[:,:,1]) / 2.0
            
            # Near infrared gets placed on the "red" channel
            im[:,:,0] = nir
            
            # normalize to 0-1
            # todo: assert im > 1
            im = im / 255.
            
            # Find the background-line (1 px tall by n px wide)
            bg  = np.median(im, axis=0)[np.newaxis, :, :] + 0.00001
            
            
            # divide out the background and gamma correct
            dv  = (im/bg) ** 3
            
            # mask regions blown to >= 1
            m = dv > 1
            dv2 = dv.copy()
            
            # normalize and invert these areas
            dv2[m] = 1.0 - ((dv2[m] - np.min(dv2[m])) / (np.max(dv2[m]) - np.min(dv2[m])))
            
            # maybe something else or more fancy tech <- here,

            # create mask 
            mk = 1.0 - dv2
            
            #mk = np.zeros(dv2.shape, dtype="float64")
            #mk[dv2 < 0.9] = 1.0 - dv2[dv2 < 0.9]
            
            
            #print("mk stats", np.min(mk), np.mean(mk), np.median(mk), np.max(mk))
            
            # merge channels
            mk2 = (np.sum(mk, axis=2) / 3.0) ** 2.0
            
            #print("mk2 stats", np.min(mk2), np.mean(mk2), np.median(mk2), np.max(mk2))
            
            mk2 = mk2 > threshold_yen(mk2)
            #mk2[mk2 > 0.375] = 1
            #mk2[mk2 < 0.375] = 0
            
            
            dv3 = dv2 #hacky
            
            ##############
            # pass 2 - better background estimation
            ##############
            
            im2 = im.copy()
            im2[mk2] = (mk2[:,:,np.newaxis]*bg)[mk2]
            
            #b = (1 ^ mk2).astype("bool")
            
            
            # sol1
            # im2[b] = (b*bg)[b]
            
            
            # for r, row in enumerate(im2):
            #     row[b[r]] = bg[:, b[r]]
            
            
            
            bg = np.median(im2, axis=0)[np.newaxis, :, :] + 0.00001
            
            dv  = (im/bg) ** 3
            
            # mask regions blown to >= 1
            m = dv > 1
            dv2 = dv.copy()
            
            # normalize and invert these areas
            dv2[m] = 1.0 - ((dv2[m] - np.min(dv2[m])) / (np.max(dv2[m]) - np.min(dv2[m])))
            
            # maybe something else or more fancy tech <- here,

            # create mask 
            mk = 1.0 - dv2
            
            #mk = np.zeros(dv2.shape, dtype="float64")
            #mk[dv2 < 0.9] = 1.0 - dv2[dv2 < 0.9]
            
            
            #print("mk stats", np.min(mk), np.mean(mk), np.median(mk), np.max(mk))
            
            # merge channels
            mk2 = (np.sum(mk, axis=2) / 3.0) ** 2.0
            
            #print("mk2 stats", np.min(mk2), np.mean(mk2), np.median(mk2), np.max(mk2))
            
            mk2 = mk2 > threshold_yen(mk2)
            #mk2[mk2 > 0.375] = 1
            #mk2[mk2 < 0.375] = 0
            
            
            dv3 = dv2 #hacky
            
            
            
            #return (im, bg, dv, mk, mk2) #, markers)
            return (
                vis.astype('uint8'), 
                nir.astype('uint8'), 
                (im*255).astype('uint8'), 
                (dv3*255).astype('uint8'), 
                (mk*255).astype('uint8'),
                mk2.astype('bool')
            )
        
        
        
        start = time.time()
        very_start = start
        
        for part in EZ(Iter(paired), Seq(
                (load_n_combine, load_n_combine, load_n_combine, 
                 load_n_combine, load_n_combine, load_n_combine, 
                 load_n_combine, load_n_combine, load_n_combine, 
                 load_n_combine, load_n_combine, load_n_combine, 
                 load_n_combine, load_n_combine, load_n_combine, 
                 load_n_combine, load_n_combine, load_n_combine),
                 Stamp()
            )).items():
                
            self.vis.append(part[0])
            self.nir.append(part[1])
            
            self.im.append(part[2])    
            
            #self.dv2.append(part[1])    
            self.dv3.append(part[3])   
            self.mk.append(part[4])    
            self.mk2.append(part[5])    

            
        print("loading took", time.time() - start, "seconds")
        
        
        start = time.time()
        
        self.vis = np.concatenate(self.vis)
        self.nir = np.concatenate(self.nir)
        self.im = np.concatenate(self.im)
        #self.bg = np.concatenate(self.bg)
        #self.dv = np.concatenate(self.dv)
        #self.dv2 = np.concatenate(self.dv2)
        self.dv3 = np.concatenate(self.dv3)
        
        
        self.mk = np.concatenate(self.mk)
        self.mk2 = np.concatenate(self.mk2)
        print("concat took", time.time() - start, "seconds")
        
        start = time.time()
        """
        self.mk2 = np.array(
            binary_dilation(
            binary_erosion(    self.mk2, iterations=5), 
                                         iterations=5)
            , dtype='bool')
        """
        #self.mk2 = self.mk2.astype('bool')
        self.mk2 = opening(self.mk2).astype('bool')
        
        
        print("dialation took", time.time() - start, "seconds")
        
        
        start = time.time()
        self.labels = measure.label(self.mk2, background=0)
        
        print("labels took", time.time() - start, "seconds")
        
        
        start = time.time()
        self.props = measure.regionprops(self.labels, self.im[:,:,0])
        
        print("props took", time.time() - start, "seconds")

        print("total time", time.time() - very_start)

        



def equalize(f):
    #doesn't work very well..
    h = np.histogram(f, bins=np.arange(256))[0]
    H = np.cumsum(h) / float(np.sum(h))
    e = np.floor(H[f.flatten().astype('int')] * 255.).astype('uint8')
    return e.reshape(f.shape) 

# NumPy / SciPy Recipes for Image Processing: Intensity Normalization and Histogram Equalization (PDF Download Available). Available from: https://www.researchgate.net/publication/281118372_NumPy_SciPy_Recipes_for_Image_Processing_Intensity_Normalization_and_Histogram_Equalization [accessed Mar 02 2018].


