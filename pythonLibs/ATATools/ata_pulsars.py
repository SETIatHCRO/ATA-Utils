import os
import subprocess
import argparse

from astropy.coordinates import EarthLocation, SkyCoord, AltAz
from astropy.time import Time
from astropy import units as u

import datetime
import numpy as np
import pandas as pd

ATA_LAT = 40.8178
ATA_LON = 121.473

time_string = "%Y-%m-%d %H:%M:%S"

ATA = EarthLocation.of_site("Allen Telescope Array")

'''
ATA_PULSARS = PULSARS = 
       ['J1939+2134', 
        'J1713+0747', 
        'J2145-0750', 
        'J1857+0943', 
        'J1022+1001', 
        'J1643-1224', 
        'J1744-1134', 
        'J0613-0200', 
        'J0837+0610', 
        'J0332+5434', 
        'J0953+0755', 
        'J1935+1616', 
        'J2022+2854', 
        'J2018+2839', 
        'J1932+1059', 
        'J2022+5154', 
        'J1645-0317', 
        'J1239+2453', 
        'J0358+5413']
'''

ATA_PULSAR_DATA = pd.read_csv("PULSARS.csv")#[el.split(",") for el in f.read().split("\n") if el[0] != '' and if el[0] != "PULSAR"]

ATA_PULSARS = PULSARS = ATA_PULSAR_DATA["PULSAR"]

PRIORITIES = {}

for priority in range(1, max([int(el) for el in ATA_PULSAR_DATA["PRIORITY"]]) + 1):
    if priority not in PRIORITIES:
        PRIORITIES[priority] = ATA_PULSAR_DATA["PULSAR"][ATA_PULSAR_DATA["PRIORITY"] == priority].tolist()

MAX_OBS_TIME = 30
MIN_OBS_TIME = 10
OBS_TIME_RANGE = MAX_OBS_TIME - MIN_OBS_TIME 

FLUX_DENS_HIGH_PLAT = 30
FLUX_DENS_LOW_PLAT = 5
FLUX_DENS_RANGE = FLUX_DENS_HIGH_PLAT - FLUX_DENS_LOW_PLAT

OBS_BUFFER_TIME = 3

PSRCAT_PARAMS = [
    'PSRJ',
    'RAJ',
    'DECJ',
    'S1400'
    ]

def fetch_pulsar_data(pulsar, key = None):
    options = ['-nohead',
            '-o', 'short',
            '-nonumber'
            ]
    

    command = ['psrcat', pulsar] + ['-c', " ".join(PSRCAT_PARAMS)] + options


    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    result = out.decode("utf-8")
    while "  " in result:
        result = result.replace("  ", " ")

    if key is None:
        return result.split(" ")
    else:
        return result.split(" ")[PSRCAT_PARAMS.index(key)]

def get_ATA_LST(time = None):
    if time is None:
        time = datetime.datetime.now()

    observing_location = ATA 

    obs_time = Time(time, scale = 'utc', location = observing_location)
    lst = obs_time.sidereal_time('mean')

    return lst

#takes ra and dec in 'xxhxxmxx.xs' format
def radec_to_azel(ra, dec, time):
    observing_location = ATA
    observing_time = Time(time)
    aa = AltAz(location = observing_location, obstime = observing_time)

    coord = SkyCoord(ra = ra, dec = dec)
    newcoord = coord.transform_to(aa)

    return [newcoord.altaz.az.deg, newcoord.altaz.alt.deg]

