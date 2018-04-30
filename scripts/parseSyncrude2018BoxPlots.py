import numpy as np
import matplotlib.pyplot as plt
import sys
import os
# CSV Headers: Frame ID, Particle ID, Particle Area, Particle Velocity, Particle Intensity, Particle Perimeter, X Position, Y Position, Major Axis Length, Minor Axis Length, Orientation, Solidity, Eccentricity.
MS_pixelCal = 13.94736842
MS_timeCal = 300.

LS_pixelCal = 7.797271
LS_timeCal = 4000.

def main():
	if len(sys.argv)==2:
		path = sys.argv[1]
	else:
		path = '/home/kevin/mot/data/exports/Syncrude2018ValidationExports/megaspeed'
	
	diametre_data = []
	vel_data = []
	experiment_names = []
	header_offset = None
	for d in os.listdir(path):
		p = os.path.join(path,d)

		if not os.path.isfile(p):
			continue
		print("Processing file: "+d)
		if p.find("LS") == -1:
			header_offset = 1
			pixelCal = MS_pixelCal
			timeCal = MS_timeCal
		else:
			header_offset = 0
			pixelCal = LS_pixelCal
			timeCal = LS_timeCal

		x = []
		areas = []
		# eccentricities = []
		# orientations = []
		velocities = []
		count = 0

		with open(p) as f:
			for line in f:
				count += 1
				if count==1 and not header_offset:
					continue
				l = line.split(",")
				area = float(l[2+header_offset])
				vel = float(l[3+header_offset])
				# ecc = float(l[1])
				# ori = float(l[2])
				
				x.append(count)
				areas.append(area)
				velocities.append(vel)
				# eccentricities.append(ecc)
				# orientations.append(ori)
				

		x = np.array(x)
		areas = np.array(areas)
		velocities = np.array(velocities)
		
		diametre_data.append(2*np.sqrt(areas/np.pi)*pixelCal)
		vel_data.append(-velocities*pixelCal*timeCal/1e6)
		experiment_names.append(d[:-4])
		
	plt.boxplot(diametre_data, showfliers=False)
	plt.title("Diametres for multiple experiments")
	plt.ylabel("Diametre (microns)")
	plt.xticks(range(1, len(experiment_names)+1),experiment_names, rotation=45)
	
	plt.waitforbuttonpress(0)
	plt.close('all')
	
	plt.boxplot(vel_data, showfliers=False)
	plt.title("Velocities for multiple experiments")
	plt.ylabel("Velocity (m/s)")
	plt.xticks(range(1, len(experiment_names)+1), experiment_names, rotation=45)
	plt.waitforbuttonpress(0)
	
	# eccentricities = np.array(eccentricities)
	# orientations = np.array(orientations)
	
	# filter_area_min = 150
	# filter_area_max = 1000
	
	
def inlier_range(d):
	return full_range(d)
	q75, q25 = np.percentile(d, [75 ,25])
	iqr = q75 - q25
	return (q25 - (iqr*1.5), q75 + (iqr*1.5))

def full_range(d):
	return np.min(d), np.max(d)

if __name__ == "__main__":
	main()