import numpy as np
import matplotlib.pyplot as plt
import sys

def main():
	if len(sys.argv)==2:
		path = sys.argv[1]
	else:
		path = '/home/mot/data/eccentricityOrientationResults/BU-2015-10-22.msTOP-027260000001.txt'
		
	x = []
	areas = []
	eccentricities = []
	orientations = []
	count = 0
	with open(path) as f:
		for line in f:
			count += 1
			l = line.split(",")
			area = float(l[0])
			ecc = float(l[1])
			ori = float(l[2])
			
			x.append(count)
			areas.append(area)
			eccentricities.append(ecc)
			orientations.append(ori)
	
	x = np.array(x)
	areas = np.array(areas)
	eccentricities = np.array(eccentricities)
	orientations = np.array(orientations)
	
	filter_area_min = 150
	filter_area_max = 1000
	
	
	plt.subplot(211)
	plt.title("Eccentricities n="+str(np.count_nonzero((areas>filter_area_min) & (areas<filter_area_max) & (eccentricities>0.5))))
	plt.hist(eccentricities[(areas>filter_area_min) & (areas<filter_area_max) & (eccentricities>0.5)], 30, (0, 1))
	plt.subplot(212)
	plt.title("Orientations n="+str(np.count_nonzero((areas>filter_area_min) & (areas<filter_area_max) & (eccentricities>0.5))))
	plt.hist(orientations[(areas>filter_area_min) & (areas<filter_area_max) & (eccentricities>0.5)], 45, (-(np.pi/2), +(np.pi/2)))
	plt.waitforbuttonpress(0)
	
	
			
			
			




if __name__ == "__main__":
	main()