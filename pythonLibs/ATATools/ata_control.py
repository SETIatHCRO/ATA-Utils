#!/usr/bin/python3

"""
Python wrappers for various command calls controlling the ATA.

Most functions that allows array_list, if not specified otherwise,
allows both list of antennas call, e.g. ['1a','2c'], or 
comma separated string call, e.g. '1a,1b'

most functions are using logger to log warnings and are rising
various exceptions on error (most can raise RuntimeError if the 
system call fails)
"""

import re
import ast
import concurrent.futures
import os
from time import sleep
from threading import Thread

from . import ata_remote,ata_constants,snap_array_helpers,logger_defaults
from .ata_rest import ATARest, ATARestException


# Table to keep source offsets to provide backwards compatibility
# with this interface.
# This should only be accessed from within this code

_source_offset_table = {}


#use discouraged. Use more specific functions instead
def get_ascii_status():
    """
    Return an ascii table of lots of ATA
    status information.
    
    This call should only be used to display information, to get
    a particular information, other function should be used.
    (there is a white space separation between columns, but also
    there __MAY__ be white space separation within a column)
    """
    
    logger = logger_defaults.getModuleLogger(__name__)

    try:
        endpoint = '/status'
        response = ATARest.get(endpoint)
        return response['status']
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise


#####
#
# Followint is set of functions to control
# ata alarms. Ata alarms are information about
# starting/stopping new observation session. 
# Use with caution
#
#####

def get_alarm():
    """
    function querrys the ata alarm state 
    returns dictionary with fields: 
    - state
    - user
    - reason
    """
    logger = logger_defaults.getModuleLogger(__name__)

    try:
        endpoint = '/alarm'
        alarm_status = ATARest.get(endpoint)
        return alarm_status
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise
    

def set_alarm(reason, user):
    """
    function to set an ata alarm. be mindful about how it works
    and don't use any automatic scripts to set it up. 
    The alarm should be set to inform that you are starting working
    on the array (started your session, not your observation), 
    and should be unset after you finished your last observation
    The alarm internally sends mails to various users so please avoid 
    mail flood
    """
    logger = logger_defaults.getModuleLogger(__name__)

    try:
        endpoint = '/alarm'
        ATARest.put(endpoint, data={'user': user, 'reason': reason})
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

def unset_alarm(reason, user):
    """
    function to set an ata alarm. be mindful about how it works
    and don't use any automatic scripts to set it up. 
    The alarm should be set to inform that you are starting working
    on the array (started your session, not your observation), 
    and should be unset after you finished your last observation
    The alarm internally sends mails to various users so please avoid 
    mail flood
    """
    logger = logger_defaults.getModuleLogger(__name__)

    try:
        endpoint = '/alarm'
        reason = '{:s}: {:s}'.format(user, reason)
        ATARest.delete(endpoint, data={'reason': reason})
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise


#####
#
# Next functions are responsible for antenna
# tracking, information etc. Note separate section
# for ON-OFF specific ephemeris generation
#
#####

#backward compatibility. Don't use in new code
def getRaDec(ant_list):
    return get_ra_dec(ant_list)

#backward compatibility. Don't use in new code
def getAzEl(ant_list):
    return get_az_el(ant_list)

def get_ant_pos(ant_list):
    """
    get the NEU position of the antenna w.r.t telescope center
    returns dictionary with 1x3 list e.g. {'1a':[-74.7315    65.9487    0.5466]}
    """
    logger = logger_defaults.getModuleLogger(__name__)
    antstr = snap_array_helpers.input_to_string(ant_list) 

    try:
        endpoint = '/antennas/{:s}/locations'.format(antstr)
        ant_locs = ATARest.get(endpoint)
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

    retval = {}
    for antname in ant_list:
        loc = ant_locs[antname]
        retval[antname] = [loc['N'], loc['E'], loc['U']]

    return retval

def get_source_ra_dec(source, deg=True):
    """
    Get the J2000 RA / DEC of `source`. Return in decimal degrees (DEC) and hours (RA)
    by default, unless `deg`=False, in which case return in sexagesimal.
    """

    logger = logger_defaults.getModuleLogger(__name__)

    try:
        endpoint = '/source'
        source_data = ATARest.get(endpoint, json={'source': source})
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

    ra = source_data['ra']
    dec = source_data['dec']

    if deg:
        return ra, dec
    else:
        ram = (ra % 1) * 60
        ras = (ram % 1) * 60
        ra_sg = "%d:%d:%.4f" % (int(ra), int(ram), ras)
        decm = (dec % 1) * 60
        decs = (decm % 1) * 60
        dec_sg = "%+d:%d:%.4f" % (int(dec), int(decm), decs)
        return ra_sg, dec_sg

def get_ra_dec(ant_list):
    """
    get the Ra-Dec pointings of each antenna
    Ra is in decimal hours [0,24)
    Dec is in decimal degree [-90,90]
    returns dictionary with 1x2 list e.g. {'1a':[0.134 1.324]}
    """
    logger = logger_defaults.getModuleLogger(__name__)
    antstr = snap_array_helpers.input_to_string(ant_list) 

    try:
        endpoint = '/antennas/{:s}/radec'.format(antstr)
        antpos = ATARest.get(endpoint)
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

    retdict = {}
    for ant in ant_list:
        pos = antpos[ant]
        if pos:
            retdict[ant] = [pos['ra'], pos['dec']]
        else:
            logger.info('non-operational ant ' + ant)
            retdict[ant] = None

    return retdict

