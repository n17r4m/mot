import matplotlib
matplotlib.use('GTK3Agg')
#.use must happen before importing pyplot.

import matplotlib.pyplot as plt
# %matplotlib tk

import numpy as np
plt.ion()
xTest = []
testTime = []
testLoss = []
testMSE = []

xTrain = []
trainTime = []
trainLoss = []
trainMSE = []
testAcc = []
trainAcc = []
count = 0

while True:

	try:
		line=input()
	except EOFError:
		break

	#legacy
	if line.startswith("Done"):
		break

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
		xTrain.append(x)
		trainLoss.append(loss)
		trainMSE.append(mse)
		trainTime.append(time)
		trainAcc.append(acc)


	if line.split(" - ")[2].startswith("Test"):
		x = int(line.split(" - ")[3].split(" ")[-1])
		time = float(line.split("-")[4].split(" ")[1])
		metrics = line.split(" - ")[5].split(",")
		# print(metrics)
		# print(metrics[0].split(":")[-1])
		loss = float(metrics[0].split(":")[-1])
		acc = float(metrics[1].split(":")[-1])
		mse = float(metrics[2].split(":")[-1][:-1])	
		xTest.append(x)
		testLoss.append(loss)
		testMSE.append(mse)
		testTime.append(time)
		testAcc.append(acc)	

		


# np.save('trainLoss', trainLoss)
# np.save('trainTime', trainTime)
# np.save('trainMSE', trainMSE)
# np.save('testLoss', testLoss)
# np.save('testTime', testTime)
# np.save('testMSE', testMSE)
# print(xTrain)
# print(trainLoss)
# print(trainTime)
# print(trainMSE)

# print(xTest)
# print(testLoss)
# print(testTime)
# print(testMSE)

plt.scatter(xTrain, trainLoss)
plt.title("Training Loss")
plt.show()

plt.waitforbuttonpress(0)


plt.clf()
plt.scatter(xTrain, trainTime)
plt.title("Training Time")
plt.show()
plt.waitforbuttonpress(0)

plt.clf()
plt.title("Training MSE")
plt.scatter(xTrain, trainMSE)
plt.show()
plt.waitforbuttonpress(0)

plt.clf()
plt.title("Training Acc")
plt.scatter(xTrain, trainAcc)
plt.show()
plt.waitforbuttonpress(0)


plt.clf()
plt.scatter(xTest, testLoss)
plt.title("Test Loss")
plt.show()
plt.waitforbuttonpress(0)

plt.clf()
plt.title("Test Time")
plt.scatter(xTest, testTime)
plt.show()
plt.waitforbuttonpress(0)

plt.clf()
plt.title("Test MSE")
plt.scatter(xTest, testMSE)
plt.waitforbuttonpress(0)

plt.clf()
plt.title("Training Acc")
plt.scatter(xTest, testAcc)
plt.show()
plt.waitforbuttonpress(0)
