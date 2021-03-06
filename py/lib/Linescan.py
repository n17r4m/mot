

import numpy as np
from pathlib import Path
from PIL import Image
import pyvips

from skimage import data, io, filters
from scipy.ndimage.morphology import (
    binary_dilation,
    binary_erosion,
    binary_opening,
    binary_closing,
    grey_dilation,
    grey_erosion,
)
from skimage.morphology import opening, closing
from skimage.morphology import watershed, diamond
from skimage.segmentation import random_walker
from skimage.filters import (
    threshold_yen,
    threshold_otsu,
    threshold_triangle,
    threshold_mean,
    threshold_local,
)
from scipy.ndimage.measurements import watershed_ift
from skimage.feature import peak_local_max
from scipy import ndimage
from skimage import measure, exposure

from mpyx import EZ, As, F, Iter, Seq, Stamp, Data

import time
import os


import tensorflow as tf


from matplotlib import pyplot as plt


class Datagram(Data):

    def tmp_dir(self):
        return "/tmp/mot/"


class LinescanSegment(Data):
    pass


class LoadLinescanSegment(F):

    def format_to_dtype(self, img_format):

        return {
            "uchar": np.uint8,
            "char": np.int8,
            "ushort": np.uint16,
            "short": np.int16,
            "uint": np.uint32,
            "int": np.int32,
            "float": np.float32,
            "double": np.float64,
            "complex": np.complex64,
            "dpcomplex": np.complex128,
        }[img_format]

    def setup(self, crop=48, debug=False, env=None, device="/gpu:0"):
        self.crop = crop
        self.width = 4000
        self.height = 1000
        self.debug = debug
        self.device = device
        print("Linescan loader running on GPU", os.environ["CUDA_VISIBLE_DEVICES"])
        tf_config = tf.ConfigProto()
        tf_config.gpu_options.allow_growth = True
        tf.enable_eager_execution(config=tf_config)

    def do(self, filename_pair):

        with tf.device(self.device):

            _vis = pyvips.Image.new_from_file(
                str(filename_pair[0]), access="sequential"
            ).crop(self.crop, 0, self.width, self.height)
            vis = (
                np.ndarray(
                    buffer=_vis.write_to_memory(),
                    dtype=self.format_to_dtype(_vis.format),
                    shape=[_vis.height, _vis.width, _vis.bands],
                ).astype("float64")
                / 255.0
            )

            _nir = (
                pyvips.Image.new_from_file(str(filename_pair[0]), access="sequential")
                .extract_band(0)
                .crop(self.crop, 0, self.width, self.height)
            )
            nir = (
                np.ndarray(
                    buffer=_nir.write_to_memory(),
                    dtype=self.format_to_dtype(_nir.format),
                    shape=[_nir.height, _nir.width, _nir.bands],
                ).astype("float64")
                / 255.0
            ).squeeze()

            # todo : add noise to reduce quatization artifacts (+/- 1/255)
            # todo : compare tensorflow performance to libvips for image ops

            """
            vis = np.array(Image.open(filename_pair[0]), dtype="float64")[
                :, self.crop : -self.crop, :
            ]
            nir = np.array(Image.open(filename_pair[1]), dtype="float64")[
                :, self.crop : -self.crop, np.newaxis
            ][:, :, 0]
            """

            print("vis", np.min(vis), np.max(vis))
            print("nir", np.min(nir), np.max(nir))

            im = tf.stack(
                [nir, tf.divide(tf.add(vis[:, :, 0], vis[:, :, 1]), 2.0), vis[:, :, 2]],
                axis=2,
            )

            bg = tf.expand_dims(tf.reduce_mean(im, axis=0), 0)

            dv = tf.square(tf.divide(im, tf.add(bg, 0.00001)))

            # mask regions blown to >= 1
            # normalize and invert these areas

            dv = tf.subtract(
                1.0,
                tf.where(
                    tf.greater(dv, 1.0),
                    tf.subtract(
                        1.0,
                        tf.divide(
                            tf.subtract(dv, 1.0), tf.subtract(tf.reduce_max(dv), 1.0)
                        ),
                    ),
                    dv,
                ),
            )

            # merge channels
            mk = tf.square(tf.divide(tf.reduce_sum(dv, axis=2), 3.0))

            # first (coarse) threshold
            th = 0.1  # threshold_yen(mk.numpy())
            mk = tf.tile(tf.expand_dims(tf.greater(mk, th), -1), [1, 1, 3])
            mk = binary_dilation(mk, iterations=3)

            # pass 2 - better background estimation

            bg = masked_mean(im, tf.subtract(1.0, mk))

            dv = tf.square(tf.divide(im, tf.add(bg, 0.00001)))

            dv = tf.subtract(
                1.0,
                tf.where(
                    tf.greater(dv, 1.0),
                    tf.subtract(
                        1.0,
                        tf.divide(
                            tf.subtract(dv, 1.0), tf.subtract(tf.reduce_max(dv), 1.0)
                        ),
                    ),
                    dv,
                ),
            )

            # second (fine) threshold
            mk = tf.square(tf.divide(tf.reduce_sum(dv, axis=2), 3.0))
            th = 0.05  # threshold_yen(mk.numpy())
            mk = tf.greater(mk, th)

            # mk = binary_opening(binary_closing(mk.numpy()))

            # normalize for uint8 RGB

            vis = tf.multiply(vis, 255.0)
            nir = tf.multiply(nir, 255.0)
            im = tf.multiply(im, 255.0)
            dv = tf.multiply(dv, 255.0)

            lss = LinescanSegment()
            lss.save("vis", vis.numpy().astype("uint8"))
            lss.save("nir", nir.numpy().astype("uint8"))
            lss.save("im", im.numpy().astype("uint8"))
            lss.save("dv", dv.numpy().astype("uint8"))
            lss.save("mk", mk)

            self.put((lss, th))


