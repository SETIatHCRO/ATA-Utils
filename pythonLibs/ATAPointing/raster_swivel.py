import matplotlib.pyplot as plt
import numpy as np
import sys
import glob
from sigpyproc.Readers import FilReader
from astropy import units as u
import math



#listx = []
#listy = []

obsdir = "/mnt/buf0/obs/2021-11-17*"
ant_list = [ "1kB",
                 "2aB", "2bB", "2cB",
                "2eB", "2jB",
                "2mB"]


ant_data = {}

for i, ant in enumerate(ant_list):
    ant_data[ant+"x"] = []
    ant_data[ant+"y"] = []


    listx = []
    listy = []
    for filename in sorted(glob.glob(obsdir)):

        filx = FilReader(glob.glob(filename+"/"+ant+"/*_x.fil")[0])
        obs_time_s = filx.header.tsamp*filx.header.nsamples
        tstart = (filx.header.tstart - 40587)*86400  + 37

        eph_fil = np.loadtxt(glob.glob(filename+"/*.txt")[0])[:,0]


        tephems = eph_fil[0]/1e9
        #print(tephems)
        tdiff = tephems - tstart

        tephemend = eph_fil[5]/1e9
        #print(tephemend)
        ephem_time = tephemend-tephems
        #print(ephem_time)
        ep_end = (filx.header.nsamples*(ephem_time+tdiff))/obs_time_s

        ep_st = (filx.header.nsamples*tdiff)/obs_time_s

        nsmp = ep_end - ep_st

        blockx = filx.readBlock(int(ep_st),int(nsmp))
        bpx = np.array(blockx[1660:1740])

        fily = FilReader(glob.glob(filename+"/"+ant+"/*_y.fil")[0])

        blocky = fily.readBlock(int(ep_st),int(nsmp))
        bpy = np.array(blocky[1660:1740])

        step = 60 // 5

        #az_list = np.linspace(0, 20, step)


        n_int = int(math.floor(nsmp/(step))*(step))

        block_x = np.sum(bpx,axis=0)
        block_y = np.sum(bpy,axis=0)

        x_bk = block_x[:n_int].reshape((step, -1))#.sum(-1)
        y_bk = block_y[:n_int].reshape((step, -1))#.sum(-1)

        #print("Done iter")
        ant_data[ant+"x"].append(block_x)
        ant_data[ant+"y"].append(block_y)

    plt.figure(i*2, figsize=[12,8])

    plt.imshow(10*np.log10((np.array(ant_data[ant+"x"])).T), interpolation='none', origin='lower', extent=[-3,3,-3,3])
    plt.xticks(np.arange(-3,3,0.5))
    plt.yticks(np.linspace(-3,3,6))
    plt.axhline(y=0, color='red', linestyle='-')
    plt.axvline(x=0, color='red', linestyle='-')
    plt.ylabel("Elevation (deg)")
    plt.xlabel("Azimuth (deg)")
    plt.title("Antenna " + str(ant) + " X-Polarization")
    plt.colorbar()

    plt.figure(i*2+1, figsize=[12,8])

    plt.imshow(10*np.log10((np.array(ant_data[ant+"y"])).T), interpolation='none', origin='lower', extent=[-3,3,-3,3])
    plt.title("Antenna " + str(ant) + " Y-Polarization")
    plt.xticks(np.arange(-3,3,0.5))
    plt.yticks(np.linspace(-3,3,6))
    plt.axhline(y=0, color='red', linestyle='-')
    plt.axvline(x=0, color='red', linestyle='-')
    plt.ylabel("Elevation (deg)")
    plt.xlabel("Azimuth (deg)")
    plt.colorbar()

    print("Done with ant " + str(ant))

plt.show()
