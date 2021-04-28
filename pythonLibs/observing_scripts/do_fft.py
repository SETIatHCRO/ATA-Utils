from scipy import fftpack
from sigpyproc.Readers import FilReader
import matplotlib.pyplot as plt
import numpy as np
import sys

fil = FilReader(sys.argv[1])
nsamps2read = min(100000, fil.header.nsamples)
block = fil.readBlock(0, nsamps2read)
ts = np.flipud(block)[700:1800].sum(axis=0)

f_s = 1/fil.header.tsamp
X = fftpack.fft(ts)
freqs = fftpack.fftfreq(len(ts))*f_s

plt.figure()
plt.imshow(10*np.log10(block), interpolation='nearest', aspect='auto')

plt.figure()
plt.plot(10*np.log10(block.sum(axis=1)), label="Mean")
plt.plot(10*np.log10(block.std(axis=1)), label="STD")
plt.legend()

plt.figure()
plt.plot(np.linspace(0, nsamps2read*fil.header.tsamp, nsamps2read),
        10*np.log10(ts))
plt.xlabel("time (seconds)")
plt.ylabel("dB")

plt.figure()
plt.plot(freqs, np.abs(X)/np.max(np.abs(X)))
plt.xlabel("Frequency (Hz)")
plt.ylabel("FFT amplitude")

plt.show()
