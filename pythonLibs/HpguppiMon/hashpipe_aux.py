import subprocess
import argparse
import time
import os
import glob
import re

from SNAPobs import snap_defaults

ATA_EXEC_DIR = os.path.join(snap_defaults.baseshare, 'bin')

init_atasnap_hashpipe_sh = os.path.join(ATA_EXEC_DIR, 'init_atasnap_hashpipe.sh')
kill_hashpipes_sh = os.path.join(ATA_EXEC_DIR, 'kill_hashpipes.sh')
init_redis_gateway_sh = os.path.join(ATA_EXEC_DIR, 'init_redis_gateway.sh')
kill_hashpipe_related_sh = os.path.join(ATA_EXEC_DIR, 'kill_hashpipe_related.sh')

def set_hashpipe_key_value(key, value, instance=0):
    '''
    Sets the value of a key by calling hashpipe_check_status, which is expected to be in the path.

    Parameters
    ----------
    key: str
        The key whose value is to be set
    key: str/int/float
        The value to be set
    instance: int
        The enumeration of the hashpipe instance whose status is adjusted

    Returns
    -------
    bytearray: The raw output of the hashpipe_check_status call
    '''
    valuearg = '--string='
    if typeof(value) == int:
        valuearg = '--int='
    if typeof(value) == float:
        valuearg = '--double='
    valuearg += str(value)

    return subprocess.run(['hashpipe_check_status', '--instance='+str(instance), '--key='+key, valuearg], capture_output=True).stdout

def get_hashpipe_key_value(key, instance=0):
    '''
    Gets the output from a call of hashpipe_check_status, which is expected to be in the path.

    Parameters
    ----------
    key: str
        The key to get the value of
    instance: int
        The enumeration of the hashpipe instance whose status is consulted

    Returns
    -------
    bytearray: The raw output of the hashpipe_check_status call
    '''
    # REDISGET = REDISGETGW.substitute(host=hostname, inst=args.instance)
    # r.hget(REDISGET, "PPRWSARG")
    return subprocess.run(['hashpipe_check_status', '--instance='+str(instance), '--query='+key], capture_output=True).stdout

def get_hashpipe_key_value_str(key, instance=0):
    '''
    Returns the value of a key in the hashpipe's status, parsed as a string.
    Calls 

    Parameters
    ----------
    key: str
        The key to get the value of
    instance: int
        The enumeration of the hashpipe instance whose status is consulted

    Returns
    -------
    str/bytearray/None: The value of the key
    '''
    ret = get_hashpipe_key_value(key, instance=0)
    try:
        return ret.decode().strip()
    except:
        return ret

def get_hashpipe_pulse(instance=0):
    '''
    Conveniently calls get_hashpipe_key_value('DAQPULSE', instance)

    Parameters
    ----------
    instance: int
        The enumeration of the hashpipe instance whose status is consulted

    Returns
    -------
    str: The value of the DAQPULSE key in the hashpipe's status
    '''
    return get_hashpipe_key_value('DAQPULSE', instance)

def block_until_pulse_change(instance=0, maxstale=20, silent=False):
    '''
    Consults the hashpipe's status DAQPULSE key for an indication that
    the instance is running.

    Parameters
    ----------
    instance: int
        The enumeration of the hashpipe instance whose status is consulted
    maxstale: int
        The limit of consistently unchanged DAQPULSE values before bailing (1 sec interval)
    silent: bool
        Whether or not to print while waiting

    Returns
    -------
    bool: Whether or not DAQPULSE is valid and changed

    '''
    stalecount = 0
    stalepulse = get_hashpipe_pulse(instance)
    while True:
        try:
            pulse_string = stalepulse.decode()
            # Validate a pulse that is decoded to UTF
            if pulse_string[0:3] in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
                break
        except:
            stalecount += 1
        if not silent:
            print('\rDAQPULSE not a UTF-8 string'+'.'*(stalecount%5), end=' '*5)
        time.sleep(2)
        if stalecount > 5:
            if not silent:
                print('\rExiting after excessive waiting for DAQPULSE to be set. (10 seconds)')
            return False
        stalepulse = get_hashpipe_pulse(instance)

    stalecount = 0

    while get_hashpipe_pulse(instance) == stalepulse:
        if not silent:
            print('\rwaiting for DAQPULSE to change'+'.'*(stalecount%5), end=' '*5)
        time.sleep(1)
        if (stalecount > maxstale):
            if not silent:
                print('\rExiting after excessive waiting for DAQPULSE to change. (%d seconds)' %(maxstale))
            break
        stalecount += 1
    if not silent:
        print('')
    if (stalecount > maxstale):
        return False
    return True

