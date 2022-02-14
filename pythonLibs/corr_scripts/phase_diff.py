from casatools import table
import numpy as np
import matplotlib.pyplot as plt
from yaml import load, Loader
#phase
calG = table()
calG.open("cal.b.G")
phase  = np.squeeze(calG.getcol("CPARAM"))
antnames = calG.getcol("ANTENNA1")

ang_p = np.rad2deg(np.angle(phase.T))
print(ang_p)

delays = np.loadtxt("./delays_residuals.txt", skiprows=1)

telinfo = load(open("/home/sonata/telinfo_ata.yml", "r").read(), Loader=Loader)

def get_antnumb(telinfo, antname):
    for entry in telinfo['antennas']:
        if entry['name'] == antname:
            return entry['number']

def get_antname(telinfo, antnum):
    for entry in telinfo['antennas']:
        if entry['number'] == antnum:
            return entry['name']


antnames = [get_antname(telinfo, int(antnum)) for antnum in delays[:,0]]
phasex = np.rad2deg((2*np.pi)*((1400*1e6) - (0/2)*1e6)*(delays[:,1]*1e-9))
phasey = np.rad2deg((2*np.pi)*((1400*1e6) - (0/2)*1e6)*(delays[:,2]*1e-9))

#phase_x = np.rad2deg(np.angle(np.exp(1j*phasex)))
#phase_y = np.rad2deg(np.angle(np.exp(1j*phasey)))


phase_x = phasex
phase_y = phasey

print(phasex)
print(phasey)

plt.figure(1)
plt.plot(-phase_x, ang_p[:,0], '.', color='blue')
plt.plot([-180,180], [-180,180])
plt.xlabel("Formula")
plt.ylabel("Measured post")

plt.figure(2)
plt.plot(-phase_y, ang_p[:,1], '.', color='blue')
plt.plot([-180,180], [-180,180])
plt.xlabel("Formula")
plt.ylabel("Measured post")

#plt.plot(phase_y, color='red', label='formula phase y')
#plt.plot(-1*ang_p[:,0], color='green', label='cal table phase x')
#plt.plot(-1*ang_p[:,1], color='orange', label='cal table phase y')

x = np.arange(len(antnames))
#plt.xticks(x, antnames)
plt.show()

#bandpass
#calBP = table()
#calBP.open("cal.b.BP")
#calBP.getcol("CPARAM")

#bandp  = np.squeeze(calBP.getcol("CPARAM"))
#antnames =  calBP.getcol("ANTENNA1")

#ang_b =  np.angle(bandp)

#phase_a = ang_p.T[:,np.newaxis,:]
#print(phase_a)

#angbp = phase_a + ang_b

#npol, nchan, nant = angbp.shape

'''
res_bp_final = np.zeros_like(angbp).reshape(nchan, nant*npol)

for iant in range(nant):
    for ipol in range(npol):
        res_bp_final[:, ipol + iant*npol] = angbp[ipol, :, iant]

antnames_pol = [str(antname)+pol for antname in antnames
        for pol in ["x","y"]]


np.savetxt("./bp_residuals.txt", res_bp_final, header=' '.join(antnames_pol), fmt='%.6f', comments='')


'''

