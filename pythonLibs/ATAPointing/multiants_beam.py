import matplotlib.pyplot as plt
import numpy as np
import sys
import glob

from sigpyproc.Readers import FilReader



obsdir = "2021-11*"

ant_list = ['2eB', '2jB', '2kB', '2mB', '3dB' ]

for i, ant in enumerate(ant_list):
    
    listx = []
    listy = []
    for filename in sorted(glob.glob(obsdir)):
    
        filx = FilReader(glob.glob(filename+"/"+ant+"/*_x.fil")[0])
       
        blockx = filx.readBlock(0, filx.header.nsamples)[1660:1740]

        fily = FilReader(glob.glob(filename+"/"+ant+"/*_y.fil")[0])
        
        blocky = fily.readBlock(0, filx.header.nsamples)[1660:1740]

        xmean = blockx.mean()
        ymean = blocky.mean()
    

        listx.append(xmean)
        listy.append(ymean)

    arrx = np.array(listx)
    arry = np.array(listy)

    imgx = arrx.reshape(12,12)
    imgy = arry.reshape(12,12)

    step = 0.5

    az_list = np.arange(-3.0,3.0, step)
    el_list = np.arange(-3.0,3.0, step)

    centers = [-3,2.5,-3,2.5]
    dx, = np.diff(centers[:2])/(imgx.shape[1]-1)
    dy, = -np.diff(centers[2:])/(imgx.shape[0]-1)
    extent = [centers[0]-dx/2, centers[1]+dx/2, centers[2]+dy/2, centers[3]-dy/2]

    plt.figure(i*2, figsize=[12,8])

    plt.imshow(10*np.log10(imgx.T), interpolation='none', extent=[-3.25,2.75,-3.25,2.75], origin='lower')
    plt.xticks(np.arange(centers[0], centers[1]+dx, dx))
    plt.yticks(np.arange(centers[3], centers[2]+dy, dy))
    plt.axhline(y=0, color='red', linestyle='-')
    plt.axvline(x=0, color='red', linestyle='-')
    plt.ylabel("Elevation (deg)")
    plt.xlabel("Azimuth (deg)")
    plt.title("Antenna " + str(ant) + " X-Polarization")
    plt.colorbar()

    plt.figure(i*2+1, figsize=[12,8])

    plt.imshow(10*np.log10(imgy.T), interpolation='none', extent=[-3.25,2.75,-3.25,2.75], origin='lower')
    plt.title("Antenna " + str(ant) + " Y-Polarization")
    plt.xticks(np.arange(centers[0], centers[1]+dx, dx))
    plt.yticks(np.arange(centers[3], centers[2]+dy, dy))
    plt.axhline(y=0, color='red', linestyle='-')
    plt.axvline(x=0, color='red', linestyle='-')
    plt.ylabel("Elevation (deg)")
    plt.xlabel("Azimuth (deg)")
    plt.colorbar()
    print("Done with ant: %s" %ant)

plt.show()
