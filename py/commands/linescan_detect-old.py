
from lib.Linescan import Linescan
import numpy as np
import time
import os
from pathlib import Path

from skimage import data, io, filters
from scipy.ndimage.morphology import binary_dilation, binary_erosion, grey_dilation, grey_erosion
from skimage.morphology import watershed, diamond
from skimage.segmentation import random_walker
from scipy.ndimage.measurements import watershed_ift
from skimage.feature import peak_local_max
from skimage import measure

from scipy import ndimage

from scipy.misc import imresize

import cv2

from uuid import uuid4


from lib.Database import Database, DBWriter


"""
Note: currently modified to dump results to csv
"""


async def main(args):
    
    if len(args) < 2: 
        print("""path/to/linescan/data/ 2018-05-22 Name-of_experiment "Notes. Notes." /dump/to/dir""")
    else:
        print(await detect_linescan(*args))


# date, name = "Unknown", notes = "",
async def detect_linescan(path, dump_path=None, *args):


    # set up path related stuff
    
    if not os.path.isdir(path):
        raise ValueError("Directory {} not found".format(path))
    else:
        path = Path(path)
    
    if dump_path is None:
        raise ValueError("Data dump directory {} not found".format(dump_path))
    
    if not os.path.isdir(dump_path):
        try:
            os.makedirs(dump_path)
        except:
            raise ValueError("Data dump directory {} could not be created".format(dump_path))
    
    dump_path = Path(dump_path)
        
    

    #path = "/home/mot/data/source/Water and Test Sand/LineScan01069/"
    #path = "/home/mot/data/source/Water, Clay and Test Sand/LineScan01075/"
    #path = "/home/mot/data/source/Water, NaOH and Oil Sand/LineScan01111/"
    #path = "/home/mot/data/source/Bubbles-BU-2018-03-01/LineScan/LineScan01028/"
    #path = "/home/mot/data/source/Glass.Bead.Tests/425.to500.um/LineScan01014/"
    #path= "/home/mot/data/source/Glass.Bead.Tests/150.to.180.um/LineScan01029/"
    #path = "/home/mot/data/source/Glass.Bead.Tests/200.to.300.um/LineScan01034/"
    #path = "/home/mot/data/source/Glass.Bead.Tests/212.to.250.um/LineScan01038/"
    #path = "/home/mot/data/source/Glass.Bead.Tests/300.to.335.um/LineScan01036/"
    #path = "/home/mot/data/source/Bitumen and Water/LineScan01140/"
    #path = "/home/mot/data/source/Water and Test Sand/LineScan01070/"
    #path = "/home/mot/data/source/Water and Test Sand/LineScan01069/"
    #path = "/home/mot/data/source/Bitumen, Test Sand and Water/LineScan01146/"
    #path = "/home/mot/data/source/BU-2018-02-05/LineScan/LineScan01125/"
    #path = "/home/mot/data/source/BU-2018-02-05/LineScan/LineScan01126/"
    #path = "/home/mot/data/source/BU-2018-02-08/LineScan/LineScan01014/"
    



    # Load linescan data
    
    ls = Linescan(path, debug=False)
    print("loaded")
    start = time.time()
    
    #sy, ey = 400, 2000    # display sample height
    #sx, ex = 400, 2000   # display sample width
    #sy, ey, sx, ex = 101750, 104250, 1000, 1700
    #sy, ey, sx, ex = 200000, 202000, 500, 1800
    #sy, ey, sx, ex = 101750, 102250, 1000, 1700
    
    sy, ey, sx, ex = 176000, 180000, 0, 4000
    
    
    # some debug stuff
    
    vis = ls.vis[sy:ey, sx:ex]
    nir = ls.nir[sy:ey, sx:ex]
    im  = ls.im[sy:ey, sx:ex]
    
    #dv  = ls.dv[sy:ey, sx:ex]
    #dv2  = ls.dv2[sy:ey, sx:ex]
    dv3  = ls.dv3[sy:ey, sx:ex]
    
    #im[1000,:,:] = 0
    
    
    #dv  = ls.dv[sy:ey, sx:ex]
    mk = ls.mk[sy:ey, sx:ex]
    mk2 = ls.mk2[sy:ey, sx:ex]
    #labels = ls.labels[sy:ey, sx:ex]
    #props = ls.props
    
    
    #labels = watershed_ift((255.0 * mk2).astype("uint8"), mk2.astype('int'))#, mask=bit4)
    
    
    cv2.imwrite(str(dump_path / "visual.png"), vis)
    cv2.imwrite(str(dump_path / "nir.png"), nir)
    cv2.imwrite(str(dump_path / "im.png"), im)
    #cv2.imshow(str("divided2", dv2)
    cv2.imwrite(str(dump_path / "divided.png"), dv3)
    cv2.imwrite(str(dump_path / "pre-mask.png"), (mk).astype('uint8'))
    cv2.imwrite(str(dump_path / "mask.png"), (mk2*255.).astype('uint8'))
    #print(np.min(labels), np.max(labels))
    #cv2.imshow("labels", labels.astype('uint8'))
    
    #cv2.waitKey(0)
    
    
    """
    # TODO: dump stuff into the database, for now, we're happy to
    # just dump to data files for review by Mark.
    db = Database()
    tx = await db.transaction()
    """
    
    import matplotlib.pyplot as plt
    import matplotlib.colors as colors
    import math
    
    # Calculate summary statistics (pass 1)
    
    x = []
    areas_prop = []
    areas_circ = []
    eccentricities = []
    orientations = []
    solidities = []
    vels = []
    
    f_counts = np.zeros((math.ceil(len(ls.vis) / 1000)))
    count = 0
    
    
    
    for p in ls.props:
        
        bb = p.bbox
        h, w = bb[2] - bb[0], bb[3] - bb[1]
        
        if w >= 17.9:
            
            count += 1
            
            v = 7.797271 * 4000.0 * (w/h) / 1000000
             
            x.append(count)
            areas_prop.append(p.area)
            areas_circ.append(((w/2.0)**2)*3.14159)
            eccentricities.append(p.eccentricity)
            orientations.append(p.orientation)
            solidities.append(p.solidity)
            f_counts[math.floor(p.centroid[0]/1000)] += 1
            
            vels.append(v)
        
    
    x = np.array(x)
    areas_prop = np.array(areas_prop)
    areas_circ = np.array(areas_circ)
    eccentricities = np.array(eccentricities)
    orientations = np.array(orientations)
    solidities = np.array(solidities)
    vels = np.array(vels)
    
    filter_area_min = 1
    filter_area_max = 999999999
    
    
    mask = (areas_circ>filter_area_min) & (areas_circ<filter_area_max)
    n_str = str(np.count_nonzero(mask))
    
    # Generate some summary charts
    
    figsize, dpi = (7,5), 300
    
    areasp_fig, areasp_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    areasp_ax1.set_title(f"Areas (prop) n={n_str}")
    areasp_ax1.hist(areas_prop[mask], 50, (0, 6000))
    areasp_ax1.set_yscale('log')
    areasp_fig.savefig(dump_path / "area-prop-histogram.png")
    
    areasc_fig, areasc_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    areasc_ax1.set_title(f"Areas (circ) n={n_str}")
    areasc_ax1.hist(areas_circ[mask], 50, (0, 6000))
    areasc_ax1.set_yscale('log')
    areasc_fig.savefig(dump_path / "area-circ-histogram.png")
    
    
    eccen_fig, eccen_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    eccen_ax1.set_title(f"Eccentricities n={n_str}")
    eccen_ax1.hist(eccentricities[mask], 50, (0, 1))
    eccen_fig.savefig(dump_path / "eccentricities-histogram.png")
    
    orien_fig, orien_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    orien_ax1.set_title(f"Orientations n={n_str}")
    orien_ax1.hist(orientations[mask], 135, (-(np.pi/2), +(np.pi/2)))
    orien_fig.savefig(dump_path / "orientation-histogram.png")
    
    veloc_fig, veloc_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    veloc_ax1.set_title(f"Velocities n={n_str}")
    veloc_ax1.hist(vels[mask], 50, (0,0.1))
    veloc_fig.savefig(dump_path / "velocity-histogram.png")
    
    solid_fig, solid_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    solid_ax1.set_title(f"Solidities n={n_str}")
    solid_ax1.hist(solidities[mask], 50, (0,1))
    solid_ax1.set_yscale('log')
    solid_fig.savefig(dump_path / "solidity-histogram.png")
    
    count_fig, count_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    count_ax1.set_title(f"Particle Counts / Frame n={n_str}")
    count_ax1.plot(f_counts)
    count_fig.savefig(dump_path / "particle-counts.png")
    
    Ap_x_V_fig, Ap_x_V_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    Ap_x_V_ax1.set_title(f"Area (prop) / Velocites n={n_str}")
    Ap_x_V_ax1.hist2d(areas_prop[mask], vels[mask], 150, ((0,5000),(0,0.1)), norm=colors.LogNorm())
    Ap_x_V_fig.savefig(dump_path / "area-prop_x_velocity-histogram.png")
    
    Ac_x_V_fig, Ac_x_V_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    Ac_x_V_ax1.set_title(f"Area (circ) / Velocites n={n_str}")
    Ac_x_V_ax1.hist2d(areas_circ[mask], vels[mask], 150, ((0,5000),(0,0.1)), norm=colors.LogNorm())
    Ac_x_V_fig.savefig(dump_path / "area-circ_x_velocity-histogram.png")
    
    O_x_V_fig, O_x_V_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    O_x_V_ax1.set_title(f"Orientation / Velocites n={n_str}")
    O_x_V_ax1.hist2d(orientations[mask], vels[mask], 150, ((-1.8,1.8),(0,0.1)), norm=colors.LogNorm())
    O_x_V_fig.savefig(dump_path / "orientation_x_velocity-histogram.png")
    
    E_x_V_fig, E_x_V_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    E_x_V_ax1.set_title(f"Eccentricity / Velocites n={n_str}")
    E_x_V_ax1.hist2d(eccentricities[mask], vels[mask], 150, ((0,1),(0,0.1)), norm=colors.LogNorm())
    E_x_V_fig.savefig(dump_path / "eccentricity_x_velocity-histogram.png")
    
    
    E_x_O_fig, E_x_O_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    E_x_O_ax1.set_title(f"Orientation / Eccentricity n={n_str}")
    E_x_O_ax1.hist2d(orientations[mask], eccentricities[mask], 150, ((-1.8,1.8),(0,1)), norm=colors.LogNorm())
    E_x_O_fig.savefig(dump_path / "orientation_x_eccentricity-histogram.png")
    
    
    
    plt.subplot(231)
    plt.title(f"Eccentricities")
    plt.hist(eccentricities[mask], 50, (0, 1))
    plt.subplot(232)
    plt.title(f"Orientations n={n_str}")
    plt.hist(orientations[mask], 135, (-(np.pi/2), +(np.pi/2)))
    plt.subplot(233)
    plt.title(f"Velocities")
    plt.hist(vels[mask], 50, (0,0.1))
    
    plt.subplot(234)
    plt.title("Areas")
    plt.hist(areas_circ[mask], 50, (0, 4000))
    
    plt.subplot(235)
    plt.title("Areas/Vel")
    plt.hist2d(areas_circ[mask], vels[mask], 150, ((0,4000),(0,0.1)), norm=colors.LogNorm())
    
    plt.subplot(236)
    plt.title("Ecc/Or")
    plt.hist2d(orientations[mask], eccentricities[mask], 150, ((-1.8,1.8),(0,1)), norm=colors.LogNorm())
    
    plt.savefig(dump_path / "summary.png", bbox_inches='tight', dpi=300)
    
    # todo: figure with random examples collaged. (maybe show outliers too?)
    
    
    
    # Describe Particles (pass 2) 
    # Todo: see if it is worth combining pass 1 & 2
    
    with open(dump_path / "detections.csv", 'w') as detections:
        
        
        detections.write("Frame ID, Particle ID, Particle Area (prop), Particle Area (circ), Particle Velocity, Particle Intensity, Particle Perimeter, X Position, Y Position, Major Axis Length, Minor Axis Length, Orientation, Solidity, Eccentricity\n")
        
        
        print("Writing out", dump_path / "detections.csv")
        
        for p in ls.props:
            bb = p.bbox
            h, w = bb[2] - bb[0], bb[3] - bb[1]
            
            if w >= 17.9:
                
                uid = uuid4()
                frame = int(bb[0] / 1000.) + 1
                collage = collage_crops(ls, p)
                
                if not os.path.isdir(dump_path / "crops" / str(frame)):
                    os.makedirs(dump_path / "crops"  / str(frame))
                
                
                v = 7.797271 * 4000.0 * (w/h) / 1000000
                
                
                """
                # show crops...
                cv2.imshow("crop", collage)
                k = cv2.waitKey(1)
                if k == ord('x'):
                    break;
                """
                
                io.imsave(dump_path / "crops" / str(frame) / "{}-{}.png".format(uid, w), collage, "pil")
                
                
                #Frame ID, Particle ID, Particle Area (prop), Particle Area (circ), Particle Velocity, Particle Intensity, Particle Perimeter, X Position, Y Position, Major Axis Length, Minor Axis Length, Orientation, Solidity, Eccentricity.
                attrs = [frame, uid,    p.area, ((w/2.0)**2)*3.14159,       v,               p.mean_intensity,   p.perimeter,        p.centroid[1], p.centroid[0],   p.major_axis_length, p.minor_axis_length, p.orientation, p.solidity, p.eccentricity]
                
                
                csv_line = ",".join(list(map(str, attrs)) + ["\n"])
            
                detections.write(csv_line)
                
    print("All done")        
 
	
	
    
