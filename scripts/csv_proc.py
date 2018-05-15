import numpy as np
import matplotlib.pyplot as plt
import sys

ms_pixelCal = 13.94736842
ms_timeCal = 300.
LS_pixelCal = 7.797271
LS_timeCal = 4000.
dia_cal = 4.0

def main():
    
    ls_path = sys.argv[1]
    ms_path = sys.argv[2]
    name = sys.argv[3]
    
    print()
    print(ls_path)
    print()
    print(ms_path)
    print()

    ### MegaSpeed
    ms_areas = []
    ms_velocities = []
    with open(ms_path) as f:
        for line in f:
            l = line.split(",")
            area = float(l[2])
            vel = float(l[3])
            ms_areas.append(area)
            ms_velocities.append(vel)
    
    ms_areas = np.array(ms_areas)
    ms_velocities = np.array(ms_velocities)
    ms_diameters = (2.0 * np.sqrt(ms_areas / np.pi)-dia_cal) * ms_pixelCal
    ms_velocities = -ms_velocities*ms_pixelCal*ms_timeCal/1e6
    
    ### LineScan
    area_circs     = []
    velocities     = []
    minors         = []
    majors         = []
    orientations   = []
    
    first = True
    with open(ls_path) as f:
        for line in f:
            if first: # skip header
                first = False
                continue
            
            l = line.split(",")
            
            area_circs.append(    float(l[3]))
            velocities.append(    float(l[4]))
            majors.append(        float(l[9]))
            minors.append(        float(l[10]))
            
            orientations.append(  float(l[11]))
            
            
    area_circs     = np.array(area_circs     )
    ls_velocities  = np.array(velocities     )
    majors         = np.array(majors         )
    minors         = np.array(minors         )
    orientations   = np.array(orientations   )
    
    # width based diameter
    #ls_diameters = 2.0 * np.sqrt(area_circs / np.pi)
    
    # ellipse based diameter
    ls_diameters = (majors * minors) / np.sqrt((minors*np.cos(orientations))**2 + (majors*np.sin(orientations))**2)
    
    
    # adjust for ellipse based diameter
    # original calc: (7.797271 * 4000.0 * (w/h) / 1000000.0)
    inv_heights = ls_velocities * 1e6 / 4000.0 / 7.797271 / (2.0 * np.sqrt(area_circs / np.pi))
    ls_velocities = (7.797271 * 4000.0 * (ls_diameters*inv_heights) / 1000000.0)
    
    
    # Convert to metric
    ls_diameters *= LS_pixelCal 
    
    # Dither the input 
    ls_diameters += np.random.uniform(-LS_pixelCal/2., LS_pixelCal/2., area_circs.shape)
    
    # Match the input spec from MegaSpeed (area filter of 100px->157.379um diametre equiv)
    filter_dia_min = 157.4     # 157.379 um diametre
    filter_dia_max = 703.8     # 703.821 um diametre
    dia_mask = (ls_diameters>filter_dia_min) & (ls_diameters<filter_dia_max)
    ls_diameters = ls_diameters[dia_mask]
    
    ls_diameters -= dia_cal*LS_pixelCal #hackity - correct for over-estimation
    
    # invert for glass beads
    ls_velocities = -ls_velocities
    
    
    ###  ----   Plot Diameter
    filt = inlier_range
    
    my_dpi = 192
    plt.figure(figsize=(2800/my_dpi, 1600/my_dpi), dpi=my_dpi)
    plot_boxes = 50
    
    # Plot filtering
    ms_diameter_lo, ms_diameter_hi = filt(ms_diameters)
    ms_diameters_filtered = ms_diameters[(ms_diameters>ms_diameter_lo) & (ms_diameters<ms_diameter_hi)]
    print("Megaspeed diameter filter range", str(ms_diameter_lo), str(ms_diameter_hi))
    
    ls_diameter_lo, ls_diameter_hi = filt(ls_diameters)
    ls_diameters_filtered = ls_diameters[(ls_diameters > ls_diameter_lo) * (ls_diameters < ls_diameter_hi)]
    print("LineScan diameter filter range:",str(ls_diameter_lo),str(ls_diameter_hi))
    
    # Plot range calculations
    plot_low = min(ls_diameter_lo, ms_diameter_lo)
    plot_high = max(ls_diameter_hi, ms_diameter_hi)
    
    plot_range = plot_high-plot_low
    
    plot_low -= 0.05 * plot_range
    plot_high += 0.05 * plot_range
    
    # Generate plots
    plt.subplot(211)
    plt.title("MegaSpeed Diameters n="+str(len(ms_diameters_filtered)))
    plt.hist(ms_diameters_filtered, 
            plot_boxes, 
            (plot_low, plot_high))
    plt.xlabel("Diameter (microns)")
    
    plt.subplot(212)
    plt.title("LineScan Diameters n="+str(len(ls_diameters_filtered)))
    plt.hist(ls_diameters_filtered, 
            plot_boxes, 
            (plot_low, plot_high))
    plt.xlabel("Diameter (microns)")
    
    plt.suptitle(name,fontsize='xx-large')
    plt.subplots_adjust(hspace = 0.5)
    # plt.savefig('/home/mot/tmp/'+name.replace(' ','_')+'_diameters.png', dpi=my_dpi)
    plt.waitforbuttonpress(0)
    plt.close('all')
    
    plt.close('all')
    # End diameter plot
    
    ###  ------    Plot velocity
    filt = inlier_range
    
    my_dpi = 192
    plt.figure(figsize=(2800/my_dpi, 1600/my_dpi), dpi=my_dpi)
    plot_boxes = 50
    
    
    
    # Plot filtering
    ms_velocity_lo, ms_velocity_hi = filt(ms_velocities)
    ms_velocities_filtered = ms_velocities[(ms_velocities>ms_velocity_lo) & (ms_velocities<ms_velocity_hi)]
    print("Megaspeed velocity filter range", str(ms_velocity_lo), str(ms_velocity_hi))
    
    ls_velocity_lo, ls_velocity_hi = filt(ls_velocities)
    ls_velocities_filtered = ls_velocities[(ls_velocities > ls_velocity_lo) * (ls_velocities < ls_velocity_hi)]
    print("LineScan velocity filter range:",str(ls_velocity_lo),str(ls_velocity_hi))
    
    # Plot range calculations
    plot_low = min(ls_velocity_lo, ms_velocity_lo)
    plot_high = max(ls_velocity_hi, ms_velocity_hi)
    
    plot_range = plot_high-plot_low
    
    plot_low -= 0.05 * plot_range
    plot_high += 0.05 * plot_range
    
    # Generate plots
    plt.subplot(211)
    plt.title("MegaSpeed velocities n="+str(len(ms_velocities_filtered)))
    plt.hist(ms_velocities_filtered, 
            plot_boxes, 
            (plot_low, plot_high))
    plt.xlabel("Velocity (m/s)")
    plt.ylabel("# observations")
    
    plt.subplot(212)
    plt.title("LineScan velocities n="+str(len(ls_velocities_filtered)))
    plt.hist(ls_velocities_filtered, 
            plot_boxes, 
            (plot_low, plot_high))
    plt.xlabel("Velocity (m/s)")
    plt.ylabel("# observations")
    
    plt.suptitle(name,fontsize='xx-large')
    plt.subplots_adjust(hspace = 0.5)
    # plt.savefig('/home/mot/tmp/'+name.replace(' ','_')+'_velocities.png', dpi=my_dpi)
    plt.waitforbuttonpress(0)
    plt.close('all')
    # End velocity plot 
    
    
def inlier_range(d):
    q75, q25 = np.percentile(d, [75 ,25])
    iqr = q75 - q25
    return (q25 - (iqr*1.5), q75 + (iqr*1.5))

def full_range(d):
    return np.min(d), np.max(d)

if __name__ == "__main__":
    main()