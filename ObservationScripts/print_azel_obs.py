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

obsdirs = ["/mnt/buf0/xGPU/UVH5/uvh5_59611*_0001.uvh5", "/mnt/buf0/xGPU/UVH5/uvh5_59612*_0001.uvh5"]

all_dirs = []

all_dirs += [glob.glob(obsdir) for obsdir in obsdirs][0]
all_dirs += [glob.glob(obsdir) for obsdir in obsdirs][1]
#all_dirs += [glob.glob(obsdir) for obsdir in obsdirs][2]

print(all_dirs)

ant_name = 'Antenna 1k'
ant_numb = 10
azm = []
elev = []

#all_dirs = ["uvh5_59604_85066_1255096_3c84_0001/node1/uvh5_59604_85066_1255096_3c84_0001_0.uvh5"]
#all_dirs = ["uvh5_59612_31494_16423400_3c309.1_0001/node1/uvh5_59612_31494_16423400_3c309.1_0001_0.uvh5"]

for filename in sorted(all_dirs):
    
    uv = UVData()
    print(filename)
    uv.read(filename)

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

print("Azimuth")
print(azm)

print("Elevation")
print(elev)

lista = np.array([azm, elev])
print(lista.T)

np.savetxt("az_el_multiobs.txt", lista.T, header = 'Azimuth Elevation', delimiter=' ', fmt='%1.2f')



