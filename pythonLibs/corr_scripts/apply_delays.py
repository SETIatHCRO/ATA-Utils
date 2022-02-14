import pandas as pd
import numpy as np

from yaml import load, Loader
import sys

def get_antnumb(telinfo, antname):
    for entry in telinfo['antennas']:
        if entry['name'] == antname:
            return entry['number']

ant_update = ["1c", "1k", "1h", "1e", "1g", "2a", "2b", "2c", 
        "2h", "2e", "2j", "2l", "2m", "3c", "3d", "3l", "4g",
        "5b", "4j", "2k"]

telinfo = load(open("/home/sonata/telinfo_ata.yml", "r").read(), Loader=Loader)
delays_initial = pd.read_csv(sys.argv[1], sep=" ", index_col=None)
delays_casa = np.loadtxt(sys.argv[2], skiprows=1)

delays_applied = delays_initial.copy()

for antname in ant_update:
    antnumb = get_antnumb(telinfo, antname)
    residuals = np.squeeze(delays_casa[delays_casa[:,0] == antnumb])[1:] # X and Y residuals
    ant_indx = delays_applied[delays_applied['#ant'] == antname].index

    delays_applied.loc[ant_indx, 'x'] += residuals[0]
    delays_applied.loc[ant_indx, 'y'] += residuals[1]

# now write the file
delays_applied.to_csv("delays_applied.txt", sep=" ", float_format="%.3f", index=False)
