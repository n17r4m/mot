
from lib.Linescan import Linescan2
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
        
    
    # Load linescan data
    
    ls = Linescan2(path, debug=False)
    print("loaded")
    start = time.time()
    
    sy, ey, sx, ex = 176000, 180000, 0, 4000
    
    im = ls.im[sy:ey, sx:ex]
    dv = ls.dv[sy:ey, sx:ex]
    mk = ls.mk[sy:ey, sx:ex]
    

    cv2.imwrite(str(dump_path / "image.png"), im)
    cv2.imwrite(str(dump_path / "divided.png"), dv)
    cv2.imwrite(str(dump_path / "mask.png"), (mk*255.).astype('uint8'))

    
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
    print("Collecting statistics")
    
    x = []
    areas_prop     = []
    areas_circ     = []
    diameters      = []
    eccentricities = []
    orientations   = []
    solidities     = []
    vels           = []
    
    LS_pixelCal = 7.797271
    LS_timeCal = 4000.
    
    f_counts = np.zeros((math.ceil(len(ls.im) / 1000)))
    count = 0
    
    
    
    for p in ls.props:
        
        bb = p.bbox
        h, w = bb[2] - bb[0], bb[3] - bb[1]
        
        if w >= 5.0:
            
            count += 1
            
            major, minor, orien = p.major_axis_length, p.minor_axis_length, p.orientation
            d = (major * minor) / np.sqrt( (minor*np.cos(orien))**2 + (major*np.sin(orien))**2 ) 
            d *= LS_pixelCal
            d += np.random.uniform(-LS_pixelCal/2., LS_pixelCal/2.)
            #note that we add a small amount of noise to prevent quantization artifacts
            v = ((LS_timeCal * (d/h) +  np.random.uniform(-LS_timeCal/2., LS_timeCal/2.)) / 1000000.0)
             
            x.append(count)
            areas_prop.append(p.area * 60.79321) # LS_pixelCal ** 2
            areas_circ.append(((d/2.0)**2)*np.pi + np.random.uniform(-np.pi/2., np.pi/2.))
            diameters.append(d)
            eccentricities.append(p.eccentricity)
            orientations.append(p.orientation)
            solidities.append(p.solidity)
            f_counts[math.floor(p.centroid[0]/1000)] += 1
            
            vels.append(v)
        
    
    x = np.array(x)
    areas_prop = np.array(areas_prop)
    areas_circ = np.array(areas_circ)
    diameters  = np.array(diameters)
    eccentricities = np.array(eccentricities)
    orientations = np.array(orientations)
    solidities = np.array(solidities)
    
    vels = np.array(vels)
    
    filter_area_min = 1
    filter_area_max = 999999999
    
    
    mask = (areas_circ>filter_area_min) & (areas_circ<filter_area_max)
    n_str = str(np.count_nonzero(mask))
    
    print("Statictics collected")
    
    # Generate some summary charts
    
    figsize, dpi = (7,5), 300
    
    
    th_fig, th_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    th_ax1.set_title(f"Thresholds (0-255) n={n_str}")
    th_ax1.hist(ls.th[mask], 50, (0, 255))
    th_ax1.set_xlabel("Value")
    th_fig.savefig(dump_path / "threshold.png")
    
    areasp_fig, areasp_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    areasp_ax1.set_title(f"Areas (prop) n={n_str}")
    areasp_ax1.hist(areas_prop[mask], 50, (0, 25e4))
    areasp_ax1.set_yscale('log')
    areasp_ax1.set_xlabel("Area (microns)")
    areasp_fig.savefig(dump_path / "area-prop-histogram.png")
    
    areasc_fig, areasc_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    areasc_ax1.set_title(f"Areas (circ) n={n_str}")
    areasc_ax1.hist(areas_circ[mask], 50, (0, 25e4))
    areasc_ax1.set_xlabel("Area (microns)")
    areasc_ax1.set_yscale('log')
    areasc_fig.savefig(dump_path / "area-circ-histogram.png")
    
    
    eccen_fig, eccen_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    eccen_ax1.set_title(f"Eccentricities n={n_str}")
    eccen_ax1.set_xlabel("Eccentricity")
    eccen_ax1.hist(eccentricities[mask], 50, (0, 1))
    eccen_fig.savefig(dump_path / "eccentricities-histogram.png")
    
    orien_fig, orien_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    orien_ax1.set_title(f"Orientations n={n_str}")
    orien_ax1.set_xlabel("Orientation (radians)")
    orien_ax1.hist(orientations[mask], 135, (-(np.pi/2), +(np.pi/2)))
    orien_fig.savefig(dump_path / "orientation-histogram.png")
    
    veloc_fig, veloc_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    veloc_ax1.set_title(f"Velocities n={n_str}")
    veloc_ax1.set_xlabel("Velocity (m/s)")
    veloc_ax1.hist(vels[mask], 50, (0,0.1))
    veloc_fig.savefig(dump_path / "velocity-histogram.png")
    
    dia_fig, dia_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    dia_ax1.set_title(f"Diameters n={n_str}")
    dia_ax1.set_xlabel("Diameter (microns)")
    dia_ax1.hist(diameters[mask], 50, (0,700))
    dia_fig.savefig(dump_path / "diameter-histogram.png")
    
    
    
    solid_fig, solid_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    solid_ax1.set_title(f"Solidities n={n_str}")
    solid_ax1.set_yscale('log')
    solid_ax1.set_xlabel("Solidities")
    solid_ax1.hist(solidities[mask], 50, (0,1))
    solid_fig.savefig(dump_path / "solidity-histogram.png")
    
    count_fig, count_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    count_ax1.set_title(f"Particle Counts / Frame n={n_str}")
    count_ax1.set_xlabel("Frame #")
    count_ax1.plot(f_counts)
    count_fig.savefig(dump_path / "particle-counts.png")
    
    Ap_x_V_fig, Ap_x_V_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    Ap_x_V_ax1.set_title(f"Area (prop) / Velocites n={n_str}")
    Ap_x_V_ax1.set_xlabel("Area (microns)")
    Ap_x_V_ax1.hist2d(areas_prop[mask], vels[mask], 150, ((0,25e4),(0,0.1)), norm=colors.LogNorm())
    Ap_x_V_fig.savefig(dump_path / "area-prop_x_velocity-histogram.png")
    
    Ac_x_V_fig, Ac_x_V_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    Ac_x_V_ax1.set_title(f"Area (circ) / Velocites n={n_str}")
    Ac_x_V_ax1.set_xlabel("Area (microns)")
    Ac_x_V_ax1.hist2d(areas_circ[mask], vels[mask], 150, ((0,25e4),(0,0.1)), norm=colors.LogNorm())
    Ac_x_V_fig.savefig(dump_path / "area-circ_x_velocity-histogram.png")
    
    D_x_V_fig, D_x_V_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    D_x_V_ax1.set_title(f"Diameter / Velocites n={n_str}")
    D_x_V_ax1.set_xlabel("Diameter (microns)")
    D_x_V_ax1.hist2d(diameters[mask], vels[mask], 150, ((0,700),(0,0.1)), norm=colors.LogNorm())
    D_x_V_fig.savefig(dump_path / "diameter_x_velocity-histogram.png")
    
    O_x_V_fig, O_x_V_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    O_x_V_ax1.set_title(f"Orientation / Velocites n={n_str}")
    O_x_V_ax1.set_xlabel("Orientation (radians)")
    O_x_V_ax1.hist2d(orientations[mask], vels[mask], 150, ((-1.8,1.8),(0,0.1)), norm=colors.LogNorm())
    O_x_V_fig.savefig(dump_path / "orientation_x_velocity-histogram.png")
    
    E_x_V_fig, E_x_V_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    E_x_V_ax1.set_title(f"Eccentricity / Velocites n={n_str}")
    E_x_V_ax1.set_xlabel("Eccentricity")
    E_x_V_ax1.hist2d(eccentricities[mask], vels[mask], 150, ((0,1),(0,0.1)), norm=colors.LogNorm())
    E_x_V_fig.savefig(dump_path / "eccentricity_x_velocity-histogram.png")
    
    
    E_x_O_fig, E_x_O_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
    E_x_O_ax1.set_title(f"Orientation / Eccentricity n={n_str}")
    E_x_O_ax1.set_xlabel("Orientation (radians)")
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
    plt.hist(areas_circ[mask], 50, (0, 25e4))
    
    plt.subplot(235)
    plt.title("Areas/Vel")
    plt.hist2d(areas_circ[mask], vels[mask], 150, ((0,25e4),(0,0.1)), norm=colors.LogNorm())
    
    plt.subplot(236)
    plt.title("Ecc/Or")
    plt.hist2d(orientations[mask], eccentricities[mask], 150, ((-1.8,1.8),(0,1)), norm=colors.LogNorm())
    
    plt.savefig(dump_path / "summary.png", bbox_inches='tight', dpi=300)
    
    # todo: figure with random examples collaged. (maybe show outliers too?)
    
    print("Plots generated")
    
    # Describe Particles (pass 2) 
    # Todo: see if it is worth combining pass 1 & 2
    
    with open(dump_path / "detections.csv", 'w') as detections:
        
        
        detections.write("Frame ID, Particle ID, Area (prop), Area (circ), Velocity, Intensity, Perimeter, X Position, Y Position, Major Axis, Minor Axis, Orientation, Solidity, Eccentricity, Diameter, Width, Height\n")
        
        
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
                
                major, minor, orien = p.major_axis_length, p.minor_axis_length, p.orientation
                d = (major * minor) / np.sqrt( (minor*np.cos(orien))**2 + (major*np.sin(orien))**2 ) 
                d *= LS_pixelCal
                d += np.random.uniform(-LS_pixelCal/2., LS_pixelCal/2.)
                #note that we add a small amount of noise to prevent quantization artifacts
                v = (LS_timeCal * ((d/h) + np.random.uniform(-LS_timeCal/2., LS_timeCal/2.)) / 1000000.0)
                
                #v = 7.797271 * 4000.0 * (w/h) / 1000000.0
                
                
                #
                # show crops...
                #cv2.imshow("crop", collage)
                #k = cv2.waitKey(1)
                #if k == ord('x'):
                #    break;
                #
                
                io.imsave(dump_path / "crops" / str(frame) / "{}-{}.png".format(uid, w), collage, "pil")
                
                
                #Frame ID, Particle ID, Area (prop), Area (circ),            Velocity, Intensity,        Perimeter,   X Position,    Y Position,    Major Axis,          Minor Axis,          Orientation,   Solidity,   Eccentricity,   Diameter, Width, Height.
                attrs = [frame, uid,    p.area,      ((w/2.0)**2)*3.14159,   v,        p.mean_intensity, p.perimeter, p.centroid[1], p.centroid[0], p.major_axis_length, p.minor_axis_length, p.orientation, p.solidity, p.eccentricity, d, w, h]

                csv_line = ",".join(list(map(str, attrs))) + "\n"
            
                detections.write(csv_line)
                
    print("All done")        
 
	
	
    
def collage_crops(ls, p):
    
    bb = p.bbox
    n_sq = 3
    
    w, h = bb[3] - bb[1], bb[2] - bb[0]
    crop = np.zeros((64+h, max(w*2, 64*n_sq), 3), dtype="uint8")
    
    div = ls.dv[bb[0]:bb[2], bb[1]:bb[3]]
    div_r = imresize(div, size=(64,64))#, mode="bicubic")
    
    vis = ls.im[bb[0]:bb[2], bb[1]:bb[3]]
    vis_r = imresize(vis, size=(64,64))
    
    mk = 255 * ls.mk[bb[0]:bb[2], bb[1]:bb[3]]
    mk_r = np.dstack([imresize(mk, size=(64,64))] * 3)
    
    
    crop[0:64, 0:(64*n_sq), :] = np.concatenate([vis_r, div_r, mk_r], axis=1)
    crop[64:(64+h), 0:w, :] = vis
    crop[64:(64+h), w:(w*2), :] = div
    
    return crop
