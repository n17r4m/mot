
import numpy as np
from lib.models.Framer import Framer


f = Framer()


im = np.ones((1, 778, 576, 1))
print(f.framer.summary())


for i in range(1000):
    f.framer.predict(im)
    print(i)

