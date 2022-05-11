import matplotlib.pyplot as plt
import numpy as np

az, el = np.loadtxt("/home/sonata/corr_data/az_el_multiobs.txt").T
fig = plt.figure()
ax = fig.add_subplot(projection='polar')
c = ax.scatter(az, el)
ax.set_ylim(90,0)

plt.show()
