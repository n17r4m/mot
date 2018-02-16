import matplotlib
matplotlib.use('GTK3Agg')
#.use must happen before importing pyplot.

import matplotlib.pyplot as plt
# %matplotlib tk

import numpy as np
plt.ion()

expStats = []
expCount = 0
LRs = []

while True:

	try:
		line=input()
	except EOFError:
		break

	if line.find("Running DVTrainer") >=0:
		# New training sesh found
		# add an array with the trainLoss, trainAcc empty arrays
		expStats.append([[],[]])
		expCount += 1
	if line.find("Learning Rate")>=0:
		LRs.append(float(line.split("Learning Rate")[-1]))

	#remove timestamp
	line = line[11:]
	if not line.split(" - ")[1].startswith("INFO"):
		continue
	if line.split(" - ")[2].startswith("Training"):
		x = int(line.split(" - ")[3].split(" ")[-1])
		time = float(line.split("-")[4].split(" ")[1])
		metrics = line.split(" - ")[5].split(",")
		# print(metrics[0].split(":")[-1])
		loss = float(metrics[0].split(":")[-1])
		acc = float(metrics[1].split(":")[-1])
		mse = float(metrics[2].split(":")[-1][:-1])
		expStats[expCount-1][0].append(loss)
		expStats[expCount-1][1].append(acc)

handles = []
for i, exp in enumerate(expStats):
	_ = plt.scatter(range(len(exp[0])), exp[0], label=LRs[i])
	handles.append(_)
plt.title("Training Loss")
plt.legend(handles=handles)
plt.show()
plt.waitforbuttonpress(0)

plt.close('all')
handles = []
for i, exp in enumerate(expStats):
	_ = plt.scatter(range(len(exp[1])), exp[1], label=LRs[i])
	handles.append(_)
plt.title("Training Acc")
plt.legend(handles=handles)
plt.show()
plt.waitforbuttonpress(0)