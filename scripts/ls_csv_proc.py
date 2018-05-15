#!/usr/bin/python

import numpy as np
import matplotlib.pyplot as plt
import sys


def main():
    # if len(sys.argv)>=2:
    path = sys.argv[1]
    # else:
        # path = '/home/mot/data/results/Glass.Bead.Tests/212.to.250.um/LineScan01038/detections.csv'
    print()
    print(path)
    print()
    if len(sys.argv)>=4:
        d_min, d_max = int(sys.argv[2]), int(sys.argv[3])
    else:
        d_min, d_max = 100, 700
    
    if len(sys.argv)==6:
        v_min, v_max = float(sys.argv[4]), float(sys.argv[5])
    else :
        v_min, v_max = -0.1, 0.1
    
    
    
    frame_ids      = []
    particle_ids   = []
    area_props     = []
    area_circs     = []
    velocities     = []
    intensities    = []
    perimeters     = []
    xs             = []
    ys             = []
    majors         = []
    minors         = []
    orientations   = []
    solidities     = []
    eccentricities = []
    
    count = 0
    first = True
    with open(path) as f:
        for line in f:
            if first: # skip header
                first = False
                continue
            
            count += 1
            l = line.split(",")
            
            frame_ids.append(     int(l[0]))
            particle_ids.append(  str(l[1]))
            area_props.append(    float(l[2]))
            area_circs.append(    float(l[3]))
            velocities.append(    float(l[4]))
            intensities.append(   float(l[5]))
            perimeters.append(    float(l[6]))
            xs.append(            float(l[7]))
            ys.append(            float(l[8]))
            majors.append(        float(l[9]))
            minors.append(        float(l[10]))
            orientations.append(  float(l[11]))
            solidities.append(    float(l[12]))
            eccentricities.append(float(l[13]))
            
            
    frame_ids      = np.array(frame_ids      )
    particle_ids   = np.array(particle_ids   )
    area_props     = np.array(area_props     )
    area_circs     = np.array(area_circs     )
    velocities     = np.array(velocities     )
    intensities    = np.array(intensities    )
    perimeters     = np.array(perimeters     )
    xs             = np.array(xs             )
    ys             = np.array(ys             )
    majors         = np.array(majors         )
    minors         = np.array(minors         )
    orientations   = np.array(orientations   )
    solidities     = np.array(solidities     )
    eccentricities = np.array(eccentricities )
    
    
    
    ### Diameter
    
    diameters = 2.0 * np.sqrt(area_circs / np.pi)
    
    
    
    LS_pixelCal = 7.797271
    LS_timeCal = 4000.
    
    diameters -= 4.0 #hackity - correct for over-estimation
    
    diameters *= LS_pixelCal
     
    diameters += np.random.uniform(-LS_pixelCal/2., LS_pixelCal/2., area_circs.shape)
    
	# Metric
    filter_dia_min = 157.4     # 157.379 um diametre
    filter_dia_max = 703.8     # 703.821 um diametre
    
    
    dia_mask = (diameters>filter_dia_min) & (diameters<filter_dia_max)
    
    dia_filt = diameters[dia_mask]
    l, h = inlier_range(dia_filt)
    print("Diameters:",str(l),str(h))
    
    dia_filt = dia_filt[(dia_filt > l) * (dia_filt < h)]
    
    
    fig = plt.figure()
    
    ax = fig.add_subplot(211)
    ax.set_title("Metric Diameters n="+str(len(dia_filt)))
    
    
    ax.hist(dia_filt, 50, (d_min, d_max))
    ax.set_xlabel("Diameter (microns)")
    
    
    
    
    
    #### Velocity
    
    # velocities = velocities*LS_pixelCal*LS_timeCal/1e6
    
    velocities_filt = velocities[dia_mask]
    l, h = inlier_range(velocities_filt)
    print("Velocities:",str(l),str(h))
    
    velocities_filt = velocities_filt[(velocities_filt > l) * (velocities_filt < h)]
    
    
    ax = fig.add_subplot(212)
    ax.set_title("Metric Velocities n="+str(len(velocities_filt)))
    
    
    ax.hist(velocities_filt, 50, (v_min, v_max))
    ax.set_xlabel("Velocity (m/s)")
    
    
    
    
    
    
    plt.waitforbuttonpress(0)
    
    
            
            
            

def inlier_range(d):
	q75, q25 = np.percentile(d, [75 ,25])
	iqr = q75 - q25
	return (q25 - (iqr*1.5), q75 + (iqr*1.5))


if __name__ == "__main__":
    main()