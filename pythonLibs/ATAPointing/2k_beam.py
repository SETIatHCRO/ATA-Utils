import matplotlib.pyplot as plt
import numpy as np
import sys

from sigpyproc.Readers import FilReader


listx = []
listy = []

obsdir = "2021*"


#for i, filename in enumerate(sys.argv[1:]):
for filename in glob.glob(obsdir):
    #print(filename)

    filx = FilReader(filename+"/"+"2kB/"+filename+"_x.fil")
    
    #print(filename+"/"+"2kB/"+filename+"_x.fil")
    
    blockx = filx.readBlock(0, filx.header.nsamples)[1660:1740]

    fily = FilReader(filename+"/"+"2kB/"+filename+"_y.fil")
    blocky = fily.readBlock(0, filx.header.nsamples)[1660:1740]

    xmean = blockx.mean()
    ymean = blocky.mean()
    
    #print(xmean)

    listx.append(xmean)
    listy.append(ymean)

arrx = np.array(listx)
arry = np.array(listy)



imgx = arrx.reshape(10,10)
imgy = arry.reshape(10,10)

step = 2

az_list = np.arange(-10.0,10.0, step)
el_list = np.arange(-10.0,10.0, step)

centers = [-10,8,-10,8]
dx, = np.diff(centers[:2])/(imgx.shape[1]-1)
dy, = -np.diff(centers[2:])/(imgx.shape[0]-1)
extent = [centers[0]-dx/2, centers[1]+dx/2, centers[2]+dy/2, centers[3]-dy/2]

plt.figure(figsize=[8,8])

plt.imshow(10*np.log10(imgx), interpolation='none', extent=[-10.5,8.5,-10.5,8.5])
plt.xlabel("Elevation (deg)")
plt.xticks(np.arange(centers[0], centers[1]+dx, dx))
plt.yticks(np.arange(centers[3], centers[2]+dy, dy))
plt.ylabel("Azimuth (deg)")
plt.title("X Polarization")
plt.colorbar()
plt.show()


plt.figure(figsize=[8,8])
plt.imshow(10*np.log10(imgy), interpolation='none', extent=[-10.5,8.5,-10.5,8.5])
plt.title("Y Polarization")
plt.xticks(np.arange(centers[0], centers[1]+dx, dx))
plt.yticks(np.arange(centers[3], centers[2]+dy, dy))
plt.xlabel("Elevation (deg)")
plt.ylabel("Azimuth (deg)")
plt.colorbar()

plt.show()

