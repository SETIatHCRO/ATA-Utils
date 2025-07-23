import ATATools.ata_sources as check
from ATATools import ata_control
import numpy as np

from parse import parse

from astropy.coordinates import EarthLocation, AltAz, ICRS, SkyCoord
from astropy import units as u
from astropy.time import Time, TimeDelta

OBSERVING_LOCATION = EarthLocation.from_geodetic(lat=40.8178*u.deg, lon=-121.4733*u.deg)

#Time to start observing script, change frequencies, RF/IF gain set, etc...
INITIAL_OVERHEAD_TIME = 70 # seconds
RF_IF_OVERHEAD_TIME   = 70 # seconds
BACKEND_OVERHEAD_TIME = 40 # seconds

# Slew rate:
SLEW_RATE = 1.5 #deg/sec
OBS_OVERHEAD = 10 #seconds

INITIAL_AZ, INITIAL_EL = (0, 18) #parked position

class ObsPlan(object):
    def __init__(self, start_time, obs_overhead = False, slew_time = False,
            initial_az = INITIAL_AZ, initial_el = INITIAL_EL):
        self.source_list = []
        self.obs_plan = []
        self.start_time = start_time
        self.time_incr = start_time
        self.obs_overhead = obs_overhead
        #if obs_overhead:
        #    self.add_wait_time(INITIAL_OVERHEAD_TIME)
        self.slew_time = slew_time
        self.current_position = (initial_az, initial_el)

    def add_wait_time(self, wait_time_sec):
        self.time_incr += wait_time_sec * u.second

    def add_rf_if_overhead(self):
        self.add_wait_time(RF_IF_OVERHEAD_TIME)
    
    def add_backend_overhead(self):
        self.add_wait_time(BACKEND_OVERHEAD_TIME)

    def add_wait_until_dt(self, t_until):
        remaining_timedelta = t_until - self.time_incr
        remaining_sec = remaining_timedelta.to_value('sec')
        if remaining_sec > 0:
            self.add_wait_time(remaining_sec)
        else:
            t_incr = self.time_incr
            print(f"OBSPLAN warning: {t_until} is in the past of current time {t_incr}")

    def add_obs_block(self, source, duration):
        # Assume source to
        if source.lower().startswith("radec"):
            source_info = self.parse_radec(source)
        else:
            if source.upper() == "NONE":
                source_info = {'object': 'NONE', 'is_up': True, 
                        'az': 180, 'el': 60, 'ra': 8, 'dec': 16, 
                        'rise_time_posix': None, 'set_time_posize': None} #XXX TODO REPLACE
            else:
                source_info = check.check_source(source)

        source_info['duration'] = duration
        # simulate a slew from "current_position" to "new_position"
        if self.slew_time:
            new_position = self.get_telescope_position(source_info, self.time_incr)
            slew_time = self.get_slew_time(self.current_position, new_position)
            self.time_incr += slew_time * u.second
            self.current_position = new_position

        # simulate overhead to start an observation
        if self.obs_overhead:
            self.time_incr += OBS_OVERHEAD * u.second

        source_info['start_time'] = self.time_incr
        self.time_incr += duration * u.second
        source_info['end_time'] = self.time_incr

        if self.slew_time:
            new_position = self.get_telescope_position(source_info, self.time_incr)
            self.current_position = new_position

        self.obs_plan.append(source_info)

    def parse_radec(self, source):
        source_info = {}
        source_info['object'] = source

        # extract radec from source_name
        res = parse('radec{ra},{dec}', source.lower())
        try:
            source_info['ra'] = float(res['ra'])
            source_info['dec'] = float(res['dec'])
        except Exception as e:
            raise Exception("Error in parsing RA/Dec from entry: '%s'" %source)
        return source_info

    def get_telescope_position(self, source_info, time):
        ra = source_info['ra']
        dec = source_info['dec']
        source_coords = ICRS(ra=ra*u.hour, dec=dec*u.deg)
        target = SkyCoord(source_coords)

        altaz = target.transform_to(AltAz(obstime=time, location=OBSERVING_LOCATION))
        return (altaz.az.deg, altaz.alt.deg)

    def get_slew_time(self, position_1, position_2):
        az1, el1 = position_1
        az2, el2 = position_2
        #max(180, abs(delta_az)) is an assumption, but good enough
        distance = np.sqrt(min(180, abs(az2 - az1)) ** 2 + (el2 - el1)**2) # degrees
        time = distance / SLEW_RATE
        return time

    def set_current_position(self, ant_list):
        az_el_dict = ata_control.get_az_el(ant_list)
        azs, els = np.array(list(az_el_dict.values())).T
        self.current_position = (np.median(azs), np.median(els))
