import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys

exec(open("/home/sonata/utils/rcparams.py", "r").read())

START_CHAN = 352
NCHAN_BP   = 192*7 #1344
NCHAN_PFB  = 2048

phases_all = pd.read_csv(sys.argv[1], sep=" ", index_col=False)

antpols = phases_all.columns
ants = np.unique([antpol.strip("x").strip("y") for antpol in antpols])

for iant, ant in enumerate(ants):
    plt.figure(iant)

    if ant+"x" in antpols:
        x = np.rad2deg(phases_all[ant+"x"])[START_CHAN:START_CHAN+NCHAN_BP]
        x[x>180] -= 360
        plt.plot(x, ".", label=ant+"x")

    if ant+"y" in antpols:
        y = np.rad2deg(phases_all[ant+"y"])[START_CHAN:START_CHAN+NCHAN_BP]
        y[y>180] -= 360
        plt.plot(y, ".", label=ant+"y")

    plt.xlabel("Frequency channel number")
    plt.ylabel("Phase [deg]")
    plt.title("Antenna: %s" %ant)
    plt.grid(b=True, which='major')
    plt.grid(b=True, which='minor')

    plt.minorticks_on()

    plt.ylim(-180,180)
    plt.legend()

plt.show()
