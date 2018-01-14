import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import numpy as np

plt.ion()

epochs = []
MOTAS = []

while True:
	try:
		line=input()
	except EOFError:
		break

	line = line.split(" - ")[-1]
	
	if line.startswith("DONE"):
		break

	if line.startswith("Evaluating"):
		experimentUUID = line.split(":")[-1]
	
	if line.startswith("Method"):
		method = line.split(":")[-1]
		epoch = method.split("Epoch")[-1]
		epoch = int(epoch)
		epochs.append(epoch)

	if line.startswith("MOTA"):
		MOTA = float(line.split(" ")[-1])
		MOTAS.append(MOTA)


X = epochs
Y = MOTAS
X, Y = zip(*sorted(zip(X, Y)))

best = np.max(Y)
print("Best:", best, "Epoch:", Y.index(best)+1)

#np.save("X", X)
#np.save("Y",  X)

plt.scatter(X, Y)
plt.title("MOTA Over Training Epochs")
plt.show()
plt.waitforbuttonpress(0)

# print(epochs)
# print(MOTAs)
