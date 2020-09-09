import os 

from . import snap_dada_defaults
from ATATools import logger_defaults

MYCWD = os.path.dirname(os.path.realpath(__file__))

DADAKEYS = ['d%id%i' %(i,i) for i in range(10)]

def create_buffers(keylist, bufsze_list, logfile):
    logger = logger_defaults.getModuleLogger(__name__)
    pairs = ""
    for key, bufsze in zip(keylist, bufsze_list):
        pairs += key
        pairs += " "
        pairs += str(bufsze)
        pairs += " "
    script = os.path.join(MYCWD, snap_dada_defaults.create_buf_script)
    cmd = script + " " + pairs + ">> " + logfile + " 2>&1"
    logger.info("Executing: %s" %cmd)
    os.system(cmd)


def destroy_buffers(keylist, logfile):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("Destroying dada buffers")
    script = os.path.join(MYCWD, snap_dada_defaults.destroy_buf_script)
    cmd = script + " " + " ".join(keylist) + ">> " + logfile + " 2>&1"
    logger.info("Executing: %s" %cmd)
    os.system(cmd)


# ugly funcion...
def udpdb(snap_hosts, rx_hosts, rx_ports, 
        cpu_cores, header_files, keylist, logfiles):
    rx_ports = [str(i) for i in rx_ports]
    cpu_cores = [str(i) for i in cpu_cores]
    logger = logger_defaults.getModuleLogger(__name__)
    logger.debug(snap_hosts)
    logger.debug(rx_hosts)
    logger.debug(rx_ports)
    logger.debug(cpu_cores)
    logger.debug(header_files)
    logger.debug(keylist)
    logger.debug(logfiles)

    script = os.path.join(MYCWD, snap_dada_defaults.udpdb_script)
    cmd = script + " "
    for allParams in zip(snap_hosts, rx_hosts, rx_ports, 
            cpu_cores, header_files, keylist, logfiles):
        cmd += " ".join(allParams) + " "

    logger.info("Executing: %s" %cmd)
    os.system(cmd)


def dbsigproc(keylist, cpu_cores, logfiles, npol, basedir, 
        disable_rfi, invert_freqs=True):
    logger = logger_defaults.getModuleLogger(__name__)
    script = os.path.join(MYCWD, snap_dada_defaults.dbsigproc_script)
    cpu_cores = [str(i) for i in cpu_cores]
    cmd = script + " "
    if invert_freqs:
        cmd += " -i "
    if disable_rfi:
        cmd += " -m "
    cmd += " -p %i " %npol
    cmd += " -D %s " %basedir
    for cpu_key_log in zip(cpu_cores, keylist, logfiles):
        cmd += " ".join(cpu_key_log) + " "
    logger.info("Executing: %s" %cmd)
    os.system(cmd)


def dbnull(inkeys):
    logger = logger_defaults.getModuleLogger(__name__)
    script = os.path.join(MYCWD, snap_dada_defaults.dbnull_script)
    cmd = script + " " + " ".join(inkeys)
    logger.info("Executing: %s" %cmd)
    os.system(cmd)



def dbsumdb(inkeys, outkey, loggerfile):
    logger = logger_defaults.getModuleLogger(__name__)
    script = os.path.join(MYCWD, snap_dada_defaults.dbsumdb_script)
    cmd = script + " " + " ".join(inkeys) + "-o "+ outkey +\
            ">> " + logfile + " 2>&1"
    logger.info("Executing: %s" %cmd)
    os.system(cmd)


def gen_key_list(nkeys):
    if nkeys > len(DADAKEYS):
        raise RuntimeError("Not enough keys to provide")
    return DADAKEYS[:nkeys]