def check_pulsar_availability(pulsar, timewindows = None):
    if timewindows is None:
        now = datetime.datetime.now()
        delta = datetime.timedelta(minutes = 30)

        timewindows = [[now - delta, now + delta]]
    
    data = fetch_pulsar_data(pulsar)

    RAJ_str = data[PSRCAT_PARAMS.index("RAJ")]

    RAJ_spl = RAJ_str.split(":")
    RAJ_fmt = RAJ_spl[0] + "h" + RAJ_spl[1] + "m" + RAJ_spl[2] + "s"

    DECJ_str = data[PSRCAT_PARAMS.index("DECJ")]

    DECJ_spl = DECJ_str.split(":")
    DECJ_fmt = DECJ_spl[0] + "d" + DECJ_spl[1] + "m" + DECJ_spl[2] + "s"

    availability = []

    for window in timewindows:
        altaz_start = radec_to_azel(RAJ_fmt, DECJ_fmt, window[0])
        altaz_end = radec_to_azel(RAJ_fmt, DECJ_fmt, window[1])

        az_beg = altaz_start[0]
        el_beg = altaz_start[1]

        az_end = altaz_end[0]
        el_end = altaz_end[1]

        available = []

        search_delta = datetime.timedelta(minutes = 1)

        #check if the object is available at the start of the window
        #else find when it rises
        if el_beg >= 20:
            available.append(window[0])
        else:
            object_rises = window[0]
            az = az_beg
            el = el_beg
            while el < 20:
                object_rises = object_rises + search_delta
                
                if object_rises >= window[1]:
                    break
                
                az, el = radec_to_azel(RAJ_fmt, DECJ_fmt, object_rises)

            #if the rise time is >= to the end of the window, the object can't be seen
            if object_rises >= window[1]:
                available.append(False)
            else:
                available.append(object_rises)


        #and now check for the end
        if el_end >= 20:
            available.append(window[1])
        else:
            #if the object was available earlier on in the window,
            #then we can check for when it sets
            if available[0]:
                object_sets = window[1]
                az = az_end
                el = el_beg
                while el < 20:
                    object_sets = object_sets - search_delta

                    #since the object was available at the beginning, we don't have to check
                    #for the object_sets time being less than the start

                    az, el = radec_to_azel(RAJ_fmt, DECJ_fmt, object_sets)

                available.append(object_sets)
            #otherwise we know the object is not visible during the window
            else:
                available.append(False)


        availability.append(available)

    return availability


