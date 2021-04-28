import numpy as np
import matplotlib.pyplot as plt

from sigpyproc.Readers import FilReader

import sys,os

fil = FilReader(sys.argv[1]+"_x.fil")
N = 200000

fig, ax = plt.subplots(nrows=3, sharex=True, figsize=(13,10))

block = fil.readBlock(0, fil.header.nsamples)

tsx = 10*np.log10(block[:-1].sum(axis=0))
m = np.median(tsx)
up = np.median(tsx[tsx > m])
down = np.median(tsx[tsx < m])
ax[0].plot(np.arange(block.shape[1])*fil.header.tsamp, tsx,
        label="XX")
ax[0].hlines([up,down], 0, (block.shape[1])*fil.header.tsamp, ls="--",
        label="XX compression: %.1f dB" %(up - down))
ax[0].set_ylabel("dB")
ax[1].imshow(10*np.log10(block[:, :N]), interpolation='nearest', aspect='auto',
        extent=[0, block[:,:N].shape[1]*fil.header.tsamp, fil.header.fbottom, fil.header.ftop])
ax[1].set_ylabel("Frequency (MHz)")
ax[1].set_xlabel("Time (sec)")
ax[1].set_title("X-pol")

ax[1].set_ylim(900, 940)

fil = FilReader(sys.argv[1]+"_y.fil")

block = fil.readBlock(0, fil.header.nsamples)

tsy = 10*np.log10(block[:-1].sum(axis=0))

m = np.median(tsy)
up = np.median(tsy[tsy > m])
down = np.median(tsy[tsy < m])
ax[0].hlines([up,down], 0, (block.shape[1])*fil.header.tsamp, ls="--",
        label="YY compression: %.1f dB" %(up - down))

ax[0].plot(np.arange(block.shape[1])*fil.header.tsamp, tsy,
        label="YY")
ax[0].set_ylabel("dB")
ax[2].imshow(10*np.log10(block[:, :N]), interpolation='nearest', aspect='auto',
        extent=[0, block[:,:N].shape[1]*fil.header.tsamp, fil.header.fbottom, fil.header.ftop])
ax[2].set_ylabel("Frequency (MHz)")
ax[2].set_xlabel("Time (sec)")
ax[2].set_title("Y-pol")

ax[2].set_ylim(900, 940)

fig.legend()
plt.xlim(2,2.8)

plt.show()

