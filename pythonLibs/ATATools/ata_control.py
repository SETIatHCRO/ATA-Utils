#!/usr/bin/python

"""
Python wrappers for various command line
tools at the ATA.
NB: many of these can only be run on
`nsg-work1`, which has control of the USB
switches and attenuators in the ATA test
setup.
"""

import os
import sys
from subprocess import Popen, PIPE
import socket
import ast
import logging
from threading import Thread
import snap_array_helpers
import snap_onoffs_contants
from plumbum import local
import time
import datetime

RF_SWITCH_HOST = "nsg-work1"
ATTEN_HOST = "nsg-work1"

def get_sky_freq():
    """
    Return the sky frequency (in MHz) currently
    tuned to the center of the ATA band
    """
    proc = Popen(["atagetskyfreq", "a"], stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    return float(stdout.strip())

def get_ascii_status():
    """
    Return an ascii table of lots of ATA
    status information.
    """
    proc = Popen("ataasciistatus", stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    return stdout

def write_obs_to_db(source, freq, az_offset=0.0, el_offset=0.0, ants=["dummy"]):
    """
    Write details of an observation in to the observation database.
    """
    proc = Popen(["obs2db", ",".join(ants), "%f" % freq, source, "%f" % az_offset, "%f" % el_offset])
    proc.wait()

def end_obs():
    """
    Write the current time as the end of the latest observation in the obs database.
    """
    proc = Popen(["obs2db", "stop"])
    proc.wait()

def get_latest_obs():
    """
    Get the latest observation ID from the obs database.
    """
    proc = Popen(["obsgetid"], stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    return int(stdout)

def point(source, freq, az_offset=0.0, el_offset=0.0, ants=['dummy'], writetodb=True):
    """
    Point the ATA at `source`, with an offset
    from the source's position of `az_offset` degrees
    in azimuth and `el_offset` degrees in elevation.
    Tune to a center sky frequency of `freq` MHz
    """

    proc = Popen(["pointshift", source, "%f" % freq, "%f" % az_offset, "%f" % el_offset])
    proc.wait()

#def set_rf_switch(switch, sel):
def set_rf_switch(ant_list):
    """
    Set RF switch `switch` (0..1) to connect the COM port
    to port `sel` (1..8)
    """
    logger = logging.getLogger(snap_onoffs_contants.LOGGING_NAME)

    ant_list_stripped = str(ant_list).replace("'","").replace("[","").replace("]","").replace(" ","")

    if socket.gethostname() == RF_SWITCH_HOST:
        proc = Popen(["rfswitch", "%s" % ant_list_stripped], stdout=PIPE, stderr=PIPE)
    else:
        proc = Popen(["ssh", "sonata@%s" % RF_SWITCH_HOST, "rfswitch", "%s" % ant_list_stripped], stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    for line in stdout.splitlines():
        logger.info("Set rfswitch for ants %s result: %s" % (ant_list_stripped, line))
    if stderr.startswith("OK"):
        logger.info("Set rfswitch for ants %s result: SUCCESS" % ant_list_stripped)
        return
    else:
        logger.info("Set switch 'rfswitch %s' failed!" % ant_list_stripped)
        raise RuntimeError("Set switch 'rfswitch %s' failed!" % (ant_list_stripped))

def rf_switch_thread(ant_list, wait):

    logger = logging.getLogger(snap_onoffs_contants.LOGGING_NAME)

    t = Thread(target=set_rf_switch, args=(ant_list,))
    t.start()

    if(wait == True):
        t.join();
        return None

    return t


def set_atten_thread(ant_list, db_list, wait):

    logger = logging.getLogger(snap_onoffs_contants.LOGGING_NAME)

    if(len(ant_list) != len(db_list)):
        logger.error("set_atten_thread, antenna list length != db_list length.")
        raise RuntimeError("set_atten_thread, antenna list length != db_list length.")

    t = Thread(target=set_atten, args=(ant_list, db_list,))
    t.start()

    if(wait == True):
        t.join();
        return None

    return t
    

def set_atten(ant_list, db_list):

    ant_list_stripped = str(ant_list).replace("'","").replace("[","").replace("]","").replace(" ","")
    db_list_stripped = str(db_list).replace("'","").replace("[","").replace("]","").replace(" ","")
    """
    Set attenuation of antenna or ant-pol `ant`
    to `db` dB.
    Allowable values are 0.0 to 31.75
    """
    logger = logging.getLogger(snap_onoffs_contants.LOGGING_NAME)
    logger.info("setting rfswitch attenuators %s %s" % (db_list_stripped, ant_list_stripped))

#    if socket.gethostname() == ATTEN_HOST:
    proc = Popen(["atten", "%s" % db_list_stripped, "%s" % ant_list_stripped],  stdout=PIPE, stderr=PIPE)
#    else:
#        proc = Popen(["ssh", "sonata@%s" % ATTEN_HOST, "sudo", "atten", "%s" % db_list_stripped, "%s" % ant_list_stripped],  stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()

    output = ""
    # Log the result
    for line in stdout.splitlines():
        output += "%s\n" % line
        logger.info("Set atten for ant %s to %s db result: %s" % (ant_list_stripped, db_list_stripped, line))
    if stderr.startswith("OK"):
        logger.info("Set atten for ant %s to %s db result: SUCCESS" % (ant_list_stripped, db_list_stripped))
        return output
    else:
        print "STDERR=%s" % (stderr)
        logger.error("Set attenuation 'sudo atten %s %s' failed! Trying again" % (db_list_stripped, ant_list_stripped))
        raise RuntimeError("ERROR: set_atten %s %s returned: %s" % (db_list_stripped, ant_list_stripped, stderr))

def set_pam_atten(ant, pol, val):
    """
    Set the attenuation of antenna `ant`, polarization `pol` to `val` dB
    """
    logger = logging.getLogger(snap_onoffs_contants.LOGGING_NAME)
    logger.info("setting pam attenuator %s%s to %.1fdb" % (ant, pol, val))
    if(pol == ""):
        proc = Popen(["ssh", "obs@tumulus", "atasetpams", ant, "%f"%val, "%f"%val], stdout=PIPE)
    else:
        proc = Popen(["ssh", "obs@tumulus", "atasetpams", ant, "-%s"%pol, "%f"%val], stdout=PIPE)
    stdout, stderr = proc.communicate()
    proc.wait()
    # Log  returned result, but strip off the newline character
    logger.info(stdout.rstrip())

def set_pam_attens(ant, valx, valy):
    """
    Set the attenuation of antenna `ant`, both pols, to valx and valy dB
    """
    logger = logging.getLogger(snap_onoffs_contants.LOGGING_NAME)
    logger.info("setting pam attenuator %s to %.1f,%.1f db" % (ant, valx, valy))
    proc = Popen(["ssh", "obs@tumulus", "atasetpams", ant, "%f"%valx, "%f"%valy], stdout=PIPE)
    stdout, stderr = proc.communicate()
    proc.wait()
    # Log  returned result, but strip off the newline character
    logger.info(stdout.rstrip())

def get_pam_status(ant):
    """
    Get the PAM attenuation settings and power detector readings for antenna `ant`
    """
    logger = logging.getLogger(snap_onoffs_contants.LOGGING_NAME)
    logger.info("getting pam attenuator %s" % ant )
    proc = Popen(["getdetpams", ant],  stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    logger.info("getting pam attenuator stdout: %s" % stdout)
    x = stdout.split(',')
    return {'ant':x[0], 'atten_xf':float(x[1]), 'atten_xb':float(x[2]), 'atten_yf':float(x[3]), 'atten_yb':float(x[4]), 'det_x':float(x[5]), 'det_y':float(x[6])}

def move_ant_group(ants, from_group, to_group):

    logger = logging.getLogger(snap_onoffs_contants.LOGGING_NAME)
    logger.info("Reserving \"%s\" from %s to %s" % (snap_array_helpers.array_to_string(ants), from_group, to_group))

    proc = Popen(["antreserve", from_group, to_group] + ants, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    lines = stdout.split('\n')
    for line in lines:
        cols = line.split()
        if (len(cols) > 0) and (cols[0]  == to_group):
            bfa = cols[1:]
    for ant in ants:
        if ant not in bfa:
            #print nonegroup
            print ants
            logger.error("Failed to move antenna %s from %s to %s" % (ant, from_group, to_group))
            raise RuntimeError("Failed to move antenna %s from %s to %s" % (ant, from_group, to_group))

def reserve_antennas(ants):

    move_ant_group(ants, "none", "bfa")

def release_antennas(ants, should_park):

    move_ant_group(ants, "bfa", "none")

    if(should_park):
        logger = logging.getLogger(snap_onoffs_contants.LOGGING_NAME)
        logger.info("Parking ants");
        proc = Popen(["ssh", "obs@tumulus", "park.csh"], stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        proc.wait()
        logger.info(stdout.rstrip())
        logger.info(stderr.rstrip())
        logger.info("Parked");

def get_ra_dec(source, deg=True):
    """
    Get the J2000 RA / DEC of `source`. Return in decimal degrees (DEC) and hours (RA)
    by default, unless `deg`=False, in which case return in sexagesimal.
    """
    proc = Popen(["atacheck", source], stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    for line in stdout.split("\n"):
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

def create_ephems(source, az_offset, el_offset):

    ssh = local["ssh"]
    cmd = ssh[("obs@tumulus", "cd /home/obs/NSG;./create_ephems.rb %s %.2f %.2f" % (source, az_offset, el_offset))]
    result = cmd()
    return ast.literal_eval(result)


def point_ants(on_or_off, ant_list):

    ssh = local["ssh"]
    cmd = ssh[("obs@tumulus", "cd /home/obs/NSG;./point_ants_onoff.rb %s %s" % (on_or_off, ant_list))]
    result = cmd()
    return ast.literal_eval(result)

def set_freq(freq, ants):

    ssh = local["ssh"]
    cmd = ssh[("obs@tumulus", "atasetskyfreq a %.2f" % freq)]
    result = cmd()
    cmd = ssh[("obs@tumulus", "atasetfocus %s %.2f" % (ants, freq))]
    result = cmd()
    return result

DEFAULT_DATA_DIR = "~/data"
output_dir = os.path.expanduser("%s" % DEFAULT_DATA_DIR)

def set_output_dir(dirname=None):

    global output_dir

    # Determine the snap data output directory based on todays date
    todays_date = datetime.datetime.today().strftime('%Y%m%d')
    if(dirname != None):
        output_dir = dirname
    else:
        output_dir = os.path.expanduser("%s/%s" % (os.path.expanduser("%s" % DEFAULT_DATA_DIR), todays_date))
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    except OSError:
        print ("Error: Creating directory %s" %  output_dir)
        send_email("Error report", "Error: Creating directory %s. exiting" % output_dir)
        sys.exit(1);

    handle = logging.FileHandler("%s/log.txt" % output_dir, 'a')
    formatter = logging.Formatter('%(asctime)s - %(module)s.%(funcName)s() - %(message)s')
    handle.setFormatter(formatter)

    logger = logging.getLogger()
    logger.handlers = [handle]


def get_output_dir():

    global output_dir
    return output_dir

#https://stackoverflow.com/questions/22934616/multi-line-logging-in-python
class CustomFilter(logging.Filter):
    def filter(self, record):
        if hasattr(record, 'dict') and len(record.dct) > 0:
            for k, v in record.dct.iteritems():
                record.msg = record.msg + '\n\t' + k + ': ' + v
        return super(CustomFilter, self).filter(record)

def setup_logger(dirname=None):

    logger = logging.getLogger(snap_onoffs_contants.LOGGING_NAME)
    logger.setLevel(logging.INFO)
    logger.addFilter(CustomFilter())

    set_output_dir(dirname)

    return logger


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
    print set_atten("2jx,2jy", "10.0,10.0")
    #print create_ephems("casa", 10.0, 5.0)
    #print point_ants("on", "1a,1b")
    #print point_ants("off", "1a,1b")
