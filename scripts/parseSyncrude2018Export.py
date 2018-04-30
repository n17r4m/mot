import numpy as np
import matplotlib.pyplot as plt
import sys
# CSV Headers: Frame ID, Particle ID, Particle Area, Particle Velocity, Particle Intensity, Particle Perimeter, X Position, Y Position, Major Axis Length, Minor Axis Length, Orientation, Solidity, Eccentricity.
pixelCal = 13.94736842
timeCal = 300.

def main():
	if len(sys.argv)==2:
		path = sys.argv[1]
	else:
		path = '/home/kevin/mot/data/exports/Syncrude2018ValidationExports/DetectLegV2_Beads_TrackingFiltered.txt'
		
	x = []
	areas = []
	# eccentricities = []
	# orientations = []
	velocities = []
	count = 0
	segment_count = 0
	segment_counts = []
	segment_last = 1
	frame_last = 1
	with open(path) as f:
		for line in f:
			count += 1
			l = line.split(",")
			area = float(l[3])
			vel = float(l[4])
			# ecc = float(l[1])
			# ori = float(l[2])
			
			x.append(count)
			areas.append(area)
			velocities.append(vel)
			# eccentricities.append(ecc)
			# orientations.append(ori)
			
			if segment_last != int(l[0]):
				segment_last = int(l[0])
				frame_last = int(l[1])
				segment_counts.append((frame_last, segment_count))
				segment_count = 0
			
			segment_count += 1

	x = np.array(x)
	areas = np.array(areas)
	velocities = np.array(velocities)
	segment_counts = np.array(segment_counts)
	
	# eccentricities = np.array(eccentricities)
	# orientations = np.array(orientations)
	
	# filter_area_min = 150
	# filter_area_max = 1000
	
	filt = inlier_range
	
	plt.subplot(211)
	d = areas
	lo,hi = filt(d)
	d_f = d[(d>lo) & (d<hi)]
	plt.title("Areas n="+str(len(d_f)))
	plt.hist(d_f, 20, (lo,hi))
	
	plt.subplot(212)
	lo,hi = filt(velocities)
	plt.title("Velocties n="+str(np.count_nonzero((velocities>lo) & (velocities<hi))))
	plt.hist(velocities[(velocities<hi) & (velocities>lo)], 20, (lo,hi))
	
	plt.waitforbuttonpress(0)
	
	plt.close('all')
	
	fig = plt.figure()
	
	ax = fig.add_subplot(211)
	diametres = 2*np.sqrt(areas/np.pi)*pixelCal
	lo,hi = filt(diametres)
	ax.set_title("Metric Diametres n="+str(np.count_nonzero((diametres>lo) & (diametres<hi))))
	ax.hist(diametres[(diametres>lo) & (diametres<hi)], 20, (lo,hi))
	ax.set_xlabel("diametre (microns)")
	
	ax = fig.add_subplot(212)
	velocities = -velocities*pixelCal*timeCal/1e6
	lo,hi = filt(velocities)
	print("lo: "+str(lo)+" hi: "+str(hi))
	ax.set_title("Metric Velocties n="+str(np.count_nonzero((velocities>lo) & (velocities<hi))))
	ax.hist(velocities[(velocities<hi) & (velocities>lo)], 20, (lo,hi))
	ax.set_xlabel("vertical velocity m/s")
	
	plt.waitforbuttonpress(0)
	
	plt.close('all')
	
	d = segment_counts
	lo, hi = full_range(d)
	plt.title("Particle per Frame ("+str(len(d))+" Segments Total)")
	plt.scatter(d[:,0],d[:,1])
	
	plt.waitforbuttonpress(0)
	
def inlier_range(d):
	q75, q25 = np.percentile(d, [75 ,25])
	iqr = q75 - q25
	return (q25 - (iqr*1.5), q75 + (iqr*1.5))

def full_range(d):
	return np.min(d), np.max(d)

if __name__ == "__main__":
	main()