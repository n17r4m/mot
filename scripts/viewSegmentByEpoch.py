import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import numpy as np

plt.ion()

# [exp1, exp2]
# [mota_c1, mota_c2, mota_c3, mota_dv]
exp = []
labels = []
current_exp = -1

while True:
	try:
		line=input()
	except EOFError:
		break
	line = line.split(" - INFO - ")[1]

	if line.startswith("Method"):
		e = line.split("Method:TrackingAllDvExp24N5weights")[1].split(" ")[0]
		e = int(e.split("Epoch")[-1])
		exp.append([])
		labels.append(e)
		current_exp += 1
		
	if line.startswith("MOTA "):
		mota = float(line.split("MOTA ")[1])
		exp[current_exp].append(mota)
	

# Reduce the number of segments
binSize = 1
newExp = []
segments = None
f = np.average
for e in exp:
	newExp.append([])
	newSegments = range(0, len(e), binSize)
	for j in range(0, len(e), binSize):
		newExp[-1].append(f(e[j:j+binSize]))
		
exp = newExp
segments = newSegments

# Find the best epoch in bin
binSize = 1
labels, exp = zip(*sorted(zip(labels, exp)))
sums = [np.sum(e[40:]) for e in exp]
maxIdxs = [j+i.index(np.max(i)) for (j,i) in [(j, sums[j:j+binSize]) for j in range(0,len(sums),binSize)]]

# Plot the results
title = "Epoch Effect on MOTA Score for \n Global Acceleration w/ Corruption Video"
plt.title(title)
plt.xlabel("Segment")
plt.ylabel("MOTA Score")

if segments is None:
	segments = range(len(exp[0]))

# print(sums)
# print(maxIdxs)
handles = []
for i in maxIdxs:
	e = exp[i]
	plt.scatter(segments, e, label="Epoch "+str(labels[i]))
	# handles.append(_)

plt.legend()
plt.show()
plt.waitforbuttonpress(0)

# print(epochs)
# print(MOTAs)