def get_az_el(ant_list):
    """
    get the Az-El pointings of each antenna
    Az is in decimal degree 
    Dec is in decimal degree 
    returns dictionary with 1x2 list e.g. {'1a':[0.134 1.324]}
    """
    logger = logger_defaults.getModuleLogger(__name__)
    antstr = snap_array_helpers.input_to_string(ant_list) 

    try:
        endpoint = '/antennas/{:s}/azel'.format(antstr)
        antpos = ATARest.get(endpoint)
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

    retdict = {}
    for ant in ant_list:
        pos = antpos[ant]
        if pos:
            retdict[ant] = [pos['az'], pos['el']]
        else:
            logger.info('non-operational ant ' + ant)
            retdict[ant] = None
    return retdict

def set_az_el(ant_list, az, el):
    """
    Set the antenna pointing to given Az-El
    Az is in decimal degree 
    Dec is in decimal degree 

    Function does not confirm if the values are set correctly. 
    Check it with get_az_el
    """
    logger = logger_defaults.getModuleLogger(__name__)
    antstr = snap_array_helpers.input_to_string(ant_list) 

    try:
        endpoint = '/antennas/{:s}/azel'.format(antstr)
        antpos = ATARest.put(endpoint, data={'az': az, 'el': el, 'wait': True})
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

def get_eph_source(antlist):
    """
    get the ephemeris file name of where the antennas are pointing
    returns dictionary e.g. {'1a':'casa'}
    """

    logger = logger_defaults.getModuleLogger(__name__)
    antstr = snap_array_helpers.input_to_string(antlist) 
    logger.info("getting sources: {}".format(antstr))

    try:
        endpoint = '/antennas/{:s}/sources'.format(antstr)
        sources = ATARest.get(endpoint)
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

    retdict = {}
    for ant in antlist:
        pos = sources[ant]
        if pos:
            retdict[ant] = pos
        else:
            logger.info('non-operational ant ' + ant)
            retdict[ant] = None
    return retdict

##################
#
# Low-level antena tracking related functions
#
# Most users should skip these and use the higher
# level functionality available in the section
# further on in this file
##################

def _set_ephemeris_defaults(ephemeris_args_dict):
    # Default ephemeris track point interval is 1 second

    if 'interval' not in ephemeris_args_dict:
        ephemeris_args_dict['interval'] = 1

    # Default ephemeris duration is 12 hours

    if 'duration' not in ephemeris_args_dict:
        ephemeris_args_dict['duration'] = 12

def generate_ephemeris(**kwargs):
    """
    Generate ephemeris for given source types

    :param kwargs: keyword args (see description below)
    :return: ephemeris ID (required for further operation)

    To generate ATA ephemeris from one of the following source types,
    supply the appropriate keyword with the value as listed:

    source=source_name : source_name is string name
       which can be catalog object, solar system body, NORAD number,
       satellite name.  Ex. source='casa'

    azel=[az,el] : value is a list of two floats, az and el (both in degrees).

    radec=[ra,dec] : value is a list of two floats, ra (hours) and dec (degs).

    tle=filename : filename is name of file containing TLE to be used.
    """
    logger = logger_defaults.getModuleLogger(__name__)
    ephem_sources = {'azel', 'radec', 'source', 'tle'}
    endpoint = '/ephemeris'

    try:
        source_count = 0
        for s in ephem_sources:
            if s in kwargs:
                source_count = source_count + 1
        if source_count != 1:
            raise Exception('generate_ephemeris() takes exactly one source type: ' + ephem_sources)

        _set_ephemeris_defaults(kwargs)
        result = ATARest.post(endpoint, json=kwargs)
        return result['id']

    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

def retrieve_ephemeris(ephemeris_id):
    """
    Retrieve specified ephemeris from the server

    :param ephemeris_id: ephemeris ID as returned by generate_ephemeris()
    :return: list of points, where each point is a list:
        [TAI_ns, az, el, inverse_range]
    """
    logger = logger_defaults.getModuleLogger(__name__)

    try:
        endpoint = '/ephemeris'
        ephem_file = ATARest.get(endpoint, json={'id': ephemeris_id})
        return ephem_file
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

def upload_ephemeris(ephemeris_filename):
    """
    Upload a custom generated ephemeris to the control server

    :param ephemeris_filename: name of existing file on local filesystem
    :return id of ephemeris on the server, suitable for track_ephemeris()
    :raises Exception on an parameter error or execution problem.
    """
    logger = logger_defaults.getModuleLogger(__name__)

    # Use the PUT operation on this endpoint

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

def track_ephemeris(ephemeris_id, antlist, wait=True):
    logger = logger_defaults.getModuleLogger(__name__)

    try:
        antstr = snap_array_helpers.input_to_string(antlist)
        #logger.info('Zeroing az/el offsets for ' + antstr)
        #endpoint = '/antennas/{:s}/offset'.format(antstr)
        #ATARest.put(endpoint, json={'azel': [0.0, 0.0]})

        logger.info('Tracking ephemeris {:s} with {:s}'.format(ephemeris_id, antstr))
        endpoint = '/antennas/{:s}/track'.format(antstr)
        #ATARest.put(endpoint, json={'id': ephemeris_id, 'wait': wait})
        ATARest.put(endpoint, json={'id': ephemeris_id, 
            'wait': wait, 'xoffset': [0.0, 0.0]})
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

def set_antennas_azel_offset(antlist, az_offset, el_offset, whence='absolute'):
    """
    Immediate set az/el offset in antennas

    :param antlist: list of antennas
    :param az_offset: az_offset to apply
    :param el_offset: el_offset to apply
    :param whence: 'absolute' or 'relative'

    This imediately changes the az/el offset currently applied to the antennas.
    An absolute offset is az/el offsets from 0 offset, which ultimately means
    relative to the individual antenna's PointingModel file.
    A relative offset, is a delta offset from whatever offset is currently
    applied in each antenna.
    """
    
    logger = logger_defaults.getModuleLogger(__name__)
    
    try:
        if whence not in ['absolute', 'relative']:
            raise Exception('set_antennas_azel_offset(): invalid whence ' + whence)
        antstr = snap_array_helpers.input_to_string(antlist)
        logger.info('Setting {:s} az/el offsets for '.format(whence, antstr))
        endpoint = '/antennas/{:s}/offset'.format(antstr)
        ATARest.put(endpoint, json={'azel': [float(az_offset), float(el_offset)]})

    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

