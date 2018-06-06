'''
Look at crops from an experiment, given some property filters.

'''

import config
import numpy as np
import os
from os.path import isdir, isfile, join
from lib.Database import Database
import matplotlib.pyplot as plt
import shutil

async def main(args):
    await view_crops()
    
    
async def view_crops():
    directory = '/home/mot/tmp/C3_cropviewer_nonvalid'
    db = Database()
    
    plt.ion()
    
    experiment_uuid = 'b6e60b0d-ca63-4999-9f29-971b9178ad10'
    diameter_low = 200
    diameter_high = 700 
    
    area_low = ((diameter_low / (2.0 * 13.94736842)) ** 2) * np.pi
    area_high = ((diameter_high / (2.0 * 13.94736842)) ** 2) * np.pi
    
    
    s = """
    SELECT p.experiment, f.frame, t.track, p.area
    FROM particle p, frame f, track t 
    WHERE p.particle = t.particle 
    AND t.frame = f.frame
    AND f.experiment = p.experiment
    AND p.experiment = '{experiment_uuid}' 
    AND p.area > {area_low}
    AND p.area < {area_high}
    AND p.valid = True
    """
    q = s.format(
        experiment_uuid=experiment_uuid,
        area_low=area_low,
        area_high=area_high
    )
    
    async for result in db.query(q):
        diameter = (2.0 * np.sqrt(result["area"] / np.pi)) * 13.94736842
        
        # Do stuff with the rows
        # Make the filename
        srcFile = os.path.join(config.experiment_dir, 
                                   str(result["experiment"]),
                                   str(result["frame"]),
                                   str(result["track"])+'.jpg')
                                   
        dstFile = os.path.join(directory, str(round(diameter))+"-"+
                                          str(result["track"])+'.jpg')
        shutil.copyfile(srcFile, dstFile) 
                                   
        # load the file
        #img = plt.imread(srcFile)        
        
        # show the file
        #plt.imshow(img, cmap='gray')
        
        # waitfor user input
        #plt.waitforbuttonpress(0)
        
        #MSBOT-010160000003C4_VT
        #35e29212-a136-4083-91d1-42b96d0bf75e (detection) 
 	    #dd6b9512-cfcb-47e9-91eb-537bff1e6d3d (tracking)
 	    
