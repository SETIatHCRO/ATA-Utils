import numpy as np
import matplotlib.pyplot as plt
import glob
from yaml import load, Loader
import re
from pyuvdata import UVData
from astropy.coordinates import EarthLocation,SkyCoord
from astropy.time import Time
from astropy import units as u
from astropy.coordinates import AltAz
import sys

#obsdir = re.compile("/home/sonata/corr_data/guppi_[59598*-59600*]_0001/")
#basedir = "/home/sonata/corr_data/"

obsdirs = ["uvh5*_0001", "uvh5*_0001"]#, "guppi_59600*_0001"]

all_dirs = []

all_dirs += [glob.glob(obsdir) for obsdir in obsdirs][0]
all_dirs += [glob.glob(obsdir) for obsdir in obsdirs][1]
#all_dirs += [glob.glob(obsdir) for obsdir in obsdirs][2]

print(all_dirs)

ant_name = 'Antenna 1k'
ant_numb = 10
xdelays = []
ydelays = []

azm = []
elev = []

for filename in sorted(all_dirs):
    print(filename)
    
    delays = np.loadtxt(filename+"/delays_residuals.txt", skiprows=1)
    xdel = delays[ant_numb,1]
    xdelays.append(xdel)
    
    ydel = delays[ant_numb,2]
    ydelays.append(ydel)
    
    print(xdel, ydel)


    #now get az/el
    uv = UVData()
    uv.read(filename+"/"+filename+"_b.uvh5", read_data=False)

    ra = uv.phase_center_ra_degrees
    dec = uv.phase_center_dec_degrees
    
    lst_array = uv.lst_array #this is an entire array for every time integration in my file
    lst = lst_array.mean()
    
    jd_array = uv.time_array
    jd = jd_array.mean()

    ata_location = EarthLocation(lat= "40:49:03.0", lon= "-121:28:24.0", height= 1008)
    observing_time = Time(jd, format='jd')

    aa = AltAz(location=ata_location, obstime=observing_time)
    coord = SkyCoord(ra*u.degree, dec*u.degree)
    coords_alt_az = coord.transform_to(aa)

    az, el = coords_alt_az.az.value, coords_alt_az.alt.value
    
    azm.append(az)
    elev.append(el)



#az, el = np.loadtxt("/home/sonata/corr_data/az_el_multiobs.txt").T
fig = plt.figure(0)
#.title(str(ant_name) + "x-pol")
ax1 = fig.add_subplot(projection='polar')
ax1.set_title(str(ant_name) + "x-pol")
x_col = ax1.scatter(azm, elev, c=xdelays)
fig.colorbar(x_col, ax=ax1)
ax1.set_ylim(90,0)

fig = plt.figure(1)
#plt.title(str(ant_name) + "y-pol")
ax2 = fig.add_subplot(projection='polar')
ax2.set_title(str(ant_name) + "y-pol")
y_col = ax2.scatter(azm, elev, c=ydelays)
fig.colorbar(y_col, ax=ax2)
ax2.set_ylim(90,0)

plt.show()

