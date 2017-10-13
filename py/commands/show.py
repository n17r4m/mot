
from skimage import io
from lib.Database import Database
from base64 import b64decode
from PIL import Image
from io import BytesIO
import numpy as np
import matplotlib.pyplot as plt
import io

async def main(args):
    
    if len(args) == 0: print("What you want to show? [frame]")
        
    else:
        if   args[0] == "frame":      await show_frame(args[1:])
        else:                         print("Invalid show sub-command")


async def show_frame(args):
    
    if len(args) < 2: print("Please supply \"experiment frame_number\"")
    else:
        db = Database()
        experiment = args[0]
        frame_number = int(args[1])
        
        async for record in db.query("""
            SELECT image, data, shape, dtype 
            FROM Image
            LEFT JOIN Frame USING (image)
            LEFT JOIN Experiment USING (experiment)
            WHERE experiment = $1 AND Frame.number = $2""", experiment, frame_number):
            
            
            print("Found", record["image"], record["shape"], record["dtype"])
            
            im = Image.open(BytesIO(b64decode(record["data"])))
            im = np.asarray(im, dtype=record["dtype"])
            plt.gray()
            plt.imshow(im.squeeze())
            plt.show()
