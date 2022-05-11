#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
import atexit
from SNAPobs import snap_dada, snap_if
import numpy as np
import sys
import time

import argparse
import logging

import os


def generate_ephem_el_swivel(az_start, el_start, el_end, t_start, t_span,  steps, invr):
    """
    Swivel along Elevation

    This function creates an ephemeris array to enable the antennas to swivel 
    across elevation at a particular azimuth

    Parameters 
    ----------
    az_start : float
               azimuth start
    el_start : float
               elevation start
    el_end   : float
               elevation end
    t_start  : float
               start time of the swivel. Note that it will be in ATA TAI seconds
    t_span   : float
               time span of the swivel in seconds
    steps    : float
               Number of data points required
    invr    :  float
               Inverse radius of the source

    Returns
    -------
    ephem : numpy_array
            Returns an array with 4 columns for time in TAI ns, azimuth, elevation 
            and inverse radius of the source
                
    Note
    ----
    ATA TAI is 37 seconds ahead of the current time

    """
    tai = np.linspace(t_start*1e9, (t_start + t_span)*1e9, steps)

    tai = np.round(tai).astype('int')

    el = np.linspace(el_start, el_end, steps)
    
    ir = np.array(steps*[invr])
    
    az = np.array(steps*[az_start])

    ephem = ((np.array([tai, az, el, ir], dtype=object)))
    
    return(ephem.T)



def generate_ephem_az_swivel(az_start, az_end, el_start, t_start, t_span,  steps, invr):
    """
    Swivel along Azimuth

    This function creates an ephemeris array to enable the antennas to swivel 
    across azimuth at a particular elevation

    Parameters 
    ----------
    az_start : float
               azimuth start
    az_end   : float
               azimuth end
    el_start : float
               elevation start
    t_start  : float
               start time of the swivel. Note that it will be in ATA TAI seconds
    t_span   : float
               time span of the swivel in seconds
    steps    : float
               Number of data points required
    invr    :  float
               Inverse radius of the source

    Returns
    -------
    ephem : numpy_array
            Returns an array with 4 columns for time in TAI ns, azimuth, elevation 
            and inverse radius of the source
                
    Note
    ----
    ATA TAI is 37 seconds ahead of the current time

    """
    tai = np.linspace(t_start*1e9, (t_start + t_span)*1e9, steps)

    tai = np.round(tai).astype('int')

    az = np.linspace(az_start, az_end, steps)
    
    ir = np.array(steps*[invr])
    
    el = np.array(steps*[el_start])

    ephem = ((np.array([tai, az, el, ir], dtype=object)))
    
    return(ephem.T)


def ephem_to_txt(save_as, ephem_file):
    """
    Ephemeris to text file

    This function exports the ephemeris array to a txt file

    Parameters
    ----------
    save_as    : string
                 file name to save the array as
    ephem_file : array
                 the ephemeris array to be exported as a txt file

    """
    ephemtxt = np.savetxt(save_as, ephem_file, fmt='%i  %.5f  %.5f  %.10E')

    return(ephemtxt)


def upload_ephemeris(ephemeris_filename):
    from ATATools import logger_defaults
    from ATATools.ata_rest import ATARest, ATARestException
    logger = logger_defaults.getModuleLogger(__name__)

    endpoint = '/ephemeris'

    try:
        with open(ephemeris_filename, 'r') as f:
            data = f.read()

        response = ATARest.put(endpoint, json={
            'ephemeris_filename': os.path.basename(ephemeris_filename),
            'ephemeris_data': data,
        })
        return response['id']

    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)
    
    ant_list = ['1k', '2a', '2b', '2c', '2e', '2j', '2m']
    lo = 'B'
    antlo_list = [ant+lo for ant in ant_list]

    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)
    

    pams = {ant+pol:27 for ant in ant_list for pol in ["x","y"]}
    ifs  = {antlo+pol:20 for antlo in antlo_list for pol in ["x","y"]}

    ata_control.set_pams(pams)
    snap_if.setatten(ifs)
    freq = 1600

    obs_time = 70

    ###snap_dada.set_freq_auto([freq]*len(ant_list), ant_list)
    ata_control.set_freq([freq]*len(ant_list), ant_list, lo='b')
    

    os.system("killall ata_udpdb")
        
    goes_az = 203.323 #121.96 (goes 16)
    goes_el = 40.119 #23.63


    #el swivel

    #az_start = goes_az
    #el_start = goes_el + 10
    #el_end   = goes_el - 10

    
    #az swivel

    el_start = goes_el # - 10
    az_start = goes_az - 10
    az_end   = goes_az + 10



    invr = 2.55e-5
    print("az: %.2f, el: %.2f" %(az_start, el_start))

    ata_control.set_az_el(ant_list, az_start, el_start)

    _ = input("enter to continue")

    grace_time = 15 # time between now and antenna actually moving

    t_start = time.time()
    t_start += 37 #leap seconds
    t_start += grace_time #let's start this in X seconds into the future

    t_span = 60 #seconds
    obs_time = int(t_span + 2*grace_time)

    steps = t_span // 5 #5 seconds per step

    #print(t_start)
    #print(t_span)
    
    #ephem = generate_ephem_el_swivel(az_start, el_start, el_end, t_start, t_span,  steps, invr)
    
    ephem = generate_ephem_az_swivel(az_start, az_end, el_start, t_start, t_span,  steps, invr)
    print(ephem)
    
    ephem_to_txt("test_ephem_goes17_az.txt", ephem)
    print("ephem file saved to disk")
    
    id = upload_ephemeris("test_ephem_goes17_az.txt")
    
    ata_control.track_ephemeris(id, ant_list)

    #t = time.time()
    utc = snap_dada.start_recording(antlo_list, obs_time,
            acclen=120, disable_rfi=True)
    #tt = time.time()

    #print(tt-t)

if __name__ == "__main__":
    main()
