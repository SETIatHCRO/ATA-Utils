#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults, ata_sources, ata_pointing
import atexit
from SNAPobs import snap_dada, snap_if
from sigpyproc.Readers import FilReader
import numpy as np
import sys
import time
import datetime
import random

import argparse
import logging

import os
import glob
OBSDIR = '/mnt/buf0/obs'

NMAX = 5
ELMIN = 25
ELMAX = 75
nRepeats = 2

def select_group_sats(sats):
    setting_sats = [sat for sat in sats if 
            (sat['state'].lower() == 'setting' and
             float(sat['el']) < ELMAX and float(sat['el']) > ELMIN)]
    rising_sats  = [sat for sat in sats if 
            (sat['state'].lower() == 'rising' and
            float(sat['el']) < ELMAX and float(sat['el']) > ELMIN)]
    return setting_sats, rising_sats



def analyzeFivePoints(x, y):
    if (len(x) != 5 or len(y) != 5):
        raise RuntimeError("Input arrays must be 5 elements long.")

    # firstly, subtrack off background and constant offset
    back = (y[0] + y[4])/2.0
    offset = x[2]
    xminus = x[1] - offset
    xpeak = x[2] - offset
    xplus = x[3] - offset
    yminus = y[1] - back
    ypeak = y[2] - back
    yplus = y[3] - back

    if (ypeak <= 0.0):
        raise RuntimeError("The peak value is smaller than the background! Cannot find solution.");

    # calculate the exponential alpha from the angular full width at half max
    Delta = (xplus - xminus)/2.0
    alpha = np.abs(Delta) / np.sqrt(np.log(2.0))
    alpha2 = alpha*alpha

    # calculate first-order offset
    delta = alpha2 * np.log(yplus / yminus) / (4.0 * Delta)
    A = ypeak / np.exp(- delta*delta / alpha2)
    Dd = Delta - delta
    new_alpha = np.sqrt(Dd * Dd / np.log(A / yplus) * np.log(2.0))

    # last error check
    if (np.abs(delta) > np.abs(2*Delta)): 
        raise RuntimeError("Peak is not between yplus and yminus.")

    return delta + offset, A/back, new_alpha





def get_power(utc, ant):
    filfile = glob.glob(os.path.join(OBSDIR, utc, ant, "*x.fil"))[0]
    fil = FilReader(filfile)

    chans = np.linspace(fil.header.ftop, fil.header.fbottom, fil.header.nchans)
    block = fil.readBlock(0, fil.header.nsamples)
    bp = block.mean(axis=1)

    #args = (chans > 1678) & (chans < 1696)
    args = (chans > 1570) & (chans < 1580)

    power_inband = (bp[args]).sum()
    return power_inband


