import pandas as pd
import numpy as np

from yaml import load, Loader
import sys

START_CHAN = 352
NCHAN_BP   = 192*7 #1344
NCHAN_PFB  = 2048

def get_antnumb(telinfo, antname):
    for entry in telinfo['antennas']:
        if entry['name'] == antname:
            return entry['number']


ant_update = ["1c", "1k", "1h", "1e", "1g", "2a", "2b", "2c", 
        "2h", "2e", "2j", "2l", "2m", "3c", "3d", "3l", "4g",
        "5b", "4j", "2k"]

telinfo = load(open("/home/sonata/telinfo_ata.yml", "r").read(), Loader=Loader)
phases_initial = pd.read_csv(sys.argv[1], sep=" ", index_col=False)
phases_casa    = pd.read_csv(sys.argv[2], sep=" ", index_col=False)


phases_applied = phases_initial.copy()



for antname in ant_update:
    antnumb = get_antnumb(telinfo, antname)

    phases_x = phases_casa['%ix' %antnumb]
    phases_y = phases_casa['%iy' %antnumb]

    if antname+"x" not in phases_initial.columns:
        phases_applied[antname+"x"] = np.zeros(NCHAN_PFB)
    phases_applied[antname+"x"][START_CHAN:START_CHAN+NCHAN_BP].values[:] +=\
            phases_x.values[:]

    if antname+"y" not in phases_initial.columns:
        phases_applied[antname+"y"] = np.zeros(NCHAN_PFB)
    phases_applied[antname+"y"][START_CHAN:START_CHAN+NCHAN_BP].values[:] +=\
            phases_y.values[:]


# now write the file
phases_applied.to_csv("phases_applied.txt", sep=" ", float_format="%.3f", index=False)
