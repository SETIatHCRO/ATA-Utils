#!/home/sonata/miniconda3/envs/ATAobs/bin/python

from blimpy.io import sigproc
from astropy import units as u
from astropy.coordinates import Angle
import numpy as np
import sys

import pytz, datetime
from astropy.time import Time
import time


OFFSET = 675 - 629.1456
DADA_HDR_SZE = 4096
FC = 1400 - OFFSET
BW = 450.
NCHANS = 2048
TSAMP = NCHANS/(BW*1e6)*128
# virgo: 
#SOURCE = 'virgo'
#RA = Angle(12.514, u.hour)
#DEC = Angle(12.391, u.deg)
# casa: 23.391 +58.808
SOURCE = 'casa'
RA = Angle(23.391, u.hour)
DEC = Angle(58.808, u.deg)
# J1934+2153
#RA = Angle(19.582, u.hour)
#DEC = Angle(21.898, u.deg)
# J0332+5434: 3.549836 +54.5787025
#RA = Angle(3.549836, u.hour)
#DEC = Angle(+54.5787025, u.deg)
TELESCOPE = "ATA"


class FilBank(object):
    def __init__(self, header):
        self.header = header

#pps_time = 1588818872
"""
t_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(pps_time))

local = pytz.timezone("America/Los_Angeles")
naive = datetime.datetime.strptime(t_now, "%Y-%m-%d %H:%M:%S")
local_dt = local.localize(naive, is_dst=None)
utc_dt = local_dt.astimezone(pytz.utc)
t = Time(utc_dt, scale='utc')
tstart = t.to_value('mjd')
"""
tstart = Time(datetime.datetime.fromtimestamp(pps_time)).to_value('mjd')
print(tstart)


# Hard code everything for now
header = {
        'src_raj': RA,
        'src_dej': DEC,
        'foff': BW/2048,
        'nbits': 32,
        'nchans': NCHANS,
        'fch1': FC-BW/2,
        'nifs': 1, 
        'tstart': tstart,
        'tsamp': TSAMP,
        'data_type': 1,
        'telescope': TELESCOPE,
        'telescope_id': 9,
        'source_name': SOURCE
        }



header_str = sigproc.generate_sigproc_header(FilBank(header))


NSTOKES = True

output_fil_x = open(sys.argv[-1]+"_x.fil", "wb")
output_fil_y = open(sys.argv[-1]+"_y.fil", "wb")
output_fil_x.write(header_str)
output_fil_y.write(header_str)
print(sys.argv[1:-1])

for f in sys.argv[1:-1]:
    input_dada = open(f, "rb")
    input_dada.seek(DADA_HDR_SZE)
    data_to_file = np.fromfile(input_dada, dtype=np.float32)

    xx = data_to_file[0::4]
    yy = data_to_file[1::4]

    output_fil_x.write(xx.tobytes())
    output_fil_y.write(yy.tobytes())
