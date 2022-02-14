from casatools import table
import numpy as np

#phase
calG = table()
calG.open("cal.b.G")
phase  = np.squeeze(calG.getcol("CPARAM"))
antnames = calG.getcol("ANTENNA1")

ang_p = np.angle(phase.T)

#bandpass
calBP = table()
calBP.open("cal.b.BP")
calBP.getcol("CPARAM")

bandp  = np.squeeze(calBP.getcol("CPARAM"))
antnames =  calBP.getcol("ANTENNA1")

ang_b =  np.angle(bandp)

phase_a = ang_p.T[:,np.newaxis,:]

angbp = phase_a + ang_b

npol, nchan, nant = angbp.shape

res_bp_final = np.zeros_like(angbp).reshape(nchan, nant*npol)

for iant in range(nant):
    for ipol in range(npol):
        res_bp_final[:, ipol + iant*npol] = angbp[ipol, :, iant]

antnames_pol = [str(antname)+pol for antname in antnames
        for pol in ["x","y"]]


np.savetxt("./bp_residuals.txt", res_bp_final, header=' '.join(antnames_pol), fmt='%.6f', comments='')




