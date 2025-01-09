import pandas as pd
import numpy as np
from multiprocessing.pool import ThreadPool
import requests
import threading
import warnings

from ATATools import logger_defaults
from ata_snap import ata_snap_fengine, ata_rfsoc_fengine
from SNAPobs.snap_config import get_ata_cfg

import time


# TODO: move and put in a config file
RFSOC_RMS = 1024
ALL_LOS = ['a', 'b', 'c', 'd']
ALL_POLS = ['x', 'y']

INIT_ATT = 23

MAX_ATT = 31.5
MIN_ATT = 0.0

NPROCS = 3

GET_ADC_CYCLES = 3 #Number of adc sample cycles to get

RESTGW_PORT = 12345 #port number for the restgw on all the gain-modules

class APIError(Exception):
    """Custom exception for API-related errors."""
    def __init__(self, status_code, message):
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.message = message

# TODO: replace
class testRfsoc(object):
    def __init__(self, rfsoc_name):
        self.hostname = rfsoc_name
        return
    def adc_get_samples(self):
        x = tuple(np.random.randint(-2000, 2000, size=8192))
        y = tuple(np.random.randint(-2000, 2000, size=8192))
        return x,y

def _round50th(list_n):
    ans = []
    for a in list_n:
        mod = a%1
        int_a = np.round(a-mod)
        if mod < 0.25:
            ans.append(float(int_a))
        elif mod >= 0.25 and mod <= 0.75:
            ans.append(float(int_a) + 0.5)
        else:
            ans.append(float(int_a) + 1)
    return np.array(ans)


# TODO: Hardcoded for now
def get_antenna_mapping():
    d = pd.read_csv("/home/sonata/antenna_config_pol.dat", sep='\s+')
    d.columns = d.columns.str.replace("#", "")
    return d


def _select_from(initial_dframe, **kwargs):
    """
    Selects according to certain columns from a dataframe,
    and returns a sub dataframe

    Parameters
    ----------
    initial_dframe : Pandas DataFrame
        Initial dataframe that we want to select columns from

    Returns
    -------
    sub_dframe : Pandas DataFrame
        Pandas DataFrame that we selected according to columns
    """
    logger = logger_defaults.getModuleLogger(__name__)
    logger.debug("Entered '_select_from' with parameters: %s"
                 %(initial_dframe))
    mask = np.ones(len(initial_dframe), dtype=bool)
    for key, value in kwargs.items():
        logger.debug(key, value)
        mask &= np.isin(initial_dframe[key], value)

    sub_dframe = initial_dframe[mask].copy()
    return sub_dframe


def set_attenuation(attn, ant_list, los, pols=ALL_POLS):
    """
    sets attenuation of provided antennas, los, and pols 
    to a certain attenuation level.

    Parameters
    ----------
    attn : float or int
        Attenuation to set the gain-modules to

    ant_list : list
        List of antenna names, e.g. ['1a', '2b']

    los : list
        List of tunings to target, e.g. ['a', 'b']

    pols : list
        List of polarisations to tune, e.g. ['x', 'y']
    """
    logger = logger_defaults.getModuleLogger(__name__)
    logger.debug("Entered 'set_attenuation' with parameters: %s %s %s %s"
                 %(attn, ant_list, los, pols))

    assert len(ant_list) == len(set(ant_list)),\
            "Detected duplicate antennas in %s" %ant_list

    # TODO: assert all variables have correct types

    # Get all the antenna mapping configuration
    ant_mapping = get_antenna_mapping()

    # Make sure ant_list and lo_list are case-insensitive
    ant_list = [ant.lower() for ant in ant_list] 
    los      = [lo.lower() for lo in los]

    sub_ant_mapping = _select_from(ant_mapping, LO=los, pol=pols,
                                   ant=ant_list)

    attens = [attn]*len(sub_ant_mapping)
    _set_attenuation_by_mapping(sub_ant_mapping, attens)


