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
import subprocess

OBSDIR = '/mnt/buf0/obs'

NMAX = 5
ELMIN = 25
ELMAX = 75
nRepeats = 2


def get_sun_pos():
    cmd = subprocess.Popen("ssh obs@control 'atacheck sun'", shell=True,
            stdout=subprocess.PIPE)
    stdout, stderr = cmd.communicate()
    s = stdout.decode("utf-8").strip()
    outlst = s.split("\n")

    if outlst[0].endswith("is up."):
        sun_is_up = True
    else:
        sun_is_up = False

    """
    this is ugly:
    output looks something like this:

    SUN is up.
    RA, Dec = 2.785, 16.008.
    Az, El = (120.251, 51.861): Tue May 04 17:48:16 UTC 2021 (LST 00:33:06.25).
    Rises > 16.5 deg          : Wed May 05 14:34:35 UTC 2021 (LST 21:22:50.17).
    Sets  < 16.5 deg          : Wed May 05 01:31:16 UTC 2021 (LST 08:17:22.79).

    """

    tmp_coords = outlst[2].split("(")[1].split(")")[0] # '120.251, 51.861'
    sun_az = float(tmp_coords.split(",")[0])
    sun_el = float(tmp_coords.split(",")[1])

    return sun_az, sun_el



def select_group_sats(sats):
    sun_az, sun_el = get_sun_pos()

    setting_sats = [sat for sat in sats if 
            (sat['state'].lower() == 'setting' and
             float(sat['el']) < ELMAX and float(sat['el']) > ELMIN and 
             abs(float(sat['el']) - sun_el) > 10 and abs(float(sat['az']) - sun_az) > 10 )]
    rising_sats  = [sat for sat in sats if 
            (sat['state'].lower() == 'rising' and
            float(sat['el']) < ELMAX and float(sat['el']) > ELMIN and
            abs(float(sat['el']) - sun_el) > 10 and abs(float(sat['az']) - sun_az) > 10 )]
    return setting_sats, rising_sats


def float_arr_to_str(arr):
    s = "["
    for i in arr:
        s += "%.3f " %float(i)
    s += "]"
    return s



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


def get_ephem_az_el(ephem, t1, t2):
    """
    t1 and t2 are in nanoseconds
    ephem is the ephemeris file (as a numpy array)
    return average az, el
    """
    ephem_sub = ephem[(ephem[:,0] > t1) & (ephem[:,0] < t2)]
    return np.mean(ephem_sub[:,1]), np.mean(ephem_sub[:,2])



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