##################
#
# mid-level antena tracking related functions
#
# Most users will find these satifactory for common needs
##################

def track_source(antlist, **kwargs):
    """
    Begin tracking a source (creates ephemeris and begins tracking it)

    :param kwargs: keyword args (see description below)
    :return: ephemeris ID (required for further operations)

    To track one of the following source types,
    supply the appropriate keyword with the value as listed:

    source=source_name : source_name is string name
       which can be catalog object, solar system body, NORAD number,
       satellite name.  Ex. source='casa'

    azel=[az,el] : value is a list of two floats, az and el (both in degrees).

    radec=[ra,dec] : value is a list of two floats, ra (hours) and dec (degs).

    tle=filename : filename is name of file containing TLE to be used.
    
    Additional keyword args:

    wait=bool : True value blocks until antennas are on source.
                This is the default, recommended for most uses.
    """
    logger = logger_defaults.getModuleLogger(__name__)
    wait_until_tracking = kwargs.pop('wait', True)

    try:
        ephem_id = generate_ephemeris(**kwargs)
        track_ephemeris(ephem_id, antlist, wait_until_tracking)
        return ephem_id
    except Exception as e:
        logger.error('track_source(): ' + str(e))
        raise
    

#discouraged in the future code
def make_and_track_ephems(source,antstr):
    return make_and_track_source(source,antstr)

def make_and_track_source(source, antstr, **ephem_kwargs):
    """
    set the antennas to track a source.
    source has to be a valid catalogue name
    the function call returns after the antennas are pointed.
    """
    logger = logger_defaults.getModuleLogger(__name__)
    try:
        endpoint = '/ephemeris'
        ephem_kwargs['source'] = source
        _set_ephemeris_defaults(ephem_kwargs)
        retval = ATARest.post(endpoint, json=ephem_kwargs)

        antstr = snap_array_helpers.input_to_string(antstr)
        logger.info("Tracking source {:s} with {:s}".format(source, antstr))
        ephem_id = retval['id']
        endpoint = '/antennas/{:s}/track'.format(antstr)
        ATARest.put(endpoint, json={'id': ephem_id, 'wait': True})
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

    # make_and_track_source() no longer returns status code

def make_and_track_tle(tle_filename, antstr, **ephem_kwargs):
    """
    Make an ephemeris file using the provided orbital
    Two-line-element (tle) file, and track the source
    using the ant list
    """
    logger = logger_defaults.getModuleLogger(__name__)
    try:
        # Read the contents of the TLE file
        with open(tle_filename, 'r') as f:
            data = f.read()

        endpoint = '/ephemeris'
        ephem_kwargs['tle'] = data
        _set_ephemeris_defaults(ephem_kwargs)
        retval = ATARest.post(endpoint, json=ephem_kwargs)

        antstr = snap_array_helpers.input_to_string(antstr)
        ephem_id = retval['id']
        logger.info("Tracking source {:s} with {:s}".format(ephem_id, antstr))
        endpoint = '/antennas/{:s}/track'.format(antstr)
        ATARest.put(endpoint, json={'id': ephem_id, 'wait': True})
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise


def make_and_track_ra_dec(ra, dec, antstr, **ephem_kwargs):
    """
    create ra-dec based ephemeris and track it with given antennas
    Ra is in decimal hours [0,24)
    Dec is in decimal degree [-90,90]
    the function call returns after the antennas are pointed.
    """
    logger = logger_defaults.getModuleLogger(__name__)
    antstr = snap_array_helpers.input_to_string(antstr)

    try:
        endpoint = '/ephemeris'
        ephem_kwargs['radec'] = [float(ra), float(dec)]
        _set_ephemeris_defaults(ephem_kwargs)
        retval = ATARest.post(endpoint, json=ephem_kwargs)

        ephem_id = retval['id']
        endpoint = '/antennas/{:s}/track'.format(antstr)
        ATARest.put(endpoint, json={'id': ephem_id, 'wait': True})
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise


#####
#
# Control of signal path (LNA, mixers, and such)
#
#####

def autotune(ants, power_level=-10.0, **kwargs):
    """
    calls autotune functionality (Power level for RF-Fiber conversion)
    on selected antennas.

    :param ants: either a list of antennas, e.g. ['1a','1b'] or comma separated string, e.g. '1a,1b'
    :param power: target power to tune to (dB)
    :param kwargs: keyword args dict of optional autotuning control parameters
    :keyword min_atten: minimum attenuation (default is 5.0 dB)
    :keyword course_atten: course searching attenuation change (default is 2.0 dB)
    :keyword tolerance: target power search tolerance (default is 1.0 dB)
    :raises Exception on parameter or execution errors
    """
    assert power_level < 0, "ataautotune: power level should be negative"
    logger = logger_defaults.getModuleLogger(__name__)
    antstr = snap_array_helpers.input_to_string(ants)

    if len(set(kwargs.keys()) - {'min_atten', 'course_atten', 'tolerance'}) > 0:
        logger.error('autotune(): bad args')
        raise Exception('autotune(): bad args')

    try:
        logger.info("autotuning: {}".format(ants))
        endpoint = '/antennas/{:s}/autotune2'.format(antstr)
        kwargs.update({'power': power_level})
        retval = ATARest.put(endpoint, data=kwargs)
        return retval
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

    #raise RuntimeError("Autotune execution error")

