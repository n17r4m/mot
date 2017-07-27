#------------------------------------------------------------------------------#
#                                                                              #
#  A detection  example                                                        #
#  python ex-detection.py                                                      #
#                                                                              #
#------------------------------------------------------------------------------#
import cv2
import os

from util.FrameGrabber import FrameGrabber
from util.Normalizer import Normalizer
from util.BinaryExtractor import BinaryExtractor
from util.ComponentExtractor import ComponentExtractor
from util.DataBag import DataBag

def main():
    # Destroy previous results if they exist
    if os.path.isfile("/local/scratch/mot/data/bags/validation/val1_detectionExample.db"):
        os.remove("/local/scratch/mot/data/bags/validation/val1_detectionExample.db")

    # Load in a pre-computed background (see ex-backgroundExtraction to compute)
    background = cv2.imread('/local/scratch/mot/data/backgrounds/validation/val1_background.png',
                            cv2.IMREAD_GRAYSCALE)

    # Init a frame grabber with the video
    frameGrabber = FrameGrabber('/local/scratch/mot/data/videos/validation/val1.avi')

    # Init the foreground extractor with a background model
    normalizer = Normalizer()

    # Init the binary extractor, setting the threshold hyperparameter
    #  note that we invert the image s.t. the droplets are high-valued
    #  and the background is low-valued
    bin_ext = BinaryExtractor(invert=True, threshold=215)

    # Create a databag to store the detection results
    bag = DataBag("/local/scratch/mot/data/bags/validation/val1_detectionExample.db")

    # Init a component extractor, passing in a databag.
    # Note that we can optionally save the computed binary image
    #  in the databag for later retreival
    comp_ext = ComponentExtractor(bag)


    # Manual inspection video
    import numpy as np
    shape = background.shape[1] * 3, background.shape[0]
    vw = cv2.VideoWriter('/local/scratch/mot/data/videos/validation/val1_inspection.avi',
                         frameGrabber.fourcc,
                         frameGrabber.fps, 
                         shape)
    # End Manual inspection video


    N_frames = frameGrabber.frames

    for i in range(N_frames):
        # Get the frame
        frame = frameGrabber.frame(i, gray=True)

        # Enhance foreground
        frame_normalized = normalizer.normalizeFrame(background, frame)

        # Extract binary foreground
        frame_binarized = bin_ext.extract(frame_normalized)
        component_data = comp_ext.extract(i, frame_binarized, frame_normalized)
        
        # Save results to manual inspection video
        vw.write(np.concatenate([frame_binarized, frame_normalized, frame], axis=1))

    # Commit our changes to the database ###
    bag.commit()
    vw.release()

    # View the results
    print bag.query('select * from assoc LIMIT 10')

if __name__ == '__main__':
    main()