def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)
    
    ant_list = ['3c']
    #pms = {ant:ata_pointing.PointingModel(ant) for ant in ant_list}
    pm = ata_pointing.PointingModel('3c')

    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)

    pams = {ant+pol:27 for ant in ant_list for pol in ["x","y"]}
    ifs  = {ant+pol:27 for ant in ant_list for pol in ["x","y"]}

    ata_control.set_pams(pams)
    snap_if.setatten(ifs)
    freq = 1575

    snap_dada.set_freq_auto([freq]*len(ant_list), ant_list)

    obs_time = 10

    utcs = []
    sats_observed = []
    time_obs = []
    ofile = open("./atapointer.txt", "w")
    tpoint = open("./3c_tpoint.txt", "w")
    atexit.register(ofile.close)
    atexit.register(tpoint.close)
    while True:
        #utc = snap_dada.start_recording(ant_list, obs_time, acclen=120*16,
        #        disable_rfi=True)
        #utcs.append(utc)
        #for ant in ant_list:
        #    p = get_power(utc, ant)
        #    print(ant, p, 10*np.log10(p), "dB")
        sats = ata_sources.get_sats()['GPS']

        setting_sats, rising_sats = select_group_sats(sats)

        to_observe = None
        # select a rising satellite from rising group first
        # then check if there's any setting satellite, and observe
        # that instead. The rising satellite will be selected in the 
        # following iteration
        for sat_group in [rising_sats, setting_sats]:
            for sat in sat_group:
                name, az, el = sat['name'], float(sat['az']), float(sat['el'])

                # skip if satellite has been observed in the last 5 times
                if name in sats_observed[-5:]:
                    continue

                to_observe = sat
                #print("will observe: %s, state: %s" %(name, sat['state']))
                break

        # if all the satellites have been observed
        if not to_observe:
            # chose a random satellite that is setting, in case there's one
            if len(setting_sats) != 0:
                to_observe = random.choice(setting_sats)
            # else chose one that is rising, if there's one
            if len(rising_sats) != 0:
                to_observe = random.choice(rising_sats)

        if to_observe:
            az, el = float(sat['az']), float(sat['el'])
            name = sat['name']
            ofile.write("%s: Observing: %s\n" %(
                datetime.datetime.now(), to_observe['name']))
            ofile.write("%s: Az, el, state: %.2f, %.2f, %s\n" %(
                datetime.datetime.now(),az, el, sat['state']))
            ata_control.create_ephem(name, 
                    **{'duration': 2, 'interval': 1})

            pbfwhm = (3.5 / freq * 1000.0);
            delta = pbfwhm / 2.0
            obs_time = 30

            # elevation then azimuth
            offsets = [
                    [0., 4*delta],
                    [0., delta],
                    [0., 0.],
                    [0., -delta],
                    [0., -4*delta],
                    [-4*delta, 0.],
                    [-delta, 0.],
                    [0., 0.],
                    [delta, 0.],
                    [4*delta, 0.]
                    ]


            # offsets = az/el
            for i in range(nRepeats):
                azs = []
                els = []
                az_offs = []
                el_offs = []
                meas = []
                igrid = 0
                for offset in offsets:
                    ofile.write("%s %s" %(datetime.datetime.now(), offset))
                    ofile.write("\n")
                    ata_control.track_and_offset(name, ant_list, xoffset=offset)

                    az_el = ata_control.get_az_el(ant_list)['3c'] #XXX

                    # Determine the true position of satellite
                    x_el_off = offset[0]
                    el_off = offset[1]
                    az_off = x_el_off / np.cos(np.deg2rad(az_el[1]))

                    azs.append(az_el[0] - az_off)
                    els.append(az_el[1] - el_off)

                    az_offs.append(az_off)
                    el_offs.append(el_off)

                    time.sleep(30)
                    utc = snap_dada.start_recording(ant_list, obs_time, acclen=120*16,            
                            disable_rfi=True)
                    meas.append(get_power(utc, "3c"))

                az_avg = np.array(azs).mean()
                el_avg = np.array(els).mean()
                print(azs)
                print(els)
                print(az_offs)
                print(el_offs)
                print(meas)
                print(az_avg)
                print(el_avg)

                peak_el = analyzeFivePoints(el_offs[:5], meas[:5])
                peak_pos_el, peak_val_el, peak_width_el = peak_el

                peak_az = analyzeFivePoints(az_offs[5:], meas[5:])
                peak_pos_az, peak_val_az, peak_width_az = peak_az

                peak_sbr = np.sqrt(peak_val_az**2 + peak_val_el**2)

                print(peak_pos_el, peak_val_el, peak_width_el)
                print(peak_pos_az, peak_val_az, peak_width_az)

                meas_az = (az_avg + peak_pos_az)
                meas_el = (el_avg + peak_pos_el)

                meas_az, meas_el, ir = pm.applyTPOINTCorrections(meas_az, meas_el, 0)
                dt = datetime.datetime.now()
                hour = dt.hour + dt.minute/60.
                tpoint.write("! %.3f, %.3f, %.3f, %.3f, %.3f, %.3f\n"
                        %(az_avg, el_avg, meas_az, meas_el, peak_sbr, hour))

            sats_observed.append(to_observe['name'])
        else:
            # wait for 20 minutes and see what other satellite pops up
            ofile.write("%s: nothing to observe, waiting\n" %(
                datetime.datetime.now()))
            #sats_observed = []
            time.sleep(20*60)
        ofile.flush()
        #print(sats_observed)



if __name__ == "__main__":
    main()