def set_pams(antdict):
    """
    set PAM attenuator values for given antennas

    the input value is a dictionary of the form:
    {'1ax': 28.0, '1ay': 28.0, '1fx': 17.0, '1fy': 15.5}
    """
    logger = logger_defaults.getModuleLogger(__name__)
    antpols = list(antdict.keys())
    for antpol in antpols:
        if not (antpol.endswith("x") or antpol.endswith("y")):
            raise RuntimeError("%s part of set_pams input dictionary"\
                    " has wrong value; antpols must end with 'x' or 'y'"\
                    %(antpol))

    ants_tmp = [antpol.strip("x").strip("y")
            for antpol in antpols]
    # very pythonic way to get unique antennas
    ants = list(set(ants_tmp))

    # this is being done sequentially, not the best
    # but the /antennas/1a,1f,3c/pams endpoint does not
    # seem to work
    for ant in ants:
        json = {}
        if ant+"x" in antdict.keys():
            json["x"] = {'x': True, 'value': antdict[ant+"x"]}
        if ant+"y" in antdict.keys():
            json["y"] = {'y': True, 'value': antdict[ant+"y"]}

        try:
            ret = ATARest.put("/antenna/%s/pams" %ant, json=json)
        except Exception as e:
            logger.error("set_pams got error: {}".format(str(e)))
            raise

def get_pams(antlist):
    """
    get PAM attenuator values for given antennas

    the return value is a dictionary:
    e.g. {'ant1ax':12.5,'ant1ay':20,'ant2ax':11,'ant2ay':13}
    """

    def sum_front_back(pams):
        return pams['front'] + pams['back']

    logger = logger_defaults.getModuleLogger(__name__)
    antstr = snap_array_helpers.input_to_string(antlist) 
    logger.info("getting pams: {}".format(antstr))

    try:
        pams = ATARest.get('/antennas/{:s}/pams'.format(antstr))
    except Exception as e:
        logger.error("get_pams got error: {}".format(str(e)))
        raise
    
    retdict = {}
    for ant in antlist:
        pams_for_ant = pams[ant]
        if pams_for_ant:
            try:
                retdict[ant + 'x'] = sum_front_back(pams_for_ant['x'])
                retdict[ant + 'y'] = sum_front_back(pams_for_ant['y'])
            except Exception as e:
                logger.warning('bad PAMS dict: ' + pams_for_ant)
                raise
            
    return retdict

def get_dets(antlist):
    """
    get PAM detector values for given antennas

    the return value is a dictionary:
    e.g. {'ant1ax':0.23,'ant1ay':0.2,'ant2ax':0.11,'ant2ay':0.83}

    """
    logger = logger_defaults.getModuleLogger(__name__)
    antstr = snap_array_helpers.input_to_string(antlist) 
    logger.info("getting dets: {}".format(antstr))

    try:
        endpoint = '/antennas/{:s}/det'.format(antstr)
        dets = ATARest.get(endpoint)
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

    retdict = {}
    for ant in antlist:
        dets_for_ant = dets[ant]
        if dets_for_ant:
            try:
                retdict[ant + 'x'] = dets_for_ant['x']
                retdict[ant + 'y'] = dets_for_ant['y']
            except Exception as e:
                logger.warning('bad dets dict: ' + dets_for_ant)
                raise

    return retdict


def get_lnas(ant_list):
    """
    Get status of LNAs for a list of antennas

    Parameters
    ----------
    ant_list : list
        List of antenna names, e.g. ['1a', '2b']

    Returns
    -------
    Dict
        A dictionary mapping with keys being antenna names, and
        values being another dictionary with keys being 'x', 'y',
        and 'on'.
    """
    logger = logger_defaults.getModuleLogger(__name__)

    antstr = ",".join(ant_list)
    endpoint = f'/antennas/{antstr}/lnas'

    try:
        lna_status = ATARest.get(endpoint)
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

    return lna_status


def try_on_lna(singleantstr):
    """
    check if the LNA for given antenna is on. 
    if LNA was already on, nothing happens
    if LNA was off, the pams are set to default value (30 dB)
    and then LNA is switched on

    for mutliple antennas, call try_on_lnas
    """

    paxstartdefault = 30.0
    wasError = False
    logger = logger_defaults.getModuleLogger(__name__)
    
    antstr = snap_array_helpers.input_to_string(singleantstr) 

    try:
        endpoint = '/antenna/{:s}/lnas'.format(antstr)
        lna = ATARest.get(endpoint)
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

    if not lna['on']:
        logger.warning('LNA {} is OFF'.format(singleantstr))
        logger.info('Setting pax to {}'.format(paxstartdefault))

        try:
            endpoint = '/antenna/{:s}/pams'.format(antstr)
            args = {'x': {'on': True, 'value': paxstartdefault},
                    'y': {'on': True, 'value': paxstartdefault}}
            ATARest.put(endpoint, json=args)
        except Exception as e:
            logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
            raise

        logger.info('switching on the LNA')
        try:
            endpoint = '/antenna/{:s}/lnas'.format(antstr)
            ATARest.put(endpoint, json={'on': True})
        except Exception as e:
            logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
            raise

    else:
        logger.info('LNA was already on')

def try_on_lnas(ant_list):
    """
    a multithread call for try_on_lna
    """
    logger = logger_defaults.getModuleLogger(__name__)
    ant_list = snap_array_helpers.input_to_list(ant_list) 
    tcount = len(ant_list)

    logger.info("starting concurrent execution of try_on_lna with {} workers".format(tcount))

    with concurrent.futures.ThreadPoolExecutor(max_workers=tcount) as executor:
    #with concurrent.futures.ProcessPoolExecutor(max_workers=tcount) as executor:
        tlist = []
        for singleantstr in ant_list:

            t = executor.submit(try_on_lna,singleantstr)
            tlist.append(t)

        for t in tlist:
            retval = t.result()

