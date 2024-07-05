import pandas as pd
import numpy as np
from multiprocessing.pool import ThreadPool
import threading
import warnings

from ATATools import logger_defaults
from SNAPobs import snap_defaults, snap_config, snap_control


# TODO: move and put in a config file
RFSOC_RMS = 1024
ALL_LOS = ['a', 'b', 'c', 'd']
ALL_POLS = ['x', 'y']

INIT_ATT = 23

MAX_ATT = 31.5
MIN_ATT = 0.0

NPROCS = 10

GET_ADC_CYCLES = 3 #Number of adc sample cycles to get

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
    return d



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

    isin_ant = np.isin(ant_mapping['#ant'], ant_list)
    isin_lo  = np.isin(ant_mapping['LO'], los)
    isin_pol = np.isin(ant_mapping['pol'], pols)

    ant_mapping_mask = isin_ant & isin_lo & isin_pol

    sub_ant_mapping = ant_mapping[ant_mapping_mask].copy()

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

    isin_ant = np.isin(ant_mapping['#ant'], ant_list)
    isin_lo  = np.isin(ant_mapping['LO'], los)
    isin_pol = np.isin(ant_mapping['pol'], pols)

    ant_mapping_mask = isin_ant & isin_lo & isin_pol

    sub_ant_mapping = ant_mapping[ant_mapping_mask].copy()

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

    isin_ant = np.isin(ant_mapping['#ant'], ant_list)
    isin_lo  = np.isin(ant_mapping['LO'], los)
    isin_pol = np.isin(ant_mapping['pol'], pols)

    ant_mapping_mask = isin_ant & isin_lo & isin_pol

    sub_ant_mapping = ant_mapping[ant_mapping_mask].copy()

    sub_ant_mapping['desired_rms'] = [desired_rms] * len(sub_ant_mapping)
    unique_gain_modules = sub_ant_mapping['gain-module'].unique()

    ant_mappings_per_module = []
    # now let's divide the table into their respective gain modules
    for gain_module in unique_gain_modules:
        mask = np.isin(sub_ant_mapping['gain-module'], gain_module)
        ant_mappings_per_module.append(sub_ant_mapping[mask].copy())

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

    rfsoc = snap_control.init_snaps(unique_rfsoc)[0]
    snap_control.get_system_information([rfsoc])
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
        _set_attn_by_module(gain_module,
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
        _set_attn_by_module(gain_module, 
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
        attens = _get_attn_by_module(gain_module, 
                            list(ant_mapping_per_module.ch)) 
        logger.debug(attens)
        sub_ant_mapping.loc[mask, 'attens'] = attens

    return sub_ant_mapping


def _set_attn_by_module(gain_module, chanlist, attenlist):
    """
    Sets the attenuation for each gain_module, with lists of channels 
    and attenuations
    This will eventually be replaced by something other than ssh-based

    Parameters:
    -----------
    gain_module : str
        Hostname of the gain module

    chanlist : list of int
        List of channels to set attenuation

    attenlist : list of float
        List of attenuations to set for each channel
    """
    import subprocess 

    logger = logger_defaults.getModuleLogger(__name__)
    logger.debug("Entered '_set_attn_by_module' with parameters: "\
            "%s %s %s"%(gain_module, chanlist, attenlist))

    assert len(chanlist) == len(attenlist)
    chanlist  = np.array(chanlist)
    attenlist = np.array(attenlist)

    if np.any(attenlist > MAX_ATT):
        warn_chan_list = chanlist[attenlist > MAX_ATT]
        warn_atten     = attenlist[attenlist > MAX_ATT]
        warnings.warn("Trying to set attenuator on channels %s " 
                      "to values %s, which is more than max [%i]"
                      %(list(warn_chan_list), list(warn_atten),
                        MAX_ATT))
        attenlist[attenlist > MAX_ATT] = MAX_ATT

    if np.any(attenlist < MIN_ATT):
        warn_chan_list = chanlist[attenlist < MIN_ATT]
        warn_atten     = attenlist[attenlist < MIN_ATT]
        warnings.warn("Trying to set attenuator on channels %s " 
                      "to values %s, which is less than min [%i]"
                      %(list(warn_chan_list), list(warn_atten),
                        MIN_ATT))
        attenlist[attenlist < MIN_ATT] = MIN_ATT

    logger = logger_defaults.getModuleLogger(__name__)
    command = "ssh sonata@%s "%gain_module
    command += "'python attenuatorMain.py"
    command += " -n "
    command += " ".join([str(i) for i in chanlist])
    command += " -a "
    command += " ".join(["%.1f"%i for i in attenlist])
    command += "'"

    logger.info(command)
    #process = subprocess.Popen(command, stdout=subprocess.PIPE,
    #        stderr=subprocess.PIPE, shell=True)

    #stdout, stderr = process.communicate()



def _get_attn_by_module(gain_module, chanlist):
    """
    Gets the attenuation for each gain_module, and lists of channels
    This will eventually be replaced by something other than ssh-based

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
    import subprocess 

    logger = logger_defaults.getModuleLogger(__name__)
    logger.debug("Entered '_get_attn_by_module' with parameters: "\
            "%s %s"%(gain_module, chanlist))

    chanlist  = np.array(chanlist)

    logger = logger_defaults.getModuleLogger(__name__)
    command = "ssh sonata@%s.hcro.org "%gain_module
    command += "'python attenuatorMain.py"
    command += " -n "
    command += " ".join(["%i"%i for i in chanlist])
    command += " -g "
    command += "'"

    logger.info(command)
    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, shell=True)

    stdout, stderr = process.communicate()
    logger.debug("return of getatten subprocess:\n%s" %stdout)
    ch_if_attn = _translate_if_output(stdout) #output if dictionary
    logger.debug("translated output:\n%s" %ch_if_attn)

    attens = []
    for chan in chanlist:
        attens += [float(ch_if_attn[str(chan)])]
    return attens

def _translate_if_output(stdout):
    # python 2 output
    # stdout of shape: '(1, 13.5)\n(2, 14.0)\n(9, 7.5)\n(10, 0.5)\n(13, 5.5)\n(14, 3.5)
    # python 3 output
    # stdout of shape: 1 15.0\n2 15.0\n11 15.0\n12 15.0\n

    ret = stdout.decode().strip()

    pairs = ret.split("\n")
    retdict = {}
    for i in pairs:
        if i.startswith("("):
            tmp = i.strip("(").strip(")")
            tmp = tmp.replace(" ","").split(",")
        else:
            tmp = i.split(" ")

        retdict[tmp[0]] = tmp[1]
    #print(retdict)
    return retdict
