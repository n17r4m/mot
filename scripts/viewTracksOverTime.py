import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import numpy as np

plt.ion()

# [exp1, exp2]
# [mota_c1, mota_c2, mota_c3, mota_dv]
Xs = []
Ys = []
i = -1

while True:
	try:
		line=input()
	except EOFError:
		break
	if line.startswith("$"):
		i += 1
		Xs.append([])
		Ys.append([])
		continue
	line = line.split("|")
	Xs[i].append(int(line[0]))
	Ys[i].append(int(line[1]))
	
	
plt.title("Global Acceleration w.o. Corruption")
plt.xlabel("Segment")
plt.ylabel("# tracks")
handles = []
labels = ["Pos+App", "Pos", "App", "DVExp18 - E6 - N5"]
for i in range(len(Xs)):
	_ = plt.scatter(Xs[i], Ys[i], label=labels[i])
	handles.append(_)
plt.legend(handles=handles)
plt.show()
plt.waitforbuttonpress(0)
	
	