def get_attenuation(ant_list, los, pols=ALL_POLS):
    """
    gets attenuation of provided antennas, los, and pols 

    Parameters
    ----------
    ant_list : list
        List of antenna names, e.g. ['1a', '2b']

    los : list
        List of tunings to target, e.g. ['a', 'b']

    pols : list
        List of polarisations to tune, e.g. ['x', 'y']
    """
    logger = logger_defaults.getModuleLogger(__name__)
    logger.debug("Entered 'get_attenuation' with parameters: %s %s %s"
                 %(ant_list, los, pols))

    assert len(ant_list) == len(set(ant_list)),\
            "Detected duplicate antennas in %s" %ant_list

    # TODO: assert all variables have correct types

    # Get all the antenna mapping configuration
    ant_mapping = get_antenna_mapping()

    # Make sure ant_list and lo_list are case-insensitive
    ant_list = [ant.lower() for ant in ant_list] 
    los      = [lo.lower() for lo in los]

    sub_ant_mapping = _select_from(ant_mapping, LO=los, pol=pols,
                                   ant=ant_list)

    sub_ant_mapping = _get_attenuation_by_mapping(sub_ant_mapping)
    logger.info("Output of get_attenuation:\n%s" %sub_ant_mapping)
    return sub_ant_mapping

def tune_if(ant_list, los, pols=ALL_POLS, desired_rms=RFSOC_RMS):
    """
    Tune the gain modules to a specific RMS value 

    Parameters
    ----------
    ant_list : list
        List of antenna names, e.g. ['1a', '2b']

    los : list
        List of tunings to target, e.g. ['a', 'b']

    rms : float or int
        RMS to set the RFSoC digitizers to 
    """
    logger = logger_defaults.getModuleLogger(__name__)
    logger.debug("Entered 'tune_if' with parameters: %s %s %s %s"
                 %(ant_list, los, pols, desired_rms))
    if type(ant_list) == np.ndarray:
        assert(ant_list.ndim == 1), "ant_list should be 1-dimensional"
    elif type(ant_list) != list:
        raise RuntimeError("ants should be a list")

    if type(los) == np.ndarray:
        assert(ant_list.ndim == 1), "los should be 1-dimensional"
    elif type(los) != list:
        raise RuntimeError("los should be a list")

    ant_mapping = get_antenna_mapping()
    
    # Make sure ant_list and lo_list are case-insensitive
    ant_list = [ant.lower() for ant in ant_list] 
    los      = [lo.lower() for lo in los]

    sub_ant_mapping = _select_from(ant_mapping, LO=los, pol=pols,
                                   ant=ant_list)

    sub_ant_mapping['desired_rms'] = [desired_rms] * len(sub_ant_mapping)
    unique_gain_modules = sub_ant_mapping['gain-module'].unique()

    ant_mappings_per_module = []
    # now let's divide the table into their respective gain modules
    for gain_module in unique_gain_modules:
        mask = np.isin(sub_ant_mapping['gain-module'], gain_module)
        ant_mapping_per_module = sub_ant_mapping[mask].copy()
        #_tune_if_by_module_threaded(ant_mapping_per_module)
        ant_mappings_per_module.append(ant_mapping_per_module)

    pool = ThreadPool(processes = NPROCS)
    pool.map(_tune_if_by_module_threaded, ant_mappings_per_module)


def _get_adc(rfsoc, pipeline_id):
    rfsoc.pipeline_id = pipeline_id
    x, y = (), ()
    for icycle in range(GET_ADC_CYCLES):
        xy = rfsoc.adc_get_samples()
        x += xy[0]
        y += xy[1]
    return x,y

