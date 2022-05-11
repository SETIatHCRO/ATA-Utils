exec(open("/home/sonata/utils/rcparams.py", "r").read())
import numpy as np
import matplotlib.pyplot as plt

from yaml import load, Loader


telinfo = load(open("/home/sonata/telinfo_ata.yml", "r").read(), Loader=Loader)

def get_antnumb(telinfo, antname):
    for entry in telinfo['antennas']:
        if entry['name'] == antname:
            return entry['number']

def get_antname(telinfo, antnum):
    for entry in telinfo['antennas']:
        if entry['number'] == antnum:
            return entry['name']


delays = np.loadtxt("delays_residuals.txt", skiprows=1)

delx = delays[:,1]
dely = delays[:,2]

antnames = [get_antname(telinfo, int(antnum)) for antnum in delays[:,0]]

srate = 1.024 * 2 * 1e9 #sampling rate of ADCs
ADC_time = 1/srate * 1e9 #ADC sample time, in ns

delays_x = delx/ADC_time
delays_y = dely/ADC_time

plt.plot(delays_x, '.', color='blue', label='x-pol')
plt.plot(delays_y, '.',  color='red', label='y-pol')
plt.ylabel("Residuals (ADC Samples)")
plt.xlabel("Antenna")
plt.legend()

x = np.arange(len(antnames))
plt.xticks(x, antnames)

plt.grid(b=True, which='major')
plt.grid(b=True, which='minor')

plt.minorticks_on()

plt.show()