def collage_crops(ls, p):
    
    bb = p.bbox
    
    w, h = bb[3] - bb[1], bb[2] - bb[0]
    crop = np.zeros((64+h, max(w*2, 64*4), 3), dtype="uint8")
    
    div = ls.dv3[bb[0]:bb[2], bb[1]:bb[3]]
    div_r = imresize(div, size=(64,64))#, mode="bicubic")
    
    vis = ls.vis[bb[0]:bb[2], bb[1]:bb[3]]
    vis_r = imresize(vis, size=(64,64))
    
    nir = ls.nir[bb[0]:bb[2], bb[1]:bb[3]]
    nir_r = np.dstack([imresize(nir, size=(64,64))] * 3)
    
    mk2 = 255 * ls.mk2[bb[0]:bb[2], bb[1]:bb[3]]
    mk2_r = np.dstack([imresize(mk2, size=(64,64))] * 3)
    
    
    crop[0:64, 0:(64*4), :] = np.concatenate([vis_r, nir_r, div_r, mk2_r], axis=1)
    crop[64:(64+h), 0:w, :] = vis
    crop[64:(64+h), w:(w*2), :] = np.dstack([nir] * 3)
    
    return crop
    
    
    
    
    
    
    
    
    """
    with open("/home/martin/Pictures/ls_im.data", 'wb') as im:
        im.write(ls.im.tobytes())
    
    with open("/home/martin/Pictures/ls_bg.data", 'wb') as im:
        im.write(ls.bg.tobytes())
    
    with open("/home/martin/Pictures/ls_dv.data", 'wb') as im:
        im.write(ls.dv.tobytes())
    """
    
    
    """
    io.imsave("/home/martin/Pictures/ls_bg.png", ls.im, "imread")
    
    print("got im")
    
    io.imsave("/home/martin/Pictures/ls_bg.png", ls.bg, "imread")
    
    print("got bg")
    
    io.imsave("/home/martin/Pictures/ls_norm.png", ls.dv, "imread")
    
    print("got dv")
    """
    
    #cv2.imshow("title", ls.ls[:, :, 0:3].astype("float64"))
    #quickcv2.waitKey(0)
    
    """
    17312020 kB
    
    
    
    
    """
