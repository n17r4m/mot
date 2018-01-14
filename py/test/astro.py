import os

import numpy as np
from skimage import io

import matplotlib.pyplot as plt

from photutils import DAOStarFinder, IRAFStarFinder
from astropy.stats import mad_std
from photutils import aperture_photometry, CircularAperture


img = io.imread("/home/mot/data/saliance/exp3/frame.png", as_grey=True)

img = 1-img


bkg_sigma = mad_std(img)    
daofind = IRAFStarFinder(fwhm=24., threshold=1.*bkg_sigma, )    
sources = daofind.find_stars(img)    
print(sources) 

positions = (sources['xcentroid'], sources['ycentroid'])    
apertures = CircularAperture(positions, r=8.)    
phot_table = aperture_photometry(img, apertures)    
print(phot_table)  

plt.imshow(img, cmap="gray")
apertures.plot(color='blue', lw=1.5, alpha=0.5)

plt.show()