def get_sky_freq(lo='a'):
    """
    Return the sky frequency (in MHz) currently
    tuned to the center of the ATA band
    """
    lo = lo.lower()
    return ATARest.get('/lo1/skyfreq/' + lo)[lo]

def set_freq_focus(freq, ants, calibrate=False):
    """
    sets the feed focus for given antennas. 
    This call is done automatically when calling set_freq, 
    however, when in piggyback mode, when set_freq can't be called
    set_freq_focus should still be called to ensure that feed is 
    moved to a desired position.
    By default no feed position calibration is executed, but 
    this behaviour can be changed
    function return immediately, but it may take a bit more time 
    to actually set the focus
    """
    logger = logger_defaults.getModuleLogger(__name__)
    ants = snap_array_helpers.input_to_string(ants) 
    endpoint = '/antennas/{:s}/focus'.format(ants)

    # Calibrate is ignored for now, since the REST call
    # currently attempts to auto cal whenever needed
    
    try:
        ATARest.put(endpoint, data={'value': freq})
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

def get_freq_focus(ant_list):
    """
    get the antenna frequency focus (feed position).
    This call is done automatically while calling get_freq
    The intention of this function is to make sure that the focus
    in piggyback mode is set correctly to the observation frequency.
    Note that due to the step motor accuracy, the actual focus is not 
    exactly equal to requested value.
    e.g. requesting 2000 MHz may end up with {'1a': 2000.2057161454934}

    returns dictionary with a value for each requested antenna (or NaN string)
    """
    logger = logger_defaults.getModuleLogger(__name__)
    antstr = snap_array_helpers.input_to_string(ant_list)

    endpoint = '/antennas/{:s}/focus'.format(antstr)
    try:
        focus_data = ATARest.get(endpoint)
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise
        
    retdict = {}
    for ant, focus in focus_data.items():
        # Return only short names like '1a'
        ant = ant.replace('ant', '')
        retdict[ant] = focus
    return retdict

def set_freq(freq, antlist, lo='a', nofocus=False):
    """
    Sets both LO frequency and antenna focus frequency to
    given freq in MHz
    """

    antstring = snap_array_helpers.input_to_string(antlist)
    logger = logger_defaults.getModuleLogger(__name__)
    lo = lo.lower()
    if lo not in ['a','b','c','d']:
        raise RuntimeError("LO provided (%s) is not in [a,b,c,d]" %lo)

    # Set LO tuning skyfreq

    try:
        ATARest.put('/lo1/skyfreq/' + lo, data={'value': freq})
    except Exception as e:
        logger.error(str(e))
        raise

    # Set ant focus
    if not nofocus:
        set_freq_focus(freq, antlist)

def get_freq(ant_list, lo='a'):
    """
    gets the LO and focus frequency in MHz
    for every antenna
    returns a dictionary with a list as values, i.e. {'1a': [1400,1400]}
    """
    logger = logger_defaults.getModuleLogger(__name__)
    antstr = snap_array_helpers.input_to_string(ant_list)
    retdict = {}

    # get LO freq

    try:
        skyfreq = get_sky_freq(lo)
    except Exception as e:
        logger.error('Error getting skyfreq {:s} - {:s}'.format(lo, str(e)))
        raise

    for ant in ant_list:
        retdict[ant] = [skyfreq]

    # get focus frequency

    try:
        focuses = ATARest.get('/antennas/{:s}/focus'.format(antstr))
    except Exception as e:
        logger.error('Error getting focus{:s} - {:s}'.format(antstr, str(e)))
        raise
        
    for ant in ant_list:
        focusfreq = focuses[ant]
        if not focusfreq:
            focusfreq = "NaN"
        else:
            retdict[ant].append(focusfreq)

    return retdict

#####
#
# Next couple of functions are dedicated
# To resource management (reserving/releasing antennas)
# release antennas should be called at the end of observation
# exception-proof (ie. called even if the code is doing 
# unexpected things)
#
#####

def _test_all_antennas_in_str(lines, antlist):
    """
    test if all antennas from antlist are in white space separated lines. returns difference between sets
    empty set means all antennas from the list were in the line
    """
    aset = set(antlist)
    antsinline = set(lines.split())
    setdiff = aset - antsinline
    return list(setdiff)

def list_antenna_group(ant_group):
    """
    list all antennas in the given group
    returns antenna list
    """
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("Querying group {}".format(ant_group))

    try:
        rval = ATARest.get('/sa/ls/' + ant_group)
    except Exception as e:
        logger.error("ERROR while listing group {} : {}".format(ant_group,stdout.decode()))
        raise RuntimeError("ERROR while listing group {} : {}".format(ant_group,stdout.decode()))

    return rval

def list_released_antennas():
    """
    list all antennas in the 'none' group
    returns antenna list
    """
    return list_antenna_group('none');

def list_reserved_antennas():
    """
    list all antennas in the 'bfa' group
    returns antenna list
    """
    return list_antenna_group('bfa');

def list_maintenance_antennas():
    """
    list all antennas in the 'maint' group
    returns antenna list
    """
    return list_antenna_group('maint');

def move_ant_group(antlist, from_group, to_group):
    """
    call to move antennas between two sals groups
    see: reserve_antennas, release_antennas
    
    raises RuntimeError if the move is not possible
    """
    logger = logger_defaults.getModuleLogger(__name__)
    antlist = snap_array_helpers.input_to_list(antlist) 
    antset = frozenset(antlist)
    antstr = snap_array_helpers.array_to_string(antlist)
    logger.info("Reserving \"{}\" from {} to {}".format(antstr, from_group, to_group))

    try:
        ants_in_group = frozenset(list_antenna_group(from_group))
        if not antset.issubset(ants_in_group):
            err = "Antennas {} are not in group {}".format(str(antset - ants_in_group), from_group)
            logger.error(err)
            raise RuntimeError(err)

        ATARest.put('/sa/give/{:s}/{:s}/{:s}'.format(from_group, to_group, antstr))
        ants_in_group = frozenset(list_antenna_group(to_group))
        if not antset.issubset(ants_in_group):
            err = "Failed to move antennas {} to group {}".format(str(antset - ants_in_group), to_group)
            logger.error(err)
            raise RuntimeError(err)

    except ATARestException as e:
        err = 'Error while working with subarrays - ' + str(e)
        logger.error(err)
        raise RuntimeError(err)

