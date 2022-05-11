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
import itertools

#obsdir = re.compile("/home/sonata/corr_data/guppi_[59598*-59600*]_0001/")
#basedir = "/home/sonata/corr_data/"
def countList(lst1, lst2):
    return np.array([[i, j] for i, j in zip(lst1, lst2)]).ravel()

obsdirs = ["/home/sonata/corr_data/uvh5_multi_new/uvh5_*"]#, "/home/sonata/corr_data/uvh5_multi_new/uvh5_59618_2*", "/home/sonata/corr_data/uvh5_multi_new/uvh5_59618_3*"]

all_dirs = []

all_dirs += [glob.glob(obsdir) for obsdir in obsdirs][0]
#all_dirs += [glob.glob(obsdir) for obsdir in obsdirs][1]
#all_dirs += [glob.glob(obsdir) for obsdir in obsdirs][2]

print(all_dirs)

#ant_name = 'Antenna 3l'
#ant_numb = 30
xdelays = []
ydelays = []

azm = []
elev = []

obs_id = []
ra_lst = []
dec_lst = []
jds = []
lsts = []

delst = []

ant_list=[3,5,7,8,10,11,12,13,15,18,19,20,21,22,23,24,30,33,35,38]

ant_names=['1c', '1e', '1g', '1h', '1k', '2a', '2b', '2c', '2e', '2h', '2j', '2k', '2l', '2m', '3c', '3d', '3l', '4g', '4j', '5b']

ant_names_pol = [ant+pol for ant in ant_names for pol in ["x","y"]]

#fixed_delay_base = 'uvh5_59618_51600_32857299_3c273_0001'

for filename in sorted(all_dirs):
    print(filename)
    baseuvh5 = os.path.basename(filename)
    delays = np.loadtxt(filename+"/delays_residuals_1c.txt", skiprows=1)
    

    #if baseuvh5 == fixed_delay_base:
    #    fixed_x = [delays[ant_numb, 1] for ant_numb in ant_list]
    #    fixed_y = [delays[ant_numb, 2] for ant_numb in ant_list]
    
    obs_id.append(baseuvh5)
    dels = [delays[ant_numb,pol] for ant_numb in ant_list for pol in [1,2]]
    delst.append(dels)
    
    #ydel = [delays[ant_numb,2] for ant_numb in ant_list]
    #ydelays.append(ydel)
    
    #print(xdel, ydel)

    #delays = countList(delays, delays)
    #delst.append(delays)
    #print(delays)
    
    #now get az/el
    uv = UVData()
    uv.read(os.path.join(filename, baseuvh5+"_b.uvh5"), read_data=False)

    ra = uv.phase_center_ra_degrees
    dec = uv.phase_center_dec_degrees
    
    ra_lst.append(float(ra))
    dec_lst.append(float(dec))

    lst_array = uv.lst_array #this is an entire array for every time integration in my file
    lst = lst_array.mean()
    lsts.append(np.rad2deg(float(lst)))
    
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

#xdelays -= fixed_x
#ydelays -= fixed_y
#delays = (xdelays + ydelays)/2.

#print(xdelays)

lista = np.array([obs_id, ra_lst, dec_lst, lsts, azm, elev]).T
#lista = np.column_stack((obs_id, lista.T))
#delays =  [x for x in itertools.chain.from_iterable(itertools.izip_longest(xdelays,ydelays)) if x]

print(delst)


#delays = countList(xdelays, ydelays)
#print(delays)

listb = np.column_stack([lista, delst])

#print(listb)

ant_names_pol_str = " ".join(ant_names_pol)


np.savetxt("uvh5_multi_new/azel_del_multiobs_allants_1c.txt", listb, header = 'OBS RA_deg Dec_deg LST_deg Azimuth Elevation %s' %ant_names_pol_str, delimiter=' ', fmt='%s')
#, fmt='%s %.6f %.6f %.8f %.6f %.6f %.6f')# %1.2f %1.2f %1.2f %1.2f %1.2f %1.2f')


