import numpy as np
from uuid import UUID, uuid4
from lib.Database import Database


from lib.util.store_args import store_args
from math import floor, ceil
import multiprocessing as mp
import itertools as it
import traceback
import config 
import matplotlib.pyplot as plt
import asyncio
from mpyx.Compress import VideoStream
# from mpyx.Process import F
from mpyx.F import F
from skimage.filters import threshold_otsu as threshold
from skimage.filters import gaussian as blur

import os

csize  = config.crop_size
csize2 = csize // 2



class FrameIter(F):
    @store_args
    def setup(self, experiment_uuid = UUID("00000000-0000-4000-0000-000000000000")):
        print("1",experiment_uuid)
        self.experiment_uuid = experiment_uuid
        self.async(self.db_frames(self.experiment_uuid))
        
    async def db_frames(self, experiment_uuid):
        async for frame in Database().query("SELECT * FROM Frame WHERE experiment = $1 ORDER BY number", self.experiment_uuid):
            self.put(dict(frame))
    
        


class OLDFrameIter(F):
    @store_args                       
    def setup(self, experiment_uuid = UUID("00000000-0000-4000-0000-000000000000")):
        self.async(self.db_frames(experiment_uuid))
        
    async def db_frames(self, experiment_uuid):
        async for frame in Database().query("SELECT * FROM Frame WHERE experiment = $1 ORDER BY number", self.experiment_uuid):
            self.push(dict(frame))
            

class VisFrame(F):
    @store_args
    def setup(self, bg = np.ones((1729, 2336)), env=None):
        from lib.models.Classifier import Classifier
        self.CC = Classifier().load()
        self.height, self.width = bg.shape
        self.db = Database()
        
    def do(self, frame):
        self.async(self.vis_frame(frame))
        
    async def vis_frame(self, frame):
        
        latents = []
        locations = []
        print('test:',frame)
        # frame=frame[1]
        s = "SELECT location, latent from Track LEFT JOIN Particle USING(particle) WHERE frame = '{frame}'"
        q = s.format(frame=str(frame["frame"]))
        async for particle in self.db.query(q):
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
        
        self.put(frame_data)
        
    def rect(self, location, w = csize, h = csize):
        x, y = location
        y1, y2, x1, x2 = y, y + csize, x, x + csize
        return [int(round(z)) for z in [y1, y2, x1, x2]]

class OLDVisFrame(F):
    @store_args
    def setup(self, bg = np.ones((1729, 2336))):
        from lib.models.Classifier import Classifier
        self.CC = Classifier().load()
        self.height, self.width = bg.shape
        self.loop = asyncio.new_event_loop()
        self.db = Database()
        
    def do(self, frame):
        self.async(self.vis_frame(frame))
        
    async def vis_frame(self, frame):
        
        latents = []
        locations = []
        # print('test:',frame)
        # frame=frame[1]
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
    