def start_hashpipe(instance=0, bindhost=None):
    '''
    Calls init_atasnap_hashpipe.sh. Does not directly kill existing hashpipes.

    Parameters
    ----------
    instance: int
        the hashpipe instance to start up.
    bindhost: str
        the interface name for the hashpipe instance to bind to.
    
    Returns
    -------
    None
    '''
    print('\nStarting hashpipe (', bindhost, ')', sep='')
    cmd = ['sudo', init_atasnap_hashpipe_sh, str(instance)]
    if bindhost is not None:
        cmd.append(bindhost) 
    subprocess.run(cmd) 

def kill_hashpipes():
    '''
    Calls kill_hashpipes.sh, which is expected to be in the path

    Parameters
    ----------
    None

    Returns
    -------
    None
    '''
    print('\nKilling existing hashpipes')
    subprocess.run(['sudo', kill_hashpipes_sh])

def start_redis_gateway(instance=0):
    '''
    Calls init_redis_gateway.sh, which is expected to be in the path

    Parameters
    ----------
    instance: int
        The enumeration of the hashpipe instance whose status is consulted

    Returns
    -------
    None
    '''
    subprocess.run([init_redis_gateway_sh, str(instance)]) # assume it will kill existing gateways

def kill_hashpipe_related():
    '''
    Calls kill_hashpipe_related.sh, which is expected to be in the path

    Parameters
    ----------
    None
    Returns
    -------
    None
    '''
    print('\nKilling existing hashpipe-related processes')
    subprocess.run(['sudo', kill_hashpipe_related_sh])

def clear_shared_memory():
    '''
    Deletes ALL shared memory and semaphores with ipcrm calls.
    Uses sudo!

    Parameters
    ----------
    None

    Returns
    -------
    None
    '''
    print('\nDeleting shared memory')
    lines = subprocess.run(['ipcs'], capture_output=True).stdout.decode().split('\n')
    mode = 0
    for line in lines:
        if mode == 1 or mode == 3:
            m = re.match(r'[^\s]*\s+([^\s]+).*', line)
            if m:
                flag = '-m' if mode == 1 else '-s'
                subprocess.run(['sudo', 'ipcrm', flag, str(m.group(1))])
            else:
                mode += 1
        elif mode == 0 and re.match(r'.*shmid.*', line):
            mode = 1
        elif mode == 2 and re.match(r'.*semid.*', line):
            mode = 3
        elif mode == 4:
            break

def get_hashpipe_capture_dir(instance=0):
    '''
    Consults the hashpipe's status hash for the path of the latest RAW
    dump: DATADIR/PROJID/BACKEND/BANK

    Parameters
    ----------
    instance: int
        The enumeration of the hashpipe instance whose status is consulted
    
    Returns
    -------
    str: The directory path of the latest RAW dump
    '''
    rawfiledir = ''
    for key in ['DATADIR', 'PROJID', 'BACKEND', 'BANK']:
        part = get_hashpipe_key_value(key, instance)
        try:
            rawfiledir = os.path.join(rawfiledir, part.decode().strip())
        except:
            print('Status Key', key, 'is not a valid string. Exiting.')
            return False
    return rawfiledir

def get_latest_raw_stem_in_dir(rawfiledir):
    '''
    Finds the latest files in the given directory and
    returns the filepath excluding .0000.raw, the stem.

    Parameters
    ----------
    rawfiledir: str
        The directory to analyse
    
    Returns
    -------
    str: The stem-filepath of the latest RAW dump, or None
    '''
    files = glob.glob(rawfiledir+'/*.raw')

    if len(files) == 0:
        print('Could not find any *.raw files in "', rawfiledir, '".', sep="")
        return None
    
    files.sort(key=os.path.getmtime, reverse=True)

    latest = files[0]
    stemmatch = re.match(r'(.*)\.\d{4}\.raw', latest, re.M|re.I)
    if not stemmatch:
        print('Could not match a stem pattern against "', latest, '".', sep="")
        return False
    return stemmatch.group(1)