"""
def move_ant_group_old(antlist, from_group, to_group):

    assert isinstance(antlist,list),"input parameter not a list"

    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("Reserving \"{}\" from {} to {}".format(snap_array_helpers.array_to_string(antlist), from_group, to_group))
    
    stdout, stderr = ata_remote.callProg(["antreserve", from_group, to_group] + antlist)

    bfa = None
    lines = stdout.decode().split('\n')
    for line in lines:
        cols = line.split()
        if (len(cols) > 0) and (cols[0]  == to_group):
            bfa = cols[1:]
    for ant in antlist:
        if ant not in bfa:
            logger.error("Failed to move antenna {} from {} to {}".format(ant, from_group, to_group))
            raise RuntimeError("Failed to move antenna {} from {} to {}".format(ant, from_group, to_group))
"""

def reserve_antennas(antlist):
    """
    move antennas from group none to bfa
    this function should be called before any other function call
    changing the antenna settings. If call fails, that measn the
    antennas were already in use by someone
    """
    move_ant_group(antlist, "none", "bfa")

def release_antennas(antlist, should_park=True):
    """
    move antennas from group bfa to none
    this function should be called at the end of observations, 
    most likely in the "finally" statement to ensure it's always executed

    failing to call the release means that any other user will
    see the antennas as "still in use"

    should_park flag determines if the antennas should be
    moved to default position, or leave it be (usefull for code debugging
    to cut down the antenna movement time)
    """

    move_ant_group(antlist, "bfa", "none")

    if(should_park):
        park_antennas(antlist)

    return

def park_antennas(antlist):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("Parking ants");
    antstr = snap_array_helpers.input_to_string(antlist) 

    try:
        endpoint = '/antennas/{:s}/park'.format(antstr)
        ATARest.put(endpoint, data={'wait': True})
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise
    logger.info("Parked");


def check_windsocking():
    logger = logger_defaults.getModuleLogger(__name__)

    try:
        endpoint = '/windsocking'
        windsocking_status = ATARest.get(endpoint)
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise
    logger.debug('{:s}: {:s}'.format(endpoint, str(windsocking_status)))
    return windsocking_status.get('windsocking_active', False)

_notifier_callback_list = []
_notifier_windsocking_state = False

def windsocking_notifier(callback_or_callback_list):
    """
    Background windsocking event notifier.

    You should start only one of these in your observation application code.
    The argument may be a callback routine, or a list [] of callback routines.
    These callback routines will be called whenever there is a change in
    windsocking status.

    Callback routines should be simple functions/methods with a single boolean
    parameter "is_windsocking", where True will indicate windsocking has
    begun, and False is windsocking is ended.

    # Define a callback

    def my_callback(is_windsocking):
        some_important_flag = is_windsocking
        if is_windsocking:
           maybe_pause_my_observation_or_do_something_important()

    # Register the callback and start the notifier thread

    windsocking_notifier(my_callback)

    # Now my app will receive windsock event callbacks....

    """
    logger = logger_defaults.getModuleLogger(__name__)

    global _notifier_windsocking_state

    def windsocking_watcher():
        while True:
            try:
                new_status = check_windsocking()
                logger.debug('windsocking status: ' + str(new_status))
                global _notifier_windsocking_state
                if new_status != _notifier_windsocking_state:
                    _notifier_windsocking_state = new_status
                    for callback in _notifier_callback_list:
                        callback(new_status)
            except:
                pass
            sleep(15.0)

    if isinstance(callback_or_callback_list, list):
        _notifier_callback_list = callback_or_callback_list.copy()
    else:
        _notifier_callback_list = [callback_or_callback_list]
    _notifier_windsocking_state = check_windsocking()
    Thread(target=windsocking_watcher, daemon=True).start()

#####
#
# The following functions are contoling the "older" snaps 
# that are connected via RF-switch. They should probably 
# be moved to backend-dependent code
#
#####

def get_snap_dictionary(array_list):
    """
    returns the dictionary for snap0-3 antennas. This is suggested way of 
    knowing which antennas are connected to which snap via rfswitch.

    The input value is a list of antennas, e.g. ['1a','2c']
    the return value is a dictionary of lists, e.g.
    {'snap0':['1a',1b'],'snap2':['5c']}

    Raises KeyError if antenna is not in known/not connected
    """
    s0 = []
    s1 = []
    s2 = []
    for ant in array_list:
        if ant in ata_constants.snap0ants:
            s0.append(ant)
        elif ant in ata_constants.snap1ants:
            s1.append(ant)
        elif ant in ata_constants.snap2ants:
            s2.append(ant)
        else:
            raise KeyError("antenna unknown")

    retval = {}
    if s0:
        retval['snap0'] = s0
    if s1:
        retval['snap1'] = s1
    if s2:
        retval['snap2'] = s2

    return retval

