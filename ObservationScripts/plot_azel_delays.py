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
import os

#obsdir = re.compile("/home/sonata/corr_data/guppi_[59598*-59600*]_0001/")
#basedir = "/home/sonata/corr_data/"

obsdirs = ["/home/sonata/corr_data/uvh5_multi_delaybp/uvh5*_0001"]#, "uvh5*_0001"]#, "guppi_59600*_0001"]

all_dirs = []

all_dirs += [glob.glob(obsdir) for obsdir in obsdirs][0]
#all_dirs += [glob.glob(obsdir) for obsdir in obsdirs][1]
#all_dirs += [glob.glob(obsdir) for obsdir in obsdirs][2]

print(all_dirs)

ant_name = 'Antenna 3l'
ant_numb = 30
xdelays = []
ydelays = []

azm = []
elev = []

obs_id = []
ra_lst = []
dec_lst = []
jds = []

fixed_delay_base = 'uvh5_59614_09310_21019836_3c454.3_0001'

for filename in sorted(all_dirs):
    print(filename)
    baseuvh5 = os.path.basename(filename)
    delays = np.loadtxt(filename+"/delays_residuals.txt", skiprows=1)
    if baseuvh5 == fixed_delay_base:
        fixed_x = delays[ant_numb, 1]
        fixed_y = delays[ant_numb, 2]
    obs_id.append(baseuvh5)
    xdel = delays[ant_numb,1]
    xdelays.append(float(xdel))
    
    ydel = delays[ant_numb,2]
    ydelays.append(float(ydel))
    
    print(xdel, ydel)


    #now get az/el
    uv = UVData()
    uv.read(os.path.join(filename, baseuvh5+"_b.uvh5"), read_data=False)

    ra = uv.phase_center_ra_degrees
    dec = uv.phase_center_dec_degrees
    
    ra_lst.append(float(ra))
    dec_lst.append(float(dec))

    lst_array = uv.lst_array #this is an entire array for every time integration in my file
    lst = lst_array.mean()
    
    jd_array = uv.time_array
    jd = jd_array.mean()
    jds.append(float(jd))

    ata_location = EarthLocation(lat= "40:49:02.75", lon= "-121:28:14.65", height= 1019.222)
    observing_time = Time(jd, format='jd')

    aa = AltAz(location=ata_location, obstime=observing_time)
    coord = SkyCoord(ra*u.degree, dec*u.degree)
    coords_alt_az = coord.transform_to(aa)

    az, el = float(coords_alt_az.az.value), float(coords_alt_az.alt.value)
    
    azm.append(az)
    elev.append(el)

#print(obs_id)
#print(ra_lst)
#print(dec_lst)
xdelays -= fixed_x
ydelays -= fixed_y
delays = (xdelays + ydelays)/2.

lista = np.array([obs_id, ra_lst, dec_lst, jds, azm, elev, delays]).T
#lista = np.column_stack((obs_id, lista.T))
#listb = np.array([azm, elev, ydelays])
print(lista)

#np.savetxt("azel_del_multiobs_1k.txt", lista, header = 'OBS RA Dec JD Azimuth Elevation Residuals', delimiter=' ', fmt='%s %.6f %.6f %.8f %.6f %.6f %.6f')# %1.2f %1.2f %1.2f %1.2f %1.2f %1.2f')
#np.savetxt("azel_ydel_multiobs.txt", listb.T, header = 'Azimuth Elevation', delimiter=' ', fmt='%1.2f')

#az, el = np.loadtxt("/home/sonata/corr_data/az_el_multiobs.txt").T
fig = plt.figure(0)
#.title(str(ant_name) + "x-pol")
ax1 = fig.add_subplot(projection='polar')
ax1.set_title(str(ant_name) + "x-pol")
#delays = (xdelays + ydelays)/2.

x_col = ax1.scatter(azm, elev, c=delays)
fig.colorbar(x_col, ax=ax1)
ax1.set_ylim(90,0)

"""
#np.savetxt()

fig = plt.figure(1)
#plt.title(str(ant_name) + "y-pol")
ax2 = fig.add_subplot(projection='polar')
ax2.set_title(str(ant_name) + "y-pol")
y_col = ax2.scatter(azm, elev, c=ydelays)
fig.colorbar(y_col, ax=ax2)
ax2.set_ylim(90,0)
"""

plt.show()

