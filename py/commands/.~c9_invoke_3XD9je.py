
from skvideo import io
from skimage.transform import downscale_local_mean
from skimage.io.imshow
from lib.Video import Video
from lib.Database import Database
from lib.Background import Background
from dateutil.parser import parse as dateparse
from base64 import b64encode

import numpy as np
import asyncio
import uuid
import tempfile
import os

async def main(args):
    
    if len(args) == 0: 
        print("What you want to insert?")
        print("USING: path/to/video/file.avi 2017-03-24 'experiment name' 'notes notes notes'")
    else:
        print(await insert_video(*args))


async def insert_video(video, date, name, notes):
    
    video = Video(video)
    db = Database()
    loop = asyncio.get_event_loop()
    
    (fp, tmp_vid_file) = tempfile.mkstemp(); os.close(fp)
    
    qres_video = []
    
    experiment = (uuid.uuid4(), dateparse(date), name, notes)
    
    await db.execute("""
        INSERT INTO Experiment (experiment, day, name, notes) 
        VALUES ($1, $2, $3, $4)
        """, *experiment)
    
    background = Background(video)
    
    
    for frame_number in range(video.frames):
        
        frame = background.normalize(video.frame(frame_number))
        
        imshow(frame.)
        
        print(np.max(frame), np.max(background))
        
        qres_video.append(downscale_local_mean(frame.squeeze(), (4,4)))
        
        
        
        image = (uuid.uuid4(), b64encode(frame.tobytes()).decode('ascii'), frame.shape, str(frame.dtype))
        t1 = db.execute("""
            INSERT INTO Image (image, data, shape, dtype)
            VALUES ($1, $2, $3, $4)
            """, *image)
        
        t2 = db.execute("""
            INSERT INTO Frame (frame, experiment, number, image)
            VALUES ($1, $2, $3, $4)
            """, uuid.uuid4(), experiment[0], frame_number, image[0])
        
        print(frame_number, round(float(frame_number)/float(video.frames) * 100.0, 1), "%")
        #await asyncio.gather(t1, t2)
    
    qres_shape = qres_video[0].shape
    io.vwrite(tmp_vid_file, np.array(qres_video), outputdict={'-vcodec': 'libx264'})
    
    
    with open(tmp_vid_file, 'rb') as qres_video:
        video = (uuid.uuid4(), b4encode(qres_video.read()).decode('ascii'), qres_shape)
        
        await db.execute("""
            INSERT INTO Video (video, data, shape, mime)
            VALUES ($1, $2, $3, $4)
            """, *video)
    
    os.remove(tmp_vid_file)
    
    return experiment[0]