def masked_mean(T, m):
    m = tf.cast(m, tf.float64)
    t = tf.reduce_sum(tf.multiply(T, m), axis=0)
    s = tf.add(tf.reduce_sum(m, axis=0), 0.00001)
    return tf.divide(t, s)


def tf_closing(T):
    kern = [[1, 1], [1, 1]]
    eroded = tf.nn.erosion2d(T, kern, [1, 1, 1, 1], [1, 1, 1, 1], "SAME")


class Linescan2:
    # powered by tensorflow
    NIR_GLOB = "LS.NIR*.tif"
    VIS_GLOB = "LS.VIS*.tif"

    def __init__(self, path, crop=48, debug=False):

        p = Path(path)
        self.crop = crop
        self.debug = debug

        vis_files = list(sorted(p.glob(self.VIS_GLOB)))
        nir_files = list(sorted(p.glob(self.NIR_GLOB)))

        if debug:  # - decrese data size # approx 100000 tall slice from center of LS
            vis_files = vis_files[100:110]
            nir_files = nir_files[100:110]

        if len(nir_files) != len(vis_files):
            raise RuntimeError(
                "Number of NIR files does not equal number of VIS files in target directory"
            )

        paired = list(zip(vis_files, nir_files))

        self.vis = []
        self.nir = []
        self.im = []
        self.dv = []
        self.mk = []
        self.th = []

        start = time.time()
        very_start = start

        for segment in EZ(
            Iter(paired),
            Seq(
                tuple(
                    (
                        LoadLinescanSegment(
                            self.crop,
                            self.debug,
                            env={"CUDA_VISIBLE_DEVICES": str(1 + (i % 3))},
                        )
                        for i in range(20)
                    )
                ),
                Stamp(),
            ),
        ).items():

            # todo: imshow on debug

            self.vis.append(segment[0].load("vis"))
            self.nir.append(segment[0].load("nir"))
            self.im.append(segment[0].load("im"))
            self.dv.append(segment[0].load("dv"))
            self.mk.append(segment[0].load("mk"))
            self.th.append(segment[1])
            segment[0].clean()

        print("loaded in", time.time() - start, "seconds")
        start = time.time()

        self.vis = np.concatenate(self.vis)
        self.nir = np.concatenate(self.nir)
        self.im = np.concatenate(self.im)
        self.dv = np.concatenate(self.dv)
        self.mk = np.concatenate(self.mk)
        self.th = np.array(self.th)

        print("concat took", time.time() - start, "seconds")

        start = time.time()
        self.mk = closing(self.mk).astype("bool")
        print("morphology took", time.time() - start, "seconds")

        start = time.time()
        self.labels = measure.label(self.mk, background=0)
        print("labels took", time.time() - start, "seconds")

        start = time.time()
        self.props = measure.regionprops(self.labels, self.im[:, :, 0])
        print("props took", time.time() - start, "seconds")

        print("total time", time.time() - very_start)