def write_header(tpoint_file, pm, freq):
    tpoint_file.write("!  Invocation: python atapointer.py\n")
    tpoint_file.write("!  Antenna: ant%s\n" %pm.antName)
    tpoint_file.write("!  Tracking: GPS\n")
    tpoint_file.write("!  Frequency = %.1f\n" %freq)
    tpoint_file.write("!  AzOffset = %f\n" %pm.AzOffset)
    tpoint_file.write("!  ElOffset = %f\n" %pm.ElOffset)
    tpoint_file.write("!  IA = %f\n" %pm.mCoef.IA)
    tpoint_file.write("!  AN = %f\n" %pm.mCoef.AN)
    tpoint_file.write("!  AW = %f\n" %pm.mCoef.AW)
    tpoint_file.write("!  CA = %f\n" %pm.mCoef.CA)
    tpoint_file.write("!  NPAE = %f\n" %pm.mCoef.NPAE)
    tpoint_file.write("!  ACES = %f\n" %pm.mCoef.ACES)
    tpoint_file.write("!  ACEC = %f\n" %pm.mCoef.ACEC)
    tpoint_file.write("!  HASA2 = %f\n" %pm.mCoef.HASA2)
    tpoint_file.write("!  HACA2 = %f\n" %pm.mCoef.HACA2)
    tpoint_file.write("!  IE = %f\n" %pm.mCoef.IE)
    tpoint_file.write("!  ECES = %f\n" %pm.mCoef.ECES)
    tpoint_file.write("!  ECEC = %f\n" %pm.mCoef.ECEC)
    tpoint_file.write("!\n")
    tpoint_file.write(":NODA\n")
    tpoint_file.write(":ALLSKY\n")
    tpoint_file.write(":ALTAZ\n")
    tpoint_file.write("+41 49 02.3\n")
    tpoint_file.write("\n")
    tpoint_file.write("!  az_com, el_com, az_meas, el_meas, peak_SBR, hour ! offset_az, offset_el\n")
    #tpoint_file.write("!  az_ast, el_ast, az_eph, el_eph, az_off, el_off, az_gauss_width, el_gauss_width, peak_SBR, hour\n")

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)
    
    #ant_list = ['2b']
    #ant_list = ["1a", "1f", "1c", "2a", "2b", "2h",
    #        "3c", "4g", "1k", "5c", "1h", "4j"]
    ant_list = ["1a", "1f", "1c", "2a", "2b", "3d",
            "3c", "4g", "1k", "5c", "1h", "4j"]
    #ant_list = ["2a", "2b", "5c"]
    pms = {ant:ata_pointing.PointingModel(ant) for ant in ant_list}
    #pm = ata_pointing.PointingModel('3c')

    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)

    pams = {ant+pol:27 for ant in ant_list for pol in ["x","y"]}
    ifs  = {ant+pol:20 for ant in ant_list for pol in ["x","y"]}

    ata_control.set_pams(pams)
    snap_if.setatten(ifs)
    freq = 1575

    snap_dada.set_freq_auto([freq]*len(ant_list), ant_list)

    # define how to grid the sky
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

    obs_time = 20

    utcs = []
    sats_observed = []
    time_obs = []
    t = time.time()

    # create directory for the pointing
    os.mkdir("/home/obsuser/pointing/%i" %t)

    ofile = open("/home/obsuser/pointing/%i/%i_atapointer.txt" %(t,t), "w")
    tpoints = {ant:open("/home/obsuser/pointing/%i/%i_%s.tpoint" %(t,t,ant), "w") 
            for ant in ant_list}

    atexit.register(ofile.close)
    for tpoint in tpoints.values():
        atexit.register(tpoint.close)

    for ant in ant_list:
        tpoint_file = tpoints[ant]
        pm = pms[ant]
        write_header(tpoint_file, pm, freq)

    while True:
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
                ofile.write("will observe: %s, state: %s\n" %(name, sat['state']))
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

            ephem = ata_control.create_ephem(name, 
                    **{'duration': 2, 'interval': 1})
            ephem = np.array(ephem)

            # offsets = az/el
            for i in range(nRepeats):
                got_nan = False
                azs = {ant:[] for ant in ant_list}
                els = {ant:[] for ant in ant_list}
                az_offs = {ant:[] for ant in ant_list}
                el_offs = {ant:[] for ant in ant_list}
                meas = {ant:[] for ant in ant_list}
                igrid = 0

                t1 = time.time() * 1e9 #nanoseconds
                # now do the cross pattern
                for offset in offsets:
                    ofile.write("%s: %s" %(datetime.datetime.now(), offset))
                    ofile.write("\n")
                    ata_control.track_and_offset(name, ant_list, xoffset=offset)

                    for ant in ant_list:
                        # XXX: what az/el are these? Encoder or astronomical?
                        az_el = ata_control.get_az_el(ant_list)[ant]

                        # Determine the true position of satellite
                        x_el_off = offset[0]
                        el_off = offset[1]
                        az_off = x_el_off / np.cos(np.deg2rad(az_el[1]))

                        azs[ant].append(az_el[0] - az_off)
                        els[ant].append(az_el[1] - el_off)

                        az_offs[ant].append(az_off)
                        el_offs[ant].append(el_off)

                    # record data
                    utc = snap_dada.start_recording(ant_list, obs_time, acclen=120*16,            
                            disable_rfi=True)
                    # get the measurement data
                    for ant in ant_list:
                        try:
                            meas[ant].append(get_power(utc, ant))
                        except:
                            got_nan = True
                            meas[ant].append(np.nan)

                t2 = time.time()*1e9 #nanoseconds
                az_avg_src, el_avg_src = get_ephem_az_el(ephem, t1, t2)

                for ant in ant_list:
                    ofile.write(ant+"\n")
                    az_avg = np.array(azs[ant]).mean()
                    el_avg = np.array(els[ant]).mean()
                    ofile.write("%s: azimuths: "%(datetime.datetime.now()) + float_arr_to_str(azs[ant]) + "\n")
                    ofile.write("%s: elevations: "%(datetime.datetime.now()) + float_arr_to_str(els[ant]) + "\n")
                    ofile.write("%s: az_offsets: "%(datetime.datetime.now()) + float_arr_to_str(az_offs[ant]) + "\n")
                    ofile.write("%s: el_offsets: "%(datetime.datetime.now()) + float_arr_to_str(el_offs[ant]) + "\n")
                    ofile.write("%s: meas: "%(datetime.datetime.now()) + float_arr_to_str(meas[ant]) + "\n")
                    ofile.write("%s: source az_avg: "%(datetime.datetime.now()) + str(az_avg) + "\n")
                    ofile.write("%s: source el_avg: "%(datetime.datetime.now()) + str(el_avg) + "\n")
                    ofile.write("%s: source ephem az_avg: "%(datetime.datetime.now()) + str(az_avg_src) + "\n")
                    ofile.write("%s: source ephem el_avg: "%(datetime.datetime.now()) + str(el_avg_src) + "\n")

                    try:
                        peak_el = analyzeFivePoints(el_offs[ant][:5], meas[ant][:5])
                        peak_pos_el, peak_val_el, peak_width_el = peak_el

                        peak_az = analyzeFivePoints(az_offs[ant][5:], meas[ant][5:])
                        peak_pos_az, peak_val_az, peak_width_az = peak_az

                        peak_sbr = np.sqrt(peak_val_az**2 + peak_val_el**2)
                    except:
                        ofile.write("%s: Something went wrong with measuring power with ant: %s\n" %(datetime.datetime.now(), ant))
                        continue

                    ofile.write("El: %f %f %f\n" %(peak_pos_el, peak_val_el, peak_width_el))
                    ofile.write("Az: %f %f %f\n" %(peak_pos_az, peak_val_az, peak_width_az))

                    meas_az = (az_avg + peak_pos_az)
                    meas_el = (el_avg + peak_pos_el)

                    meas_az, meas_el, ir = pms[ant].applyTPOINTCorrections(meas_az, meas_el, 0)
                    dt = datetime.datetime.now()
                    hour = dt.hour + dt.minute/60.

                    tpoints[ant].write("%.3f, %.3f, %.3f, %.3f, %.3f, %.3f ! %.3f, %.3f\n"
                            %(az_avg, el_avg, meas_az, meas_el, peak_sbr, hour, peak_pos_az, peak_pos_el))
                    tpoints[ant].flush()

                if got_nan:
                    os.system("killall ata_udpdb")
                    os.system("bash ~/backends/frb_backend/snap_init_spec_skipprog.bash")

            sats_observed.append(to_observe['name'])
        else:
            # wait for 20 minutes and see what other satellite pops up
            print(rising_sats)
            print(setting_sats)
            ofile.write("%s: nothing to observe, waiting\n" %(
                datetime.datetime.now()))
            #sats_observed = []
            time.sleep(20*60)
        ofile.flush()
        #print(sats_observed)



if __name__ == "__main__":
    main()
