#!/usr/bin/python
import numpy as np
import cv2
from skimage import color, data, restoration

# Remap an input range, not used
def remap(x, lo=0, hi=255):
    out_rng = hi - lo
    in_rng = np.max(x) - np.min(x)
    return lo + ((x - np.min(x)) / in_rng) * out_rng


# I wrote my own clip, since I was working with images on range 0-255 not 0-1 like RL has
def clip(x):
    x[x > 255] = 255
    x[x < 0] = 0
    return x


def gkern(l=5, sig=1.):
    """
    creates gaussian kernel with side length l and a sigma of sig
    """
    ax = np.arange(-l // 2 + 1., l // 2 + 1.)
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-(xx ** 2 + yy ** 2) / (2. * sig ** 2))

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
        x = convolve(im_deconv, psf, "same")
        np.place(x, x == 0, eps)
        relative_blur = image / x + eps
        # relative_blur = image / convolve_method(im_deconv, psf, 'same')
        im_deconv *= convolve(relative_blur, psf_mirror, "same")

    if clip:
        im_deconv[im_deconv > 1] = 1
        im_deconv[im_deconv < -1] = -1

    return im_deconv


#     ---- Read the input, convert to grayscale, make a small sample for testing -----     #

#experiment_path = "/home/mot/data/results/Glass.Bead.Tests/200.to.300.um/LineScan01034/"
experiment_path = "/home/mot/data/results/Bitumen, Test Sand and Water/LineScan01155/"


raw_im = cv2.imread(experiment_path + "image.png").astype("float64")
raw_dv = cv2.imread(experiment_path + "divided.png").astype("float64")
raw_mk = cv2.imread(experiment_path + "mask.png").astype("float64")


cv2.imwrite("/home/mot/tmp/deblur_ls_test/test-im.png", raw_im)
cv2.imwrite("/home/mot/tmp/deblur_ls_test/test-im0.png", raw_im[:, :, 0])
cv2.imwrite("/home/mot/tmp/deblur_ls_test/test-im1.png", raw_im[:, :, 1])
cv2.imwrite("/home/mot/tmp/deblur_ls_test/test-im2.png", raw_im[:, :, 2])
cv2.imwrite("/home/mot/tmp/deblur_ls_test/test-dv.png", raw_dv)
cv2.imwrite("/home/mot/tmp/deblur_ls_test/test-dv0.png", raw_dv[:, :, 0])
cv2.imwrite("/home/mot/tmp/deblur_ls_test/test-dv1.png", raw_dv[:, :, 1])
cv2.imwrite("/home/mot/tmp/deblur_ls_test/test-dv2.png", raw_dv[:, :, 2])
cv2.imwrite("/home/mot/tmp/deblur_ls_test/test-mk.png", raw_mk)


#     ---- Best kernel values when eye-balling -----     #

kernel_size = 9.0
kernel_std = 1.5
kernel_boost = 5


iters = 30


kernel = gkern(kernel_size, kernel_std) * kernel_boost

cv2.imshow("kernel", kernel)
cv2.waitKey(2000)

deconv = np.zeros(raw_im.shape)
target = raw_dv

print("Deconvolving channels")
deconv[:, :, 0] = kevs_richardson_lucy(target[:, :, 0], kernel, iters, False)
print("1 done")
deconv[:, :, 1] = kevs_richardson_lucy(target[:, :, 1], kernel, iters, False)
print("2 done")
deconv[:, :, 2] = kevs_richardson_lucy(target[:, :, 2], kernel, iters, False)
print("All done.")

cv2.imwrite("/home/mot/tmp/deblur_ls_test/test-deconv.png", deconv)
cv2.imwrite("/home/mot/tmp/deblur_ls_test/test-deconv0.png", deconv[:, :, 0])
cv2.imwrite("/home/mot/tmp/deblur_ls_test/test-deconv1.png", deconv[:, :, 1])
cv2.imwrite("/home/mot/tmp/deblur_ls_test/test-deconv2.png", deconv[:, :, 2])