def create_obs_schedule(l, timewindows = None):
    if timewindows is None:
        timewindows = [[0, 1]]

    now = datetime.datetime.now()

    for window_ind in range(len(timewindows)):
        start = timewindows[window_ind][0]
        end = timewindows[window_ind][1]
        w = [now + datetime.timedelta(minutes = start), now + datetime.timedelta(minutes = end)]
        timewindows[window_ind] = w

    print("Checking pulsar visibilities...")
    all_availabilities = [check_pulsar_availability(pulsar, timewindows) for pulsar in l] 

    availabilities_dict = {}
    for item, pulsar in zip(all_availabilities, l):
        availabilities_dict[pulsar] = item

    print("Computing observation times using BUFFERTIME = " + str(OBS_BUFFER_TIME) + "...")
    all_obstimes = []#[float(fetch_pulsar_data(pulsar, "S1400")) for pulsar in l]
    #all_obstimes = [OBS_BUFFER_TIME + min(MIN_OBS_TIME + OBS_TIME_RANGE * (max(FLUX_DENS_HIGH_PLAT - fluxdens, 0) / FLUX_DENS_RANGE), MAX_OBS_TIME) for fluxdens in all_obstimes]

    for pulsar_ind in range(len(l)):
        pulsar = l[pulsar_ind]
        fluxdens = float(fetch_pulsar_data(pulsar, "S1400"))
        basetime = MIN_OBS_TIME + OBS_TIME_RANGE * ((max(FLUX_DENS_HIGH_PLAT - fluxdens, 0) / FLUX_DENS_HIGH_PLAT) ** (1 / 2))
        maxtime = MAX_OBS_TIME
        obstime = OBS_BUFFER_TIME + min(basetime, MAX_OBS_TIME)

        obstime = min( max( MIN_OBS_TIME, MIN_OBS_TIME / ((fluxdens / FLUX_DENS_HIGH_PLAT) ** 2)), MAX_OBS_TIME) + OBS_BUFFER_TIME

        all_obstimes.append(obstime)

    obstimedict = {}

    for ind in range(len(PULSARS)):
        obstimedict[PULSARS[ind]] = all_obstimes[ind]

    remaining_pulsars = obstimedict

    visible_matches = {}

    schedule = {}

    print("Matching observation windows to visible pulsars...")

    observed = []

    for twind_ind in range(len(timewindows)):
        timewindow = timewindows[twind_ind]
        print("\tChecking visible pulsars for window", timewindow[0].strftime(time_string), "->", timewindow[1].strftime(time_string))
        available = []
        for pulsar in l:
            pulsar_window = availabilities_dict[pulsar][twind_ind]
            if not pulsar_window[0]:
                continue
            else:
                available.append(pulsar)

        schedule[timewindow[0]] = []
        marker = timewindow[0]

        for priority in range(max(PRIORITIES), 0, -1):
            print("\t\tWorking on priority " + str(priority) + "...")
            if priority not in PRIORITIES:
                print("\t\t\tNo pulsars with this priority, skipping...")
                continue

            this_priority_avail = [el for el in available if el in PRIORITIES[priority]]
            this_priority_avail.sort(key = lambda x : availabilities_dict[x][twind_ind][0])

            print("\t\t\tPrioritizing unobserved pulsars...")
            #for every pulsar we observe, we want to put those at the back of the list 
            #so we will keep track of which pulsars we have observed, and whenever we
            #construct a lis of available pulsars, and sort by earliest visibility
            #time, we will remove every observed pulsar and then add the list of observed pulsars
            #back to the end (after sorting that itself for earliest visibility time)

            #we only want to add back observed pulsars that are still available
            observed_add_back = []

            for pulsar in observed:
                try:
                    this_priority_avail.remove(pulsar)
                    observed_add_back.append(pulsar)
                except ValueError:
                    pass

            observed_add_back.sort(key = lambda x : availabilities_dict[x][twind_ind][0])

            this_priority_avail = this_priority_avail + observed_add_back

            visible_matches[timewindow[0]] = this_priority_avail

            print("\t\t\tConstructing schedule for window...")

            for pulsar in this_priority_avail:
                obs_len = obstimedict[pulsar]

                pulsar_window = availabilities_dict[pulsar][twind_ind]

                if marker < pulsar_window[0]:
                    marker = pulsar_window[0]

                #if the pulsar isn't visible for long enough
                if pulsar_window[1] - pulsar_window[0] < datetime.timedelta(minutes = obs_len):
                    continue

                #if we don't have enough time to observe the pulsar
                if marker + datetime.timedelta(minutes = obs_len) > timewindow[1]:
                    continue

                schedule[timewindow[0]].append([pulsar, obs_len])

                if pulsar not in observed:
                    observed.append(pulsar)

                print("\t\t\t\tObserve P(" + str(priority) + ")", pulsar, "@", marker.strftime(time_string), "for {:.2f}".format(obs_len - OBS_BUFFER_TIME), "+", OBS_BUFFER_TIME, "\tmin")

                marker = marker + datetime.timedelta(minutes = obs_len)

    print("-" * 50)
    print("FINAL OBSERVING SCHEDULE:")
    for window in schedule:
        print("Starting @ " + window.strftime(time_string) + ":")
        for pulsar in schedule[window]:
            print("\tObserve " + pulsar[0] + "  for {:.2f}".format(pulsar[1] - OBS_BUFFER_TIME, 2), "+", OBS_BUFFER_TIME, "minutes")

    return schedule



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Create an observing schedule for target pulsars.')
    parser.add_argument('-w', '--windows', help = "Format, in minutes: start-end,start-end. Example: 0-60,120-180")

    args = parser.parse_args()

    if args.windows == None:
        args.windows = "0-60"

    windows = args.windows.split(",")
    windows = [[int(n) for n in el.split("-")] for el in windows]

    schedule = create_obs_schedule(PULSARS, windows)
