#from casatools import table
import numpy as np
import matplotlib.pyplot as plt

from yaml import load, Loader

#phase
#calG = table()
#calG.open("cal.b.G")
#phase  = np.squeeze(calG.getcol("CPARAM"))
#antnames = calG.getcol("ANTENNA1")

#ang_p = np.angle(phase.T)

#x_ang = ang_p[:,0]
#print(ang_p)

#calk = table()
#calk.open("cal.b.K")
#delay  = np.squeeze(calk.getcol("CPARAM"))
#antname = calk.getcol("ANTENNA1")

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


antnames = [get_antname(telinfo, int(antnum)) for antnum in delays[:,0]]
phasex = np.rad2deg((2*np.pi)*((1400*1e6) - (672/2)*1e6)*(delays[:,1]*1e-9))
phasey = np.rad2deg((2*np.pi)*((1400*1e6) - (672/2)*1e6)*(delays[:,2]*1e-9))

print(phasex)
print(phasey)

phase_x = np.rad2deg(np.unwrap(np.deg2rad(phasex)))
phase_y = np.rad2deg(np.unwrap(np.deg2rad(phasey)))

#phase_x = phasex
#phase_y = phasey

print(phase_x)
print(phase_y)

plt.plot(phase_x, color='blue', label='x-pol')
plt.plot(phase_y, color='red', label='y-pol')
plt.xlabel("Phase")
plt.ylabel("Antenna")
plt.legend()

x = np.arange(len(antnames))
plt.xticks(x, antnames)

#plt.ylim(-360,360)

plt.show()

