#!/usr/bin/python3

"""
Python library to obtain state and positions of various
astronomical/satellite objects
"""

from . import logger_defaults
from .ata_rest import ATARest


def get_sats(allSats=False):
    """
    Get satellites that are currently (i.e. time the function
    was called) above the ATA.
    Emulates the behaviour of obs@control:~/$atasats

    Parameters
    ----------
    allSats : bool
        list all satellites and positions regardless of elevation

    Returns
    -------
    satellites : dict
        dictionary of list of dictionaries of satellite parameters.
    

    Examples
    --------
    >>> sats = get_sats()
    >>> print(sats['GPS'])
    [{'name': 'GPS-BIIF-10--PRN-08-',
      'az': '44.081',
      'el': '22.919',
      'state': 'Setting'},
     {'name': 'GPS-BIIF-5---PRN-30-',
      'az': '53.549',
      'el': '76.608',
      'state': 'Setting'},
     ...
    ]
    """

    logger = logger_defaults.getModuleLogger(__name__)


    if allSats:
        raise NotImplementedError("allSats = True is not implemented")

    try:
        endpoint = '/satellites'
        response = ATARest.get(endpoint)
        return response
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise


def check_source(sourcename):
    """
    Get visibility status of source
    Emulates the behaviour of atacheck utility

    Parameters
    ----------
    sourcename: str
        Name of source (satellite, solar system body, astronomical catalog name)

    Returns
    -------
    dictionary of source attributes
    

    Examples
    --------
    >>> info = check_source('casa')
    >>> print(info)
    {
        'az': 350.72113037109375,
        'dec': 58.80799865722656,
        'el': 10.83260726928711,
        'is_up': False,
        'object': 'casa',
        'ra': 23.391000747680664,
        'rise_time': 1621837379433419184,
        'set_time': 1621901955350964440
    }
    """
    logger = logger_defaults.getModuleLogger(__name__)

    try:
        endpoint = '/source'
        response = ATARest.get(endpoint, json={'source': sourcename})
        return response
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise
