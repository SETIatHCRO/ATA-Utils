#!/usr/bin/python3

"""
Python wrappers for various command line
tools at the ATA.
"""

import re
import ast
import concurrent.futures
from . import ata_remote,ata_constants,snap_array_helpers,logger_defaults

def get_snap_dictionary(array_list):
    """
    returns the dictionary for snap0-3 antennas

    Raises KeyError if antenna is not in list
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

def autotune(ants):
    logger = logger_defaults.getModuleLogger(__name__)

    assert isinstance(ants,str),"input parameter not a string"

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

def get_sky_freq():
    """
    Return the sky frequency (in MHz) currently
    tuned to the center of the ATA band
    """
    stdout, stderr = ata_remote.callObs(["atagetskyfreq", "a"])
    return float(stdout.decode().strip())

def get_ascii_status():
    """
    Return an ascii table of lots of ATA
    status information.
    """
    
    stdout, stderr = ata_remote.callObs(["ataasciistatus","-l"])
    return stdout.decode()

def set_rf_switch(ant_list):
    """
    Set RF switch `switch` (0..1) to connect the COM port
    to port `sel` (1..8)
    """
    logger = logger_defaults.getModuleLogger(__name__)

    assert isinstance(ant_list,list),"input parameter not a list"

    ants = ','.join(ant_list)

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

def getRaDec(ant_list):
    """
    get the Ra-Dec pointings of each antenna
    Ra is in decimal hours [0,24)
    Dec is in decimal degree [-90,90]
    returns dictionary with 1x2 list e.g. {'1a':[0.134 1.324]}
    """
    logger = logger_defaults.getModuleLogger(__name__)
    antstr = ",".join(ant_list)
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

def getAzEl(ant_list):
    """
    get the Az-El pointings of each antenna
    Az is in decimal degree 
    Dec is in decimal degree 
    returns dictionary with 1x2 list e.g. {'1a':[0.134 1.324]}
    """
    logger = logger_defaults.getModuleLogger(__name__)
    antstr = ",".join(ant_list)
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

def get_ant_pos(ant_list):
    """
    get the NEU position of the antenna w.r.t telescope center
    returns dictionary with 1x3 list e.g. {'1a':[-74.7315    65.9487    0.5466]}
    """
    logger = logger_defaults.getModuleLogger(__name__)
    stdout, stderr = ata_remote.callObs(["fxconf.rb", "antpos"])

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


def rf_switch_thread(ant_list):
    """
    start a thread to set rf switch,
    ant list should consist of antennas from separate snaps
    """

    logger = logger_defaults.getModuleLogger(__name__)
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


def set_atten_thread(antpol_list_list, db_list_list):
    """
    start a thread to set attenuator value
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

def set_atten(antpol_list, db_list):
    """
    Set attenuation of antenna or ant-pol `ant`
    to `db` dB.
    Allowable values are 0.0 to 31.75
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

def get_pams(antlist):

    assert isinstance(antlist,list),"input parameter not a list"

    logger = logger_defaults.getModuleLogger(__name__)
    antstr = ",".join(antlist)
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

    assert isinstance(antlist,list),"input parameter not a list"

    logger = logger_defaults.getModuleLogger(__name__)
    antstr = ",".join(antlist)
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

def move_ant_group(antlist, from_group, to_group):

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

def reserve_antennas(antlist):

    move_ant_group(antlist, "none", "bfa")

def release_antennas(antlist, should_park):

    move_ant_group(antlist, "bfa", "none")

    if(should_park):
        logger = logger_defaults.getModuleLogger(__name__)
        logger.info("Parking ants");
        stdout, stderr = ata_remote.callObs(["park.csh", ','.join(antlist)])
        logger.info(stdout.rstrip())
        logger.info(stderr.rstrip())
        logger.info("Parked");

def get_ra_dec(source, deg=True):
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

def make_and_track_ephems(source,antstr):
    logger = logger_defaults.getModuleLogger(__name__)
    result,errormsg = ata_remote.callObs(['ataephem',source])
    logger.info(result)
    if errormsg:
        logger.error(errormsg)

    logger.info("Tracking source {} with {}".format(source,antstr))
    result,errormsg = ata_remote.callObs(['atatrackephem','-w',antstr,source+'.ephem'])
    logger.info(result)
    if errormsg:
        logger.error(errormsg)

    return result

def create_ephems(source, az_offset, el_offset):

    #ssh = local["ssh"]
    #cmd = ssh[("obs@tumulus", "cd /home/obs/NSG;./create_ephems.rb %s %.2f %.2f" % (source, az_offset, el_offset))]
    #result = cmd()
    result,errormsg = ata_remote.callObs(['cd /home/obs/NSG;./create_ephems.rb {0!s} {1:.2f} {2:.2f}'.format(source,az_offset,el_offset)])
    if errormsg:
        logger = logger_defaults.getModuleLogger(__name__)
        logger.error(errormsg)
    return ast.literal_eval(result)


def point_ants(on_or_off, ants):

    assert isinstance(ants,str),"input parameter not a string"

    result,errormsg = ata_remote.callObs(['cd /home/obs/NSG;./point_ants_onoff.rb {} {}'.format(on_or_off, ants)]) 
    if errormsg:
        logger = logger_defaults.getModuleLogger(__name__)
        logger.error(errormsg)
    #ssh = local["ssh"]
    #cmd = ssh[("obs@tumulus", "cd /home/obs/NSG;./point_ants_onoff.rb %s %s" % (on_or_off, ants))]
    #result = cmd()
    return ast.literal_eval(result)

def set_freq(freq, ants):

    assert isinstance(ants,str),"input parameter not a string"

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
