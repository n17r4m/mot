import numpy as np
import matplotlib.pyplot as plt
import sys
pixelCal = 13.94736842
timeCal = 300.

def main():
    if len(sys.argv)>=2:
        path = sys.argv[1]
    else:
        path = '/home/kevin/mot/data/exports/batchTest/Glass.Bead.Tests/212.to.250.um/MSBOT-010180000005_Tracking.txt'
    print()
    print(path)
    print()
    areas = []
    velocities = []
    
    with open(path) as f:
        for line in f:
            l = line.split(",")
            area = float(l[2])
            vel = float(l[3])
            areas.append(area)
            velocities.append(vel)

    m_lo_d = float(sys.argv[2])
    m_hi_d = float(sys.argv[3])
    
    m_lo_v = float(sys.argv[4])
    m_hi_v = float(sys.argv[5])
    
    boxes = 50
    
    areas = np.array(areas)
    velocities = np.array(velocities)
    dia_cal = 4.0
    diametres = (2.0 * np.sqrt(areas / np.pi)-dia_cal) * pixelCal
    velocities = -velocities*pixelCal*timeCal/1e6
    
    filt = inlier_range

    d = diametres
    lo,hi = filt(d)
    print("Area range", str(lo), str(hi))
    d_f = d[(d>lo) & (d<hi)]
    
    fig = plt.figure()
    ax = fig.add_subplot(211)
    ax.set_title("Metric Diameters n="+str(len(d_f)))
    ax.hist(d_f, boxes, (m_lo_d, m_hi_d))
    ax.set_xlabel("Diameter (microns)")
    
    
    d = velocities
    lo,hi = filt(d)
    print("Vel range", str(lo), str(hi))
    d_f = d[(d>lo) & (d<hi)]
        
    ax = fig.add_subplot(212)
    ax.set_title("Metric Velocties n="+str(len(d_f)))
    ax.hist(d_f, boxes, (m_lo_v, m_hi_v))
    ax.set_xlabel("Vertical Velocity m/s")
    
    plt.waitforbuttonpress(0)
    plt.close('all')
    
    
    
def inlier_range(d):
    q75, q25 = np.percentile(d, [75 ,25])
    iqr = q75 - q25
    return (q25 - (iqr*1.5), q75 + (iqr*1.5))

def full_range(d):
    return np.min(d), np.max(d)

if __name__ == "__main__":
    main()