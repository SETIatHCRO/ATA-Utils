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
from . import ata_remote,ata_constants,snap_array_helpers,logger_defaults

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
    
    stdout, stderr = ata_remote.callObs(["ataasciistatus","-l"])
    return stdout

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
    - trigger
    - state
    - user
    - reason
    """
    logger = logger_defaults.getModuleLogger(__name__)
    str_out,str_err = ata_remote.callObs(['atagetalarm','-l'])
    if str_err:
        logger.error("atagetalarm got error: {}".format(str_err))

    retdict = {}
    lines = str_out.splitlines()
    for line in lines:
        regroups = re.search('(?P<trig>\w*)/(?P<com>\w*)\s*:\s*(?P<user>\w*)\s*:\s*(?P<reason>.*)',line.decode());
        if regroups:
            retdict['trigger'] = regroups.group('trig')
            retdict['state'] = regroups.group('com')
            retdict['user'] = regroups.group('user')
            retdict['reason'] = regroups.group('reason')
        else:
            logger.warning('unable to parse line: {}'.format(line))

    return retdict

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
    return _setalarm(reason,user,'on')

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
    return _setalarm(reason,user,'off')

def _setalarm(reason, user=None, alarmstate='off'):
    """
    This is an internal function. Should not be called by the user!
    """
    
    logger = logger_defaults.getModuleLogger(__name__)

    if alarmstate not in ['on','off']:
        logger.error("set/unset alarm error: bad state {}".format(alarmstate))
        raise RuntimeError('bad alarm state')

    if not user:
        user = 'obsuser'
    reason = "\'{0:s}\'".format(reason)

    str_out,str_err = ata_remote.callObs(['atasetalarm','-c',alarmstate,'-u',user,'-m',reason])

    if str_err:
        logger.error("atagetalarm got error: {}".format(str_err))

    return str_out

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
    stdout, stderr = ata_remote.callObs(["fxconf.rb", "antpos"])

    ant_list = snap_array_helpers.input_to_list(ant_list) 

    retdict = {}
    for line in stdout.splitlines():
        if not line.startswith(b'#'):
            sln = line.decode().split()
            ant = sln[3]
            pos_n = float(sln[0])
            pos_e = float(sln[1])
            pos_u = float(sln[2])
            if ant in ant_list:
                retdict[ant] = [pos_n,pos_e,pos_u]

    return retdict

def get_source_ra_dec(source, deg=True):
    """
    Get the J2000 RA / DEC of `source`. Return in decimal degrees (DEC) and hours (RA)
    by default, unless `deg`=False, in which case return in sexagesimal.
    """
    stdout, stderr = ata_remote.callObs(["atacheck", source])
    for line in stdout.decode().split("\n"):
        if "Found %s" % source in line:
            cols = line.split()
            ra  = float(cols[-1].split(',')[-2])
            dec = float(cols[-1].split(',')[-1])
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
    stdout, stderr = ata_remote.callObs(["atagetradec", antstr])

    retdict = {}
    for line in stdout.splitlines():
        if line.startswith(b'ant'):
            sln = line.decode().split()
            ant = sln[0][3:]
            ra = float(sln[1])
            dec = float(sln[2])
            retdict[ant] = [ra,dec]
        else:
            logger.info('not processed line: {}'.format(line))
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
    stdout, stderr = ata_remote.callObs(["atagetazel", antstr])

    retdict = {}
    for line in stdout.splitlines():
        if line.startswith(b'ant'):
            sln = line.decode().split()
            ant = sln[0][3:]
            az = float(sln[1])
            el = float(sln[2])
            retdict[ant] = [az,el]
        else:
            logger.info('not processed line: {}'.format(line))
    return retdict

def get_eph_source(antlist):
    """
    get the ephemeris file name of where the antennas are pointing
    returns dictionary e.g. {'1a':'casa'}
    """

    logger = logger_defaults.getModuleLogger(__name__)
    ant_list = snap_array_helpers.input_to_list(antlist) 

    antstr = snap_array_helpers.input_to_string(antlist) 
    logger.info("getting sources: {}".format(antstr))

    str_out,str_err = ata_remote.callObs(['ataasciistatus','-l','--header','Name,Source'])
    if str_err:
        logger.error("ataasciistatus got error: {}".format(str_err))

    retdict = {}
    lines = str_out.splitlines()
    for line in lines:
        regroups = re.search('ant(?P<ant>..)\s*(?P<name>.+)',line.decode());
        if regroups:
            ant = regroups.group('ant')
            if ant in ant_list:
                src = regroups.group('name')
                #retdict['ant' + ant] = src
                # keep consistency with getRADec and getAzEl
                retdict[ant] = src

    return retdict

def make_and_track_ephems(source,antstr):
    """
    set the antennas to track a source.
    source has to be a valid catalogue name
    the function call returns only after the antennas are pointed.
    """
    logger = logger_defaults.getModuleLogger(__name__)
    result,errormsg = ata_remote.callObs(['ataephem',source])
    logger.info(result)
    if errormsg:
        logger.error(errormsg)

    antstr = snap_array_helpers.input_to_string(antstr) 

    logger.info("Tracking source {} with {}".format(source,antstr))
    result,errormsg = ata_remote.callObs(['atatrackephem','-w',antstr,source+'.ephem'])
    logger.info(result)
    if errormsg:
        logger.error(errormsg)

    return result

#####
#
# Control of signal path (LNA, mixers, and such)
#
#####

def autotune(ants):
    """
    calls autotune functionality (Power level for RF-Fiber conversion)
    on selected antennas.
    ants is either a list of antennas, e.g. ['1a','1b']
    or comma separated string, e.g. '1a,1b'

    logger is used for autotune response

    Raises RuntimeError if autotune execution fails.
    """
    logger = logger_defaults.getModuleLogger(__name__)

    ants = snap_array_helpers.input_to_string(ants) 

    logger.info("autotuning: {}".format(ants))
    str_out,str_err = ata_remote.callObs(['ataautotune',ants])
    #searching for warnings or errors
    rwarn = str_out.find(b"warning")
    logger.info(str_err)
    if rwarn != -1:
        logger.warning(str_out)
    rerr = str_err.find(b"error")
    if rerr != -1:
        logger.error(str_out)
        raise RuntimeError("Autotune execution error")

def get_pams(antlist):
    """
    get PAM attenuator values for given antennas

    the return value is a dictionary:
    e.g. {'ant1ax':12.5,'ant1ay':20,'ant2ax':11,'ant2ay':13}
    """
    logger = logger_defaults.getModuleLogger(__name__)
    antstr = snap_array_helpers.input_to_string(antlist) 
    logger.info("getting pams: {}".format(antstr))
    str_out,str_err = ata_remote.callObs(['atagetpams','-q',antstr])

    if str_err:
        logger.error("atagetpams got error: {}".format(str_err))

    retdict = {}
    lines = str_out.splitlines()
    for line in lines:
        regroups = re.search('ant(?P<ant>..)\s*on\s*(?P<x>[\d.]+)\s*on\s*(?P<y>[\d.]+)',line.decode());
        if regroups:
            ant = regroups.group('ant')
            xval = float(regroups.group('x'))
            yval = float(regroups.group('y'))
            retdict['ant' + ant + 'x'] = xval
            retdict['ant' + ant + 'y'] = yval
        else:
            logger.warning('unable to parse line: {}'.format(line))

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
    str_out,str_err = ata_remote.callObs(['atagetdet','-q',antstr])

    if str_err:
        logger.error("atagetdet got error: {}".format(str_err))

    retdict = {}
    lines = str_out.splitlines()
    for line in lines:
        regroups = re.search('ant(?P<ant>..)\s*(?P<x>[\d.]+)\s*(?P<y>[\d.]+)',line.decode());
        if regroups:
            ant = regroups.group('ant')
            xval = float(regroups.group('x'))
            yval = float(regroups.group('y'))
            retdict['ant' + ant + 'x'] = xval
            retdict['ant' + ant + 'y'] = yval
        else:
            logger.warning('unable to parse line: {}'.format(line))

    return retdict

def try_on_lna(singleantstr):
    """
    check if the LNA for given antenna is on. 
    if LNA was already on, nothing happens
    if LNA was off, the pams are set to default value (30 dB)
    and then LNA is switched on

    for mutliple antennas, call try_on_lnas
    """

    paxstartdefault = '30'
    wasError = False
    logger = logger_defaults.getModuleLogger(__name__)
    
    result,errormsg = ata_remote.callObsIgnoreError(['atagetlnas',singleantstr])
    logger.info(result)
    if errormsg:
        logger.error(errormsg)
        
    if result.startswith(b'LNA bias is off'):
        logger.warning('LNA {} is OFF'.format(singleantstr))
        logger.info('Setting pax to {}'.format(paxstartdefault))
        result,errormsg = ata_remote.callObs(['atasetpams',singleantstr,paxstartdefault,paxstartdefault])
        logger.info(result)
        if errormsg:
            logger.error(errormsg)
        logger.info('switching on the LNA')
        result,errormsg = ata_remote.callObs(['atalnaon',singleantstr])
        logger.info(result)
        if errormsg:
            logger.error(errormsg)
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

def get_sky_freq():
    """
    Return the sky frequency (in MHz) currently
    tuned to the center of the ATA band
    """
    stdout, stderr = ata_remote.callObs(["atagetskyfreq", "a"])
    return float(stdout.decode().strip())

def set_freq(freq, ants):
    """
    Sets both LO A frequency and antenna focus frequency to
    given freq in MHz
    """
    ants = snap_array_helpers.input_to_string(ants) 

    logger = logger_defaults.getModuleLogger(__name__)

    freqstr = '{0:.2f}'.format(freq)
    stdout, stderr = ata_remote.callObs(['atasetskyfreq','a',freqstr])
    if stderr:
        logger.error(errormsg)

    stdout, stderr = ata_remote.callObs(['atasetfocus',ants,freqstr])
    if stderr:
        logger.error(errormsg)
    #ssh = local["ssh"]
    #cmd = ssh[("obs@tumulus", "atasetskyfreq a %.2f" % freq)]
    #result = cmd()
    #cmd = ssh[("obs@tumulus", "atasetfocus %s %.2f" % (ants, freq))]
    #result = cmd()
    #return result

def get_freq(ant_list):
    """
    gets the LO A and focus frequency in MHz
    for every antenna
    returns a dictionary with a list as values, i.e. {'1a': [1400,1400]}
    """
    logger = logger_defaults.getModuleLogger(__name__)
    antstr = snap_array_helpers.input_to_string(ant_list)

    # get LO A freq
    stdout, stderr = ata_remote.callObs(["atagetskyfreq", "a"])
    skyfreq = float(stdout.decode().strip())
    retdict = {}
    for ant in ant_list:
        retdict[ant] = [skyfreq]

    # get focus frequency
    stdout, stderr = ata_remote.callObs(["atagetfocus", antstr])
    for line in stdout.splitlines():
        if line.startswith(b'ant'):
            sln = line.decode().split()
            ant = sln[0][3:]
            try:
                focusfreq = float(sln[1])
            except ValueError as e:
                focusfreq = "NaN"
            finally:
                retdict[ant].append(focusfreq)
        else:
            logger.info('not processed line: {}'.format(line))
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

def test_all_antennas_in_str(lines, antlist):
    """
    test if all antennas from antlist are in white space separated lines. returns difference between sets
    empty set means all antennas from the list were in the line
    """
    aset = set(antlist)
    antsinline = set(lines.split())
    setdiff = aset - antsinline
    return list(setdiff)

def move_ant_group(antlist, from_group, to_group):
    """
    call to move antennas between two sals groups
    see: reserve_antennas, release_antennas
    
    raises RuntimeError if the move is not possible
    """
    logger = logger_defaults.getModuleLogger(__name__)
    antlist = snap_array_helpers.input_to_list(antlist) 
    logger.info("Reserving \"{}\" from {} to {}".format(snap_array_helpers.array_to_string(antlist), from_group, to_group))

    stdout, stderr = ata_remote.callObs(['fxconf.rb','sals',from_group])
    notants = test_all_antennas_in_str(stdout.decode(),antlist)
    if notants:
        logger.error("Antennas {} are not in group {}".format(snap_array_helpers.array_to_string(notants),from_group))
        raise RuntimeError("Failed to move antenna {} from {} to {} (not in from_group)".format(snap_array_helpers.array_to_string(notants), from_group, to_group))

    stdout, stderr = ata_remote.callObs(['fxconf.rb','sagive', from_group, to_group] + antlist)

    stdout, stderr = ata_remote.callObs(['fxconf.rb','sals',to_group])
    notants = test_all_antennas_in_str(stdout.decode(),antlist)
    if notants:
        logger.error("Failed to move antennas {} to group {}, reversing sagive".format(snap_array_helpers.array_to_string(notants),to_group))
        stdout, stderr = ata_remote.callObs(['fxconf.rb','sagive',to_group,from_group] + antlist)
        raise RuntimeError("Failed to move antenna {} from {} to {}".format(snap_array_helpers.array_to_string(notants), from_group, to_group))

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
        logger = logger_defaults.getModuleLogger(__name__)
        logger.info("Parking ants");
        stdout, stderr = ata_remote.callObs(["park.csh", ','.join(antlist)])
        logger.info(stdout.rstrip())
        logger.info(stderr.rstrip())
        logger.info("Parked");

    return

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

def create_ephems(source, az_offset, el_offset):
    """
    a script call to create 2 ephemeris files, one on target, one
    shifted by az_ and el_offset. Mainly used for ON-OFF observations
    together with point_ants function
    """
    #ssh = local["ssh"]
    #cmd = ssh[("obs@tumulus", "cd /home/obs/NSG;./create_ephems.rb %s %.2f %.2f" % (source, az_offset, el_offset))]
    #result = cmd()
    result,errormsg = ata_remote.callObs(['cd /home/obs/NSG;./create_ephems.rb {0!s} {1:.2f} {2:.2f}'.format(source,az_offset,el_offset)])
    if errormsg:
        logger = logger_defaults.getModuleLogger(__name__)
        logger.error(errormsg)
    return ast.literal_eval(result.decode())


def point_ants(on_or_off, ants):
    """
    on_or_off is a string, either "on" or "off". If "on", the antennas are pointed to the source
    if "off", the antennas are pointed away from the source by az_ and el_offset given to create_ephems 

    requires earlier call of create_ephems
    """
    ants = snap_array_helpers.input_to_string(ants) 

    result,errormsg = ata_remote.callObs(['cd /home/obs/NSG;./point_ants_onoff.rb {} {}'.format(on_or_off, ants)]) 
    if errormsg:
        logger = logger_defaults.getModuleLogger(__name__)
        logger.error(errormsg)
    #ssh = local["ssh"]
    #cmd = ssh[("obs@tumulus", "cd /home/obs/NSG;./point_ants_onoff.rb %s %s" % (on_or_off, ants))]
    #result = cmd()
    return ast.literal_eval(result.decode())


def create_ephems2(source, az_offset, el_offset):
    """
    WF: edited version of 'create_ephems' to use '$sourcename_on' and off
    ephem files
    a script call to create 2 ephemeris files, one on target, one
    shifted by az_ and el_offset. Mainly used for ON-OFF observations
    together with point_ants function
    """
    #ssh = local["ssh"]
    #cmd = ssh[("obs@tumulus", "cd /home/obs/NSG;./create_ephems.rb %s %.2f %.2f" % (source, az_offset, el_offset))]
    #result = cmd()
    result,errormsg = ata_remote.callObs(['cd /home/obs/NSG;./create_ephems_source.rb {0!s} {1:.2f} {2:.2f}'.format(source,az_offset,el_offset)])
    if errormsg:
        logger = logger_defaults.getModuleLogger(__name__)
        logger.error(errormsg)
    return ast.literal_eval(result.decode())

def point_ants2(source, on_or_off, ants):
    """
    WF: edited version of 'point_ants' to use '$sourcename_on' and off
    ephem files
    on_or_off is a string, either "on" or "off". If "on", the antennas are pointed to the source
    if "off", the antennas are pointed away from the source by az_ and el_offset given to create_ephems 

    requires earlier call of create_ephems
    """
    ants = snap_array_helpers.input_to_string(ants) 

    result,errormsg = ata_remote.callObs(['cd /home/obs/NSG;./point_ants_onoff_source.rb {} {} {}'.format(on_or_off, ants, source)]) 
    if errormsg:
        logger = logger_defaults.getModuleLogger(__name__)
        logger.error(errormsg)
    #ssh = local["ssh"]
    #cmd = ssh[("obs@tumulus", "cd /home/obs/NSG;./point_ants_onoff.rb %s %s" % (on_or_off, ants))]
    #result = cmd()
    return ast.literal_eval(result.decode())



if __name__== "__main__":

    #print get_pam_status("2a")

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
