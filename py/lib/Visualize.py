import numpy as np
from uuid import UUID, uuid4
from lib.Database import Database
from lib.Compress import VideoStream

from lib.util.store_args import store_args
from math import floor, ceil
import multiprocessing as mp
import itertools as it
import traceback
import config 
import matplotlib.pyplot as plt
import asyncio

from lib.Process import F
from skimage.filters import threshold_otsu as threshold
from skimage.filters import gaussian as blur

import os

csize  = config.crop_size
csize2 = csize // 2





class FrameIter(F):
    @store_args                       
    def setup(self, experiment_uuid = UUID("00000000-0000-4000-0000-000000000000")):
        self.async(self.db_frames(experiment_uuid))
        
    async def db_frames(self, experiment_uuid):
        async for frame in Database().query("SELECT * FROM Frame WHERE experiment = $1 ORDER BY number", self.experiment_uuid):
            self.push(dict(frame))
            

class VisFrame(F):
    @store_args
    def setup(self, bg = np.ones((1729, 2336))):
        
        # Exec("env").into(Print()).start()
        
        self.height, self.width = bg.shape
        
        from lib.models.Classifier import Classifier
        self.CC = Classifier().load()
            
        self.loop = asyncio.new_event_loop()
        self.db = Database()
        
    
    def do(self, frame):
        self.async(self.vis_frame(frame))
        
    async def vis_frame(self, frame):
        
        latents = []
        locations = []

        frame=frame[1]
        async for particle in self.db.query("SELECT location, latent from Track LEFT JOIN Particle USING(particle) WHERE frame = $1", frame["frame"]):
            locations.append(particle["location"])
            latents.append([float(i) for i in particle["latent"][1:-1].split(',')])
            
        #todo: ensure maximum batchsize does not exceed capacity of GPU
        crops = self.CC.decoder.predict(np.array(latents))
        
        frame_data = np.ones((self.height + csize, self.width + csize))
        frame_data[csize2:-csize2, csize2:-csize2] = self.bg
        
        for particle in zip(locations, crops):
            y1, y2, x1, x2 = self.rect(particle[0])
            crop = self.CC.deproc(particle[1]) / 255.
            crop[crop > threshold(crop)] = 1
            crop = np.clip(crop.squeeze(), 0, 1)
            frame_data[y1:y2, x1:x2] *= blur(crop, 1)
        
        frame_data = np.clip((frame_data * 255.), 0, 255)[csize2:-csize2, csize2:-csize2].astype("uint8")
        
        self.push(frame_data)
        
    def rect(self, location, w = csize, h = csize):
        x, y = location
        y1, y2, x1, x2 = y, y + csize, x, x + csize
        return [int(round(z)) for z in [y1, y2, x1, x2]]
    




"""
class Visualize:
    @store_args
    def __init__(self, experiment_uuid = "Error", output_file = str(uuid4()) + ".mp4", width=2336, height=1729, fps=24.):
        self.db = Database()
        self.CC = Classifier().load()
        self.vs_queue = mp.Queue(10)
        self.VS = VideoStream(self.vs_queue, "./", output_file, width, height)
        self.VS.start()
        self.bg = imread("./bg.png", as_grey=True).astype("float64")
        self.bg /= 255.
        self.bg /= 255. #wtf..

    async def go(self):
        
        async for experiment in self.db.query("SELECT * FROM Experiment WHERE experiment = $1", UUID(self.experiment_uuid)):
            async for frame in self.db.query(
                print("Frame", frame["number"])
                await self.visFrame(experiment, frame)
        
        self.vs_queue.put(None)
        self.VS.join()
        return self.output_file

    async def visFrame(self, experiment, frame):
        frame_data = np.ones((self.height + csize, self.width + csize))
        frame_data[csize2:-csize2, csize2:-csize2] = self.bg.squeeze()
        
        
        latents = []
        locations = []
        async for particle in self.db.query("SELECT location, latent from Track LEFT JOIN Particle USING(particle) WHERE frame = $1", frame["frame"]):
            locations.append(particle["location"])
            latents.append([float(i) for i in particle["latent"][1:-1].split(',')])
            
        #todo: ensure maximum batchsize does not exceed capacity
        crops = self.CC.decoder.predict(np.array(latents))
        
        
        
        for particle in zip(locations, crops):
            y1, y2, x1, x2 = self.rect(particle[0])
            crop = self.CC.deproc(particle[1]) / 255.
            th = threshold(crop)
            crop[crop > th] = 1
            crop = np.clip(crop.squeeze(), 0, 1)
            
            frame_data[y1:y2, x1:x2] *= blur(crop, 1)
            
        print(np.min(crops), np.max(crops))
        print(np.min(frame_data), np.max(frame_data))
         
        
        
        frame_data = np.clip((frame_data * 255.), 0, 255)[csize2:-csize2, csize2:-csize2].astype("uint8")
        
        
        self.vs_queue.put(frame_data.tobytes())
        

    def rect(self, location, w = csize, h = csize):
        x, y = location
        y1, y2, x1, x2 = y, y + csize, x, x + csize
        return [int(round(z)) for z in [y1, y2, x1, x2]]


"""









""" OLD sprite painting
# Get sprite coordinates in the (f)rame and the (o)bject
fy1, fy2, fx1, fx2, oy1, oy2, ox1, ox2 = self.rect()
# We'll use the alpha channel as a mask for the blending
mask = np.float32(self.sprite[oy1:oy2, ox1:ox2, 3] / 255.0)
# ... first we'll expand the mask a little, then blur for smoother edges
mask = cv2.dilate(mask, (8,8))
mask = cv2.blur(mask, (8,8))

for c in range(0,3):
    bg = frame[fy1:fy2, fx1:fx2, c] * (1-mask)
    fg = frame[fy1:fy2, fx1:fx2, c] * (self.sprite[oy1:oy2, ox1:ox2, c]/255.0) * mask
    
    frame[fy1:fy2, fx1:fx2, c] = bg + fg
"""