def _tune_if_by_module_threaded(ant_mapping_per_module):
    """
    
    """
    logger = logger_defaults.getModuleLogger(__name__)
    logger.debug("Entered '_tune_if_by_module_threaded' with"\
            "thread_number: %i and ant_mapping:\n%s"\
                 %(threading.get_ident(), ant_mapping_per_module))

    # Set the attenuation to an initial value
    _set_attenuation_by_mapping(ant_mapping_per_module, 
                                [INIT_ATT]*len(ant_mapping_per_module)) 

    # An optimization here is to create 1 connection to each board, 
    # and manually change the "pipeline_id" attribute to switch between 
    # different antennas, rather than extablishing more than 1 
    # connection for each pipeline ID
    unique_rfsocs_pid = ant_mapping_per_module.hostname.unique()

    # I am assuming the hostnames are the following: "rfsocXX-ctrl-Y"
    # the [:-7] will remove the "-ctrl-7"
    unique_rfsoc = np.unique([i[:-7] for i in unique_rfsocs_pid])

    assert len(unique_rfsoc) == 1, "We should have 1 rfsoc per module"
    unique_rfsoc = unique_rfsoc[0]

    gain_module = ant_mapping_per_module['gain-module'].unique()[0]

    rfsoc = ata_rfsoc_fengine.AtaRfsocFengine(unique_rfsoc, pipeline_id = 0)
    ata_cfg = get_ata_cfg()
    rfsoc_fpg_file = ata_cfg['RFSOCFPG']

    for i in range(5):
        try:
            rfsoc.fpga.get_system_information(rfsoc_fpg_file)
            failed = False
            break
        except Exception as e:
            failed = True
            logger.error(e)
            logger.error("Trying again in 0.5s...")
            time.sleep(0.5)

    if failed:
        raise e

    logger.info("Initialized RFSoC: %s" %unique_rfsoc)

    #rfsoc = testRfsoc(unique_rfsoc)

    ant_mapping_per_module['meas_rms'] = [0.]*len(ant_mapping_per_module)
    ant_mapping_per_module['attn'] = [INIT_ATT]*len(ant_mapping_per_module)

    # Do the calculation twice
    for i in range(2):
        # populate the current rms values of the boards
        for unique_pid in unique_rfsocs_pid:
            pipeline_id = int(unique_pid[-1])
            x, y = _get_adc(rfsoc, pipeline_id-1) #TODO: implement!
            rms_x = np.std(x)
            rms_y = np.std(y)
            logger.info("RMS values for x,y: %.3f %.3f" %(rms_x, rms_y))

            tmp_mask = ant_mapping_per_module.hostname ==\
                    str(unique_rfsoc) + "-ctrl-%i" %pipeline_id
            tmp_mapping = ant_mapping_per_module[tmp_mask]

            if 'x' in list(tmp_mapping.pol):
                ant_mapping_per_module.loc[tmp_mask & 
                            (ant_mapping_per_module.pol == 'x'), 
                                           'meas_rms'] = rms_x
            if 'y' in list(tmp_mapping.pol):
                ant_mapping_per_module.loc[tmp_mask & 
                            (ant_mapping_per_module.pol == 'y'), 
                                           'meas_rms'] = rms_y

        # now calculate what attenuation we need to set 
        atten_diff = 20*np.log10(ant_mapping_per_module['meas_rms'] /
                                 ant_mapping_per_module['desired_rms'])
        ant_mapping_per_module['attn'] = _round50th(
                ant_mapping_per_module['attn'] + atten_diff)

        # apply the attenuation
        set_attn_by_module(gain_module,
                            list(ant_mapping_per_module.ch),
                            list(ant_mapping_per_module.attn))



def _set_attenuation_by_mapping(sub_ant_mapping, attens):
    """
    Same as ``set_attenutation`` funcion, but pass an antenna mapping matrix
    rather than antenna names, LOs and pols

    sub_ant_mapping : Pandas DataFrame
        subset of the antenna mapping table

    attens : list of floats
        list of attenuation values 
    """
    logger = logger_defaults.getModuleLogger(__name__)
    logger.debug("Entered '_set_attenuation_by_mapping' with parameters:\n"\
            "%s\n%s"%(sub_ant_mapping, attens))

    assert (len(sub_ant_mapping) == len(attens))

    unique_gain_modules = sub_ant_mapping['gain-module'].unique()

    sub_ant_mapping['attens'] = attens

    for gain_module in unique_gain_modules:
        mask = np.isin(sub_ant_mapping['gain-module'], gain_module)
        ant_mapping_per_module = sub_ant_mapping[mask]
        set_attn_by_module(gain_module,
                            list(ant_mapping_per_module.ch), 
                            list(ant_mapping_per_module.attens))