def rf_switch_thread(ant_list):
    """
    start a thread to set rf switch,
    ant list should consist of antennas from separate snaps

    the call execute parallel threads for each RF switch.
    and internally calls set_rf_switch
    """

    logger = logger_defaults.getModuleLogger(__name__)
    ant_list = snap_array_helpers.input_to_list(ant_list) 
    tcount = len(ant_list)

    logger.info("starting concurrent execution of set_rf_switch with {} workers".format(tcount))

    with concurrent.futures.ThreadPoolExecutor(max_workers=tcount) as executor:
    #with concurrent.futures.ProcessPoolExecutor(max_workers=tcount) as executor:
        tlist = []
        for cant in ant_list:

            t = executor.submit(set_rf_switch,[cant])
            tlist.append(t)

        for t in tlist:
            retval = t.result()

    return

def set_rf_switch(ant_list):
    """
    Set RF switch `switch` (0..1) to connect the COM port
    to port `sel` (1..8) based on antenna call. 

    Calling this function on multiple antenna may be slow, consider calling
    rf_switch_thread
    """
    logger = logger_defaults.getModuleLogger(__name__)

    ants = snap_array_helpers.input_to_string(ant_list) 

    stdout, stderr = ata_remote.callSwitch(['rfswitch',ants])

    for line in stdout.splitlines():
        logger.info("Set rfswitch for ants %s result: %s" % (ants, line))
    
    if stderr.startswith(b"OK"):
        logger.info("Set rfswitch for ants %s result: SUCCESS" % ants)
        return
    else:
        logger.error("Set switch 'rfswitch %s' failed!" % ants)
        logger.error(stdout)
        logger.error(stderr)
        raise RuntimeError("Set switch 'rfswitch %s' failed!" % (ants))

def set_atten_thread(antpol_list_list, db_list_list):
    """
    start a thread to set attenuator value
    each list member should be from separate snaps
    
    eg. set_atten_thread([['1ax','1ay'],['5ax','5ay']],[[12,12],[13,15]])
    It's possible to set only one polarization. Second parameter is
    attenuation value in dB. The shape of db_list_list must match the 
    shape of antpol_list_list

    the call execute parallel threads for each attenuator.
    and internally calls set_atten
    """

    logger = logger_defaults.getModuleLogger(__name__)
    tcount = len(antpol_list_list)
    if(len(antpol_list_list) != len(db_list_list)):
        logger.error("set_atten_thread, antenna list list length != db_list list length.")
        raise RuntimeError("set_atten_thread, antenna list list length != db_list list length.")

    logger.info("starting concurrent execution of set_atten with {} workers".format(tcount))
    with concurrent.futures.ThreadPoolExecutor(max_workers=tcount) as executor:
    #with concurrent.futures.ProcessPoolExecutor(max_workers=tcount) as executor:
        tlist = []
        for ii in range(tcount):
            antpol_list = antpol_list_list[ii]
            db_list = db_list_list[ii]
            if(len(antpol_list) != len(db_list)):
                logger.error("set_atten_thread, antenna list length != db_list length.")
                raise RuntimeError("set_atten_thread, antenna list length != db_list length.")

            t = executor.submit(set_atten,antpol_list, db_list)
            tlist.append(t)

        for t in tlist:
            retval = t.result()

    return

def set_atten(antpol_list, db_list):
    """
    Set attenuation of antenna or ant-pol `ant`
    to `db` dB.
    Allowable values are 0.0 to 31.75

    Calling the function for multiple antennas may be slow. consider calling 
    set_atten_thread instead
    """

    assert isinstance(antpol_list,list),"input parameter not a list"
    assert isinstance(db_list,list),"input parameter not a list"

    antpol_str = ",".join(antpol_list)
    db_str = ",".join(map(str,db_list))

    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("setting rfswitch attenuators %s %s" % (db_str, antpol_str))

    stdout, stderr = ata_remote.callSwitch(["atten",db_str,antpol_str])

    output = ""
    # Log the result
    for line in stdout.splitlines():
        output += "%s\n" % line
        logger.info("Set atten for ant %s to %s db result: %s" % (antpol_str, db_str, line))

    if stderr.startswith(b"OK"):
        logger.info("Set atten for ant %s to %s db result: SUCCESS" % (antpol_str, db_str))
        return output
    else:
        logger.error("Set attenuation 'atten %s %s' failed! (STDERR=%s)" % (db_str, antpol_str,stderr))
        raise RuntimeError("ERROR: set_atten %s %s returned: %s" % (db_str, antpol_str, stderr))


#####
#
# Be careful when using the following functions 
# They are mainly used for on-off modification
# and are very specific for that case
#
#####

_create_ephem_offset_source = None
def create_ephem(source, **ephem_kwargs):
    logger = logger_defaults.getModuleLogger(__name__)
    endpoint = '/ephemeris'

    global _create_ephem_offset_source
    _create_ephem_offset_source = source

    try:
        ephem_kwargs['source'] = source
        _set_ephemeris_defaults(ephem_kwargs)
        print(ephem_kwargs)
        retval = ATARest.post(endpoint, json=ephem_kwargs)
        ephem_id = retval['id']
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

    endpoint = '/ephemeris'
    try:
        ephem_file = ATARest.get(endpoint, json={'id': ephem_id})
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

    return ephem_file


def track_and_offset(source, antstr, **ephem_kwargs):
    logger = logger_defaults.getModuleLogger(__name__)
    assert source == _create_ephem_offset_source
    try:
        antstr = snap_array_helpers.input_to_string(antstr)
        logger.info("Tracking source {:s} with {:s}".format(source, antstr))
        ephem_id = source
        json = {'id': ephem_id, 'wait': True}
        json.update(ephem_kwargs)
        endpoint = '/antennas/{:s}/track'.format(antstr)
        ATARest.put(endpoint, json=json)
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise


# This variable is used to store the ephemeris id generated in
# create_ephems() to be used later in point_ants().

_create_ephems_source_name = None

