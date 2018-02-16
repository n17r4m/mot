import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import numpy as np

plt.ion()

# [exp1, exp2]
# [mota_c1, mota_c2, mota_c3, mota_dv]
exp = [[], []]
current_exp = 0

while True:
	try:
		line=input()
	except EOFError:
		break

	if line.startswith("#"):
		current_exp += 1		
		current_mota = 0
	if line.startswith("."):
		current_mota += 1
		exp[current_exp-1].append([])
		continue
	if line == '' or line.startswith("$"):
		continue
	if current_mota:
		# print(current_exp, current_mota)
		exp[current_exp-1][current_mota-1].append(float(line))
	


# X = epochs
# Y = MOTAS
# X, Y = zip(*sorted(zip(X, Y)))

# best = np.max(Y)
# print("Best:", best, "Epoch:", Y.index(best)+1)

#np.save("X", X)
#np.save("Y",  X)
# print(exp)
titles = ["Global Acceleration w.o. Corruption", "Global Acceleration w/ Corruption"]
labels = ["Pos+App", "Pos", "App", "DVExp18 - E6 - N5", "DVExp23 - E26 - N5",  "DVExp23 - E39 - N5", "DVExp23 - E39 - N10", "DVExp18 - E6 - N10", "DvExp24 - E5 - N5"]
mask = [1,1,1,1,0,0,0,0,0]
for i, e in enumerate(exp):
	plt.close('all')
	plt.title(titles[i])
	plt.xlabel("Segment")
	plt.ylabel("MOTA Score")
	handles = []
	for j, method in enumerate(e):
		if not mask[j]:
			continue
		_ = plt.scatter(range(len(method)), method, label=labels[j])
		handles.append(_)
	
	plt.legend(handles=handles)
	plt.show()
	plt.waitforbuttonpress(0)

# print(epochs)
# print(MOTAs)