"""
class Linescan:
    # powered by numpy
    NIR_GLOB = "LS.NIR*.tif"
    VIS_GLOB = "LS.VIS*.tif"

    def __init__(self, path, crop=48, debug=False):

        p = Path(path)

        vis_files = list(sorted(p.glob(self.VIS_GLOB)))
        nir_files = list(sorted(p.glob(self.NIR_GLOB)))

        if debug:  # - decrese data size # approx 100000 tall slice from center of LS
            vis_files = vis_files[100:110]
            nir_files = nir_files[100:110]

        if len(nir_files) != len(vis_files):
            raise RuntimeError(
                "Number of NIR files does not equal number of VIS files in target directory"
            )

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
            vis = np.array(Image.open(filename_pair[0]), dtype="float64")[
                :, crop:-crop, :
            ]
            nir = np.array(Image.open(filename_pair[1]), dtype="float64")[
                :, crop:-crop, np.newaxis
            ][:, :, 0]

            
            # print("R pre", np.min(vis[:,:,0]), np.max(vis[:,:,0]))
            # print("G pre", np.min(vis[:,:,1]), np.max(vis[:,:,1]))
            # print("B pre", np.min(vis[:,:,2]), np.max(vis[:,:,2]))    
            

            im = vis.copy()
            # visible light RGB gets compressed into to green/blue space
            # blue has some unique differentations,/.?
            # im[:,:,2] = (vis[:,:,1] + vis[:,:,2]) / 2.0
            im[:, :, 1] = (vis[:, :, 0] + vis[:, :, 1]) / 2.0

            # Near infrared gets placed on the "red" channel
            im[:, :, 0] = nir

            # normalize to 0-1
            # todo: assert im > 1
            im = im / 255.

            # Find the background-line (1 px tall by n px wide)
            bg = np.median(im, axis=0)[np.newaxis, :, :] + 0.00001

            # divide out the background and gamma correct
            dv = (im / bg) ** 3

            # mask regions blown to >= 1
            m = dv > 1
            dv2 = dv.copy()

            # normalize and invert these areas
            dv2[m] = 1.0 - (
                (dv2[m] - np.min(dv2[m])) / (np.max(dv2[m]) - np.min(dv2[m]))
            )

            # maybe something else or more fancy tech <- here,

            # create mask
            mk = 1.0 - dv2

            # mk = np.zeros(dv2.shape, dtype="float64")
            # mk[dv2 < 0.9] = 1.0 - dv2[dv2 < 0.9]

            # print("mk stats", np.min(mk), np.mean(mk), np.median(mk), np.max(mk))

            # merge channels
            mk2 = (np.sum(mk, axis=2) / 3.0) ** 2.0

            # print("mk2 stats", np.min(mk2), np.mean(mk2), np.median(mk2), np.max(mk2))

            mk2 = mk2 > threshold_yen(mk2)
            # mk2[mk2 > 0.375] = 1
            # mk2[mk2 < 0.375] = 0

            dv3 = dv2  # hacky

            ##############
            # pass 2 - better background estimation
            ##############

            im2 = im.copy()
            im2[mk2] = (mk2[:, :, np.newaxis] * bg)[mk2]

            # b = (1 ^ mk2).astype("bool")

            # sol1
            # im2[b] = (b*bg)[b]

            # for r, row in enumerate(im2):
            #     row[b[r]] = bg[:, b[r]]

            bg = np.median(im2, axis=0)[np.newaxis, :, :] + 0.00001

            dv = (im / bg) ** 3

            # mask regions blown to >= 1
            m = dv > 1
            dv2 = dv.copy()

            # normalize and invert these areas
            dv2[m] = 1.0 - (
                (dv2[m] - np.min(dv2[m])) / (np.max(dv2[m]) - np.min(dv2[m]))
            )

            # maybe something else or more fancy tech <- here,

            # create mask
            mk = 1.0 - dv2

            # mk = np.zeros(dv2.shape, dtype="float64")
            # mk[dv2 < 0.9] = 1.0 - dv2[dv2 < 0.9]

            # print("mk stats", np.min(mk), np.mean(mk), np.median(mk), np.max(mk))

            # merge channels
            mk2 = (np.sum(mk, axis=2) / 3.0) ** 2.0

            # print("mk2 stats", np.min(mk2), np.mean(mk2), np.median(mk2), np.max(mk2))

            mk2 = mk2 > threshold_yen(mk2)
            # mk2[mk2 > 0.375] = 1
            # mk2[mk2 < 0.375] = 0

            dv3 = dv2  # hacky

            # return (im, bg, dv, mk, mk2) #, markers)
            return (
                vis.astype("uint8"),
                nir.astype("uint8"),
                (im * 255).astype("uint8"),
                (dv3 * 255).astype("uint8"),
                (mk * 255).astype("uint8"),
                mk2.astype("bool"),
            )

        start = time.time()
        very_start = start

        for part in EZ(
            Iter(paired),
            Seq(
                (
                    load_n_combine,
                    load_n_combine,
                    load_n_combine,
                    load_n_combine,
                    load_n_combine,
                    load_n_combine,
                    load_n_combine,
                    load_n_combine,
                    load_n_combine,
                    load_n_combine,
                    load_n_combine,
                    load_n_combine,
                    load_n_combine,
                    load_n_combine,
                    load_n_combine,
                    load_n_combine,
                ),
                Stamp(),
            ),
        ).items():

            self.vis.append(part[0])
            self.nir.append(part[1])

            self.im.append(part[2])

            # self.dv2.append(part[1])
            self.dv3.append(part[3])
            self.mk.append(part[4])
            self.mk2.append(part[5])

        print("loading took", time.time() - start, "seconds")

        start = time.time()

        self.vis = np.concatenate(self.vis)
        self.nir = np.concatenate(self.nir)
        self.im = np.concatenate(self.im)
        # self.bg = np.concatenate(self.bg)
        # self.dv = np.concatenate(self.dv)
        # self.dv2 = np.concatenate(self.dv2)
        self.dv3 = np.concatenate(self.dv3)

        self.mk = np.concatenate(self.mk)
        self.mk2 = np.concatenate(self.mk2)
        print("concat took", time.time() - start, "seconds")

        start = time.time()
        
        # self.mk2 = np.array(
        #     binary_dilation(
        #     binary_erosion(    self.mk2, iterations=5), 
        #                                  iterations=5)
        #     , dtype='bool')
        
        # self.mk2 = self.mk2.astype('bool')
        self.mk2 = binary_erosion(opening(self.mk2))

        print("morphology took", time.time() - start, "seconds")

        start = time.time()
        self.labels = measure.label(self.mk2, background=0)

        print("labels took", time.time() - start, "seconds")

        start = time.time()
        self.props = measure.regionprops(self.labels, self.im[:, :, 0])

        print("props took", time.time() - start, "seconds")

        print("total time", time.time() - very_start)


def equalize(f):
    # doesn't work very well..
    h = np.histogram(f, bins=np.arange(256))[0]
    H = np.cumsum(h) / float(np.sum(h))
    e = np.floor(H[f.flatten().astype("int")] * 255.).astype("uint8")
    return e.reshape(f.shape)


"""