def _get_attenuation_by_mapping(sub_ant_mapping):
    """
    Same as ``get_attenutation`` funcion, but pass an antenna mapping matrix
    rather than antenna names, LOs and pols

    Parameters:
    ----------
    sub_ant_mapping : Pandas DataFrame
        subset of the antenna mapping table

    Returns:
    --------
    sub_ant_mapping : Pandas DataFrame
        same as input, with a "attens" columns for the attenuations read
    """
    logger = logger_defaults.getModuleLogger(__name__)
    logger.debug("Entered '_get_attenuation_by_mapping' with parameters:\n"\
            "%s"%(sub_ant_mapping))

    unique_gain_modules = sub_ant_mapping['gain-module'].unique()
    sub_ant_mapping['attens'] = [0.0]*len(sub_ant_mapping)

    for gain_module in unique_gain_modules:
        mask = np.isin(sub_ant_mapping['gain-module'], gain_module)
        ant_mapping_per_module = sub_ant_mapping[mask]
        attens = get_attn_by_module(gain_module,
                            list(ant_mapping_per_module.ch)) 
        logger.debug(attens)
        sub_ant_mapping.loc[mask, 'attens'] = attens

    return sub_ant_mapping


def set_attn_by_module(gain_module, chanlist, attenlist):
    """
    Sets the attenuation for each gain_module, with lists of channels 
    and attenuations
    Done through a POST request

    Parameters:
    -----------
    gain_module : str
        Hostname of the gain module

    chanlist : list of int
        List of channels to set attenuation

    attenlist : list of float
        List of attenuations to set for each channel
    """

    logger = logger_defaults.getModuleLogger(__name__)
    logger.debug("Entered 'set_attn_by_module' with parameters: "\
            "%s %s %s"%(gain_module, chanlist, attenlist))

    assert len(chanlist) == len(attenlist)
    chanlist  = np.array(chanlist)
    attenlist = np.array(attenlist)

    if np.any(attenlist > MAX_ATT):
        warn_chan_list = chanlist[attenlist > MAX_ATT]
        warn_atten     = attenlist[attenlist > MAX_ATT]
        warnings.warn("Trying to set %s on channels %s " 
                      "to values %s, which is more than max [%i]"
                      %(gain_module, list(warn_chan_list), list(warn_atten),
                        MAX_ATT))
        attenlist[attenlist > MAX_ATT] = MAX_ATT

    if np.any(attenlist < MIN_ATT):
        warn_chan_list = chanlist[attenlist < MIN_ATT]
        warn_atten     = attenlist[attenlist < MIN_ATT]
        warnings.warn("Trying to set %s on channels %s " 
                      "to values %s, which is less than min [%i]"
                      %(gain_module, list(warn_chan_list), list(warn_atten),
                        MIN_ATT))
        attenlist[attenlist < MIN_ATT] = MIN_ATT

    # URL for the specific gain-module we are requesting
    baseurl = f"http://{gain_module}:{RESTGW_PORT}/set"
    payload = {"channels": chanlist.tolist(), "values": attenlist.tolist()}

    # Attempt the SET request
    logger.debug(f"Attempting POST request on {baseurl} with payload: {payload}")
    response = requests.post(baseurl, json=payload)

    if response.status_code == 200:
        logger.debug(f"Success, POST request returned status code: 200")
        attens = response.json().get("updated_values")
    else:
        logger.error(f"Error with SET request on {baseurl}")
        raise APIError(response.status_code, response.text)



def get_attn_by_module(gain_module, chanlist=None):
    """
    Gets the attenuation for each gain_module, and lists of channels
    Done through a GET request

    Parameters:
    -----------
    gain_module : str
        Hostname of the gain module

    chanlist : list of int
        List of channels to set attenuation

    Returns:
    --------
    attens : list of float
        List of attenuations
    """

    logger = logger_defaults.getModuleLogger(__name__)
    logger.debug("Entered 'get_attn_by_module' with parameters: "\
            "%s %s"%(gain_module, chanlist))

    if not gain_module.endswith(".hcro.org"):
        gain_module += ".hcro.org"

    # URL for the specific gain-module we are requesting
    baseurl = f"http://{gain_module}:{RESTGW_PORT}/get"
    if chanlist:
        channel_query = ",".join(map(str, chanlist))
        channel_query_dict = {"channels": channel_query}
    else: #requested all channels
        channel_query_dict = None

    # Attempt the GET request
    logger.debug(f"Attempting GET request on {baseurl}")
    response = requests.get(baseurl, params=channel_query_dict)

    if response.status_code == 200:
        logger.debug(f"Success, GET request returned status code: 200")
        attens = response.json().get("values")
        return attens
    else:
        logger.error(f"Error with GET request on {baseurl}")
        raise APIError(response.status_code, response.text)
