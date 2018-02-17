
from mpyx import EZ, As, By, F
from mpyx import Serial, Parallel, Broadcast, S, P, B
from mpyx import Iter, Const, Print, Stamp, Map, Filter, Batch, Seq, Zip, Read, Write

from mpyx.Vid import FFmpeg, BG

import numpy as np


print("Background modelling!")




import cv2

class BGPlayer(F):
    def do(self, frame_bg):
        cv2.imshow("bg", frame_bg["bg"])
        cv2.waitKey(1)
        self.put(frame_bg)


class VideoPlayer(F):
    def do(self, frame):
        cv2.imshow("frame", frame)
        cv2.waitKey(1)
        self.put(frame)


class FrameDivider(F):
    def do(self, frame_bg):
        div_frame = (255 * (frame_bg["frame"] / frame_bg["bg"]).clip(0, 1)).astype('uint8')
        self.put(div_frame)

class FrameSubtractor(F):
    def do(self, frame_bg):
        #sub_frame = (frame_bg["frame"].astype('float32') - frame_bg["bg"].astype('float32')).clip(0,255).astype('uint8')
        sub_frame = np.float64(255 - (np.absolute(np.int16(frame_bg["frame"])-np.int16(frame_bg["bg"]))))
        
        sub_frame -= sub_frame.min()
        sub_frame *= 255.0/sub_frame.max()
        
        
        self.put(np.uint8(sub_frame))




scaleby = 1
#w, h = int(2336/scaleby), int(1729/scaleby)
w, h = int(1920/scaleby), int(1080/scaleby)



#vid = "../data/source/BU-2015-10-14/T02578.avi"
#vid = "../data/experiments/a5f4681c-9e28-4a49-a370-ccadf6d47ef1/raw.mp4"
vid = "/home/datasets/mot17/train/MOT17-02-DPM/img1/video.mp4"



EZ(
    FFmpeg(vid, "-ss 0", (h, w,3), "-vf scale={}:{}".format(w,h)),
    Seq(As(6, BG, model='splitmedian', window_size=20, img_shape=(h, w,3))),
    #Seq(tuple(BG(model='ae', window_size=15, img_shape=(h, w,3), env={"CUDA_VISIBLE_DEVICES":str(i)}) for i in range(4))),
    
    BGPlayer(),
    #Seq(As(2, FrameSubtractor)),
    Seq(As(2, FrameDivider)),
    #Seq(As(16, F)),
    VideoPlayer(),
    FFmpeg((h, w, 3), [], "../data/ae_bg/b2d.avi", "-c:v libx264 -preset slow -crf 17", "-y"),
    Stamp()
).daemonize().watch().start().join()
