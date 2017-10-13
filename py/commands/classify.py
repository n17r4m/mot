
from skimage import io
from lib.Database import Database
from lib.Crop import Crop
from lib.models.Classifier import Classifier
from base64 import b64decode
import numpy as np
import io

async def main(args):
    
    if len(args) == 0:                print("No subcommand provided")
    else:
        if   args[0] == "saliency":   await dump_saliency_maps(args[1:])
        else:                         print("Invalid classify sub-command")


async def dump_saliency_maps(args):
    
    if len(args) < 2: print("Please supply \"experiment frame_number out_pattern\"")
    else:
        
        db = Database()
        experiment = args[0]
        frame_number = int(args[1])
        out_pattern = args[2] if len(args) > 2 else "saliency"
        
        
        async for record in db.query("""
            SELECT image, data, shape, dtype 
            FROM Image
            LEFT JOIN Frame USING (image)
            LEFT JOIN Experiment USING (experiment)
            WHERE experiment = $1 AND Frame.number = $2""", experiment, frame_number):
            
            
            print("Found frame", record["image"])
            
            im = np.fromstring(b64decode(record["data"]), record["dtype"]).reshape(record["shape"])
        
        print(im.shape)
        
        stride = 2
        size = 64
        cropper = Crop(im)
        
        for y in range(0, im.shape[0], stride):
            
            line = np.zeros(im.shape[1], size, size, im.shape[-1])
            
            for x in range(0, im.shape[1], stride):
            
                line[x] = cropper.crop(x, y, size, size)
                
                print(x, y, crop.shape)

            print (line.shape)