import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

exec(open("/home/sonata/utils/rcparams.py", "r").read())

data = pd.read_csv("./sources_observed.csv")

perc_observed = []
freqs = []

for cname in data.columns:
    if not cname.startswith('cfreq'):
        continue
    freqs.append(float(cname.replace("cfreq_", "").replace("mhz", "")))

    obs_n    = len(np.where(data[cname] == 1)[0])
    nonobs_n = len(np.where(data[cname] == 0)[0])

    perc = float(obs_n) / (float(obs_n) + float(nonobs_n)) * 100

    perc_observed.append(perc)

print(perc_observed)
print(freqs)

plt.bar(freqs, perc_observed, width=200)
plt.xlabel("Frequency [MHz]")
plt.ylabel("Percentage observed [%]")

plt.show()
