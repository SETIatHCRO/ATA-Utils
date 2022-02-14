from pyuvdata import UVData

uv = UVData()

uv.read("/home/sonata/corr_data/guppi_59600_59008_139648_3c273_0001/guppi_59600_59008_139648_3c273_0001_b.uvh5", read_data=False)

# Now let's get ra/dec
ra = uv.phase_center_ra_degrees
dec = uv.phase_center_dec_degrees

# Now I need time:
lst_array = uv.lst_array #this is an entire array for every time integration in my file
lst = lst_array.mean() #take the mean for the centre of the observation

# or I get the Julian Date:
jd_array = uv.time_array
jd = jd_array.mean() #take the mean for the centre of the observation

# now use some astropy magic to convert to az/el:
from astropy.coordinates import EarthLocation,SkyCoord
from astropy.time import Time
from astropy import units as u
from astropy.coordinates import AltAz

ata_location = EarthLocation(lat= "40:49:03.0", lon= "-121:28:24.0", height= 1008)
observing_time = Time(jd, format='jd')
aa = AltAz(location=ata_location, obstime=observing_time)

coord = SkyCoord(ra*u.degree, dec*u.degree)
coords_alt_az = coord.transform_to(aa)

az, el = coords_alt_az.az.value, coords_alt_az.alt.value


print(az,el)
