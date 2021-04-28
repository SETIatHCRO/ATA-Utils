import numpy as np
import matplotlib.pyplot as plt
import sys

from sigpyproc.Readers import FilReader

"""
fil = FilReader(sys.argv[1]+"_x.fil")
fil.downsample(tfactor=16)
fil = FilReader(sys.argv[1]+"_y.fil")
fil.downsample(tfactor=16)
"""

#fil = FilReader('./2020-06-10-19:37:23_x_f1_t16.fil')
fil = FilReader(sys.argv[1]+'_x.fil')

block = fil.readBlock(0, fil.header.nsamples)

N = 200000

fig, ax = plt.subplots(nrows=3, sharex=True, figsize=(13,10)) 

ax[0].plot(np.arange(block.shape[1])*fil.header.tsamp, 10*np.log10(block[:-1].sum(axis=0)),
        label="XX") 
ax[0].set_ylabel("dB")                                                                              
ax[1].imshow(10*np.log10(block[:, :N]), interpolation='nearest', aspect='auto', 
        extent=[0, block[:,:N].shape[1]*fil.header.tsamp, fil.header.fbottom, fil.header.ftop])
ax[1].set_ylabel("Frequency (MHz)")                                                                 
ax[1].set_xlabel("Time (sec)")                                                                      
ax[1].set_title("X-pol")

ax[1].set_ylim(900, 940)



#fil = FilReader('./2020-06-10-19:37:23_y_f1_t16.fil')
fil = FilReader(sys.argv[1]+'_y.fil')

block = fil.readBlock(0, fil.header.nsamples)

ax[0].plot(np.arange(block.shape[1])*fil.header.tsamp, 10*np.log10(block[:-1].sum(axis=0)), 
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