# NumPy / SciPy Recipes for Image Processing: Intensity Normalization and Histogram Equalization (PDF Download Available). Available from: https://www.researchgate.net/publication/281118372_NumPy_SciPy_Recipes_for_Image_Processing_Intensity_Normalization_and_Histogram_Equalization [accessed Mar 02 2018].


# a few utilities to deal with reading in crops

import re
import random


def getrandcrops(crop_dir_list, resized=True):

    crops = []

    for crop_dir in crop_dir_list:
        crop_list = []
        for crop_file in Path(crop_dir).glob("*.png"):
            crop_list.append(os.path.join(crop_dir, crop_file))
        crops.append(crop_list)

    while True:

        idx = random.randrange(0, len(crops))
        crop = readcrop(random.choice(crops[idx]))
        yield idx, crop


def getcrops(crop_dir, resized=True):
    p = Path(crop_dir).glob("*.png")
    for f in p:
        yield readcrop(os.path.join(crop_dir, f), resized)


def cropsize(filename):
    return int(
        re.search(
            "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-(\d*)\.png",
            filename,
        ).group(1)
    )


def readcrop(filename, resized=True):

    crop = np.array(Image.open(filename), dtype="float64")
    s = 64
    w, h = cropsize(filename), len(crop) - s

    if resized:
        im = crop[0:s, 0:s]
        dv = crop[0:s, s : s * 2]
        mk = crop[0:s, s * 2 :]
        return im, dv, mk
    else:
        im = crop[s:, 0:w]
        dv = crop[s:, w:]
        return im, dv
