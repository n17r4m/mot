import numpy as np
import cv2
from skimage import color, data, restoration

# Remap an input range, not used
def remap(x, lo=0, hi=255):    
    out_rng = hi-lo
    in_rng = np.max(x) - np.min(x)
    return lo + ((x-np.min(x)) / in_rng) * out_rng

# I wrote my own clip, since I was working with images on range 0-255 not 0-1 like RL has
def clip(x):
    x[x>255] = 255
    x[x<0] = 0
    return x

def gkern(l=5, sig=1.):
    """
    creates gaussian kernel with side length l and a sigma of sig
    """   
    ax = np.arange(-l // 2 + 1., l // 2 + 1.)
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-(xx**2 + yy**2) / (2. * sig**2))

    return kernel / np.sum(kernel)

def kevs_richardson_lucy(image, psf, iterations=50, clip=True):
    # Note, I currently assume a 2D image (greyscale),
    # refer to https://github.com/scikit-image/scikit-image/blob/master/skimage/restoration/deconvolution.py
    # for higher D images
    from scipy.signal import convolve
    eps = np.finfo(image.dtype).eps

    im_deconv = 0.5 * np.ones(image.shape)
    psf_mirror = psf[::-1, ::-1]

    for _ in range(iterations):
        # https://github.com/scikit-image/scikit-image/issues/2551
        eps = np.finfo(image.dtype).eps
        x = convolve(im_deconv, psf, 'same')
        np.place(x, x==0, eps)
        relative_blur = image / x + eps        
        # relative_blur = image / convolve_method(im_deconv, psf, 'same')
        im_deconv *= convolve(relative_blur, psf_mirror, 'same')

    if clip:
        im_deconv[im_deconv > 1] = 1
        im_deconv[im_deconv < -1] = -1

    return im_deconv


#     ---- Read the input, convert to grayscale, make a small sample for testing -----     #
raw_img = cv2.imread('/home/mot/data/results/Glass.Bead.Tests/200.to.300.um/LineScan01034/image.png').astype('float64')
# Convert to grayscale
raw_img  = raw_img[:,:,0]
# Pick a 100x100 patch as a crop
crop = raw_img[850:950,440:540]

cv2.imwrite('/home/mot/tmp/deblur_test/test-img.png', raw_img)
# cv2.imwrite('test-crop.png', crop)

#     ---- Look for correct kernel size and std -----     #
# n = 25
# m = 25
# h = crop.shape[0]
# w = crop.shape[1]

# output = np.zeros((n*h, m*w))

# kernel_sizes = np.linspace(1,25,n)
# kernel_stds = np.linspace(0.01,5,m)
# # Rows (change the kernel size)
# for i in range(n):
#     # Columns (change the kernel standard deviation)
#     for j in range(m):
#         kernel = gkern(kernel_sizes[i],kernel_stds[j])
#         deconv = kevs_richardson_lucy(crop, kernel, 5, False)
#         deconv = clip(deconv)
#         # Add the image to the "collage"
#         output[i*h:i*h+h, j*w:j*w+w] = deconv
#         # Print the input parameters
#         print("i:",i,"j:",j,kernel_sizes[i],kernel_stds[j])
# cv2.imwrite('test-output-kernel.png', output)


#     ---- Best kernel values when eye-balling -----     #
kernel_size = 7.0
kernel_std = 1.0495833333333333

kernel_size = 7.0
kernel_std = 0.8

#     ----- Look for correct iterations -----     #

# n = 50
# h = crop.shape[0]
# w = crop.shape[1]
# output = np.zeros((n*h, w))

# for i in range(n):    
#     kernel = gkern(kernel_size,kernel_std)
#     iters = i
#     deconv = restoration.richardson_lucy(crop, kernel, iters, False)
#     deconv = clip(deconv)
#     output[i*h:i*h+h, :] = deconv
#     print("i:",i, iters)

# cv2.imwrite('test-output-iters.png', output)

#     ---- Best iteration value when eye-balling -----     #
iters = 15

#     ---- Try on the full frame -----     #
kernel = gkern(kernel_size,kernel_std)
deconv = kevs_richardson_lucy(raw_img, kernel, iters, False)

cv2.imwrite('/home/mot/tmp/deblur_test/test-deconv.png', deconv)












