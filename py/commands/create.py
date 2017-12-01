'''
Create will take raw data (external 
or within experiment dir), perform a function, and store
the result within the experiment dir.
- screen level 
    - resized frame
    - engineered features
- track level
    - crops (currently detection does this)
- experiment level
    - detection video (currently draw is planned to do this)
    - tracking video (currently draw does this)


'''
import config
import os

from skimage.transform import resize
from skimage.io import imsave

from lib.Database import Database
from lib.Video import Video

import numpy as np

async def main(args):
    
    if len(args) == 0: print("What you want to create? [frame_resize]")
    else:
        if   args[0] == "frame_resize":     await frame_resize(args[1:])
        else:                               print("Invalid draw sub-command")



async def frame_resize(args):
    '''
    args: experiment_uuid size
    '''
    experiment_uuid = args[0]
    experiment_dir = os.path.join(config.experiment_dir, experiment_uuid)    
    # video_file = args[1]
    video_file = os.path.join(experiment_dir, "extraction.mp4")
    size = int(args[1])
    
    db = Database()
    
    print("Opening video file")
    gray = True
    video = Video(video_file, gray = gray)

    async for record in db.query("""
                                SELECT frame, number
                                FROM frame
                                WHERE experiment = $1
                                ORDER BY number
                                 """, experiment_uuid):
        # get the video frame
        if record["number"] and not record["number"]%10:
            print("Resizing frame", record["number"])
        # image = video.normal_frame(record["number"])
        image = video.frame(record["number"])

        # resize the image
        image = np.uint8(255*resize(image, (size, size)))
        if gray:
            image = np.squeeze(image)
        
        # store the image in the filesystem
        frameDir = os.path.join(config.experiment_dir, 
                            str(experiment_uuid), 
                            str(record["frame"])) 
        outfile = os.path.join(frameDir, str(size)+'x'+str(size)+'.png')
        
        if not os.path.exists(frameDir):
            os.mkdir(frameDir)
        imsave(outfile, image)