def create_ephems(source, az_offset, el_offset):
    """
    a script call to create 2 ephemeris files, one on target, one
    shifted by az_ and el_offset. Mainly used for ON-OFF observations
    together with point_ants function
    
    if multiple observers use that at a time, the call in ambigous and you may not point into desired source
    safer option is to use point_ants2
    """
    global _create_ephems_source_name
    _create_ephems_source_name = source
    return create_ephems2(source, az_offset, el_offset)


def point_ants(on_or_off, ants):
    """
    on_or_off is a string, either "on" or "off". If "on", the antennas are pointed to the source
    if "off", the antennas are pointed away from the source by az_ and el_offset given to create_ephems 

    requires earlier call of create_ephems
    if multiple observers use that at a time, the call in ambigous and you may not point into desired source
    safer option is to use point_ants2
    """
    return point_ants2(_create_ephems_source_name, on_or_off, ants)


# This variable is used to store the ephemeris id generated in
# create_ephems2_radec() to be used later in point_ants2_radec().

_create_ephems2_radec_source_id = None

def create_ephems2_radec(ra,dec,az_offset,el_offset, **ephem_kwargs):
    """
    JSK: edited version of 'create_ephems2' to use 'radec_on' and off
    ephem files
    a script call to create 2 ephemeris files, one on target, one
    shifted by az_ and el_offset. Mainly used for ON-OFF observations
    together with point_ants2_radec function
    """
    logger = logger_defaults.getModuleLogger(__name__)
    endpoint = '/ephemeris'
    
    try:
        ephem_kwargs['radec'] = [float(ra), float(dec)]
        _set_ephemeris_defaults(ephem_kwargs)
        retval = ATARest.post(endpoint, json=ephem_kwargs)
        ephem_id = retval['id']
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

    # Internally store the requested offsets for later use
    # since the interface has changed to no longer require
    # an actual second offset ephemeris, but can be adjusted at tracking time

    _source_offset_table[ephem_id] = [az_offset, el_offset]

    # Save the generated ephemeris ID for later call
    # to point_ants2_radec()

    global _create_ephems2_radec_source_id
    _create_ephems2_radec_source_id = ephem_id

    # Return the ephemeris id stored on the control computer
    # This value can be ignored for this pair of routines
    # (create_ephems2, point_ants2)

    return ephem_id


def point_ants2_radec(ra,dec, on_or_off, ants):
    """
    JSK: edited version of 'point_ants' to use 'radec_on' and off
    ephem files
    on_or_off is a string, either "on" or "off". If "on", the antennas are pointed to the source
    if "off", the antennas are pointed away from the source by az_ and el_offset given to create_ephems2_radec

    requires earlier call of create_ephems
    """

    return point_ants2(_create_ephems2_radec_source_id, on_or_off, ants)


def create_ephems2(source, az_offset, el_offset, **ephem_kwargs):
    """
    WF: edited version of 'create_ephems' to use '$sourcename_on' and off
    ephem files
    a script call to create 2 ephemeris files, one on target, one
    shifted by az_ and el_offset. Mainly used for ON-OFF observations
    together with point_ants function
    """

    logger = logger_defaults.getModuleLogger(__name__)
    endpoint = '/ephemeris'
    
    try:
        ephem_kwargs['source'] = source
        _set_ephemeris_defaults(ephem_kwargs)
        retval = ATARest.post(endpoint, json=ephem_kwargs)
        ephem_id = retval['id']
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

    # Internally store the requested offsets for later use
    # since the interface has changed to no longer require
    # an actual second offset ephemeris, but can be adjusted at tracking time

    _source_offset_table[ephem_id] = [az_offset, el_offset]

    # Return the ephemeris id stored on the control computer
    # This value can be ignored for this pair of routines
    # (create_ephems2, point_ants2)

    return ephem_id

def point_ants2(source, on_or_off, ant_list, **ephem_kwargs):
    """
    WF: edited version of 'point_ants' to use '$sourcename_on' and off
    ephem files
    on_or_off is a string, either "on" or "off". If "on", the antennas are pointed to the source
    if "off", the antennas are pointed away from the source by az_ and el_offset given to create_ephems 

    requires earlier call of create_ephems
    """
    logger = logger_defaults.getModuleLogger(__name__)
    antstr = snap_array_helpers.input_to_string(ant_list) 

    # Ephemeris id is mandatory of course
    # source_name emulates the ATA status display of ephemeris file
    # with the _on or _off suffix

    source_name = '{:s}_{:s}'.format(source, on_or_off)
    ephem_kwargs['id'] = source
    ephem_kwargs['name'] = source_name
    ephem_kwargs['wait'] = True

    # If off source pointing is requested, alter the track at runtime
    # by the previously stored az/el offset

    print(_source_offset_table)
    print(source)
    print(on_or_off)
    
    if on_or_off == 'off':
        offsets = _source_offset_table.get(source)
        print(offsets)
        if not offsets:
            raise Exception('point_ants2(): source {:s} was not previously generated'.format(source))
        ephem_kwargs['offset'] = offsets

    try:
        endpoint = '/antennas/{:s}/track'.format(antstr)
        ATARest.put(endpoint, json=ephem_kwargs)
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

    # This used to return a process exit code which no longer applies
    

if __name__== "__main__":

    print(get_pams("ant1a"))

    #send_email("Test subject", "Test message")
    #logger = logging.getLogger(snap_onoffs_contants.LOGGING_NAME)
    #logger.setLevel(logging.INFO)
    #sh = logging.StreamHandler(sys.stdout)
    #fmt = logging.Formatter('[%(asctime)-15s] %(message)s')
    #sh.setFormatter(fmt)
    #logger.addHandler(sh)

    #print set_freq(2000.0, "2a,2b")
    #print set_atten("2jx,2jy", "10.0,10.0")
    #print create_ephems("casa", 10.0, 5.0)
    #print point_ants("on", "1a,1b")
    #print point_ants("off", "1a,1b")
    print('foo')
