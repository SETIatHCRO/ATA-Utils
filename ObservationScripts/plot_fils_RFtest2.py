import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import glob

from sigpyproc.Readers import FilReader

"""
fil = FilReader(sys.argv[1]+"_x.fil")
fil.downsample(tfactor=16)
fil = FilReader(sys.argv[1]+"_y.fil")
fil.downsample(tfactor=16)

UTCs_180 = [
        "2020-06-10-20:15:57", 
        "2020-06-10-20:18:57", 
        "2020-06-10-20:20:53",
        "2020-06-10-20:24:35",
        "2020-06-10-20:26:06",
        "2020-06-10-20:27:55"
        ]

UTCs_270 = [
        "2020-06-10-20:35:49",
        "2020-06-10-20:37:31",
        "2020-06-10-20:39:20",
        "2020-06-10-20:41:29",
        "2020-06-10-20:43:02",
        "2020-06-10-20:45:25"
        ]
"""


RF_freqs = [900, 850, 800, 750, 700, 
        650, 600, 550, 500, 450, 400,
        350, 300, 250, 200 ]



UTCs = [
        "2020-06-24-23:16:48",
        "2020-06-24-23:21:00",
        "2020-06-24-23:25:22",
        "2020-06-24-23:28:49",
        "2020-06-24-23:32:16",
        "2020-06-24-23:48:35",
        "2020-06-24-23:54:30",
        "2020-06-25-00:00:02",
        "2020-06-25-00:03:55",
        "2020-06-25-00:07:58",
        "2020-06-25-00:11:37",
        "2020-06-25-00:15:51",
        "2020-06-25-00:19:02",
        "2020-06-25-00:22:31"]




#PWR = [-3, 0, 3, 6, 9 ,12]
PWR = [10]

BASEDIR = "/mnt/buf0/obs"
outdir = "/home/sonata/RF_signal_generator/june24/same_RF_freq/"

for iutc, utc in enumerate(UTCs):
    print (utc)
    for ant in os.listdir(os.path.join(BASEDIR, utc)):
        if len(ant) != 2:
            continue
        print(ant)

        filx = glob.glob(os.path.join(BASEDIR, utc, ant, "*_x.fil"))[0]
        fil = FilReader(filx)

        block = fil.readBlock(0, fil.header.nsamples)

        N = 200000

        fig, ax = plt.subplots(nrows=3, sharex=True, figsize=(13,10)) 

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

        ax[1].set_ylim(fil.header.fcenter-100, fil.header.fcenter+100)



        #fil = FilReader('./2020-06-10-19:37:23_y_f1_t16.fil')
        fily = glob.glob(os.path.join(BASEDIR, utc, ant, "*_y.fil"))[0]
        fil = FilReader(fily)

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

        #ax[2].set_ylim(900, 940)
        ax[2].set_ylim(fil.header.fcenter-100, fil.header.fcenter+100)

        fig.legend()
        plt.xlim(2,2.8)
        freq = np.int(fil.header.fcenter)
        tname = ant+"_"+str(freq)+"_MHz_pos_"+"180"
        fig.suptitle(tname)
        plt.savefig(os.path.join(outdir, tname+".pdf"), fmt="pdf", 
                bbox_inches='tight')
        plt.clf()
        del(fig)
        del(ax)


