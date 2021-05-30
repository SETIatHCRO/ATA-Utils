#!/usr/bin/python3

"""
Python library to obtain state and positions of various
astronomical/satellite objects
"""

from datetime import datetime, timezone

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
        'az': 329.0008850097656,
        'dec': 58.80799865722656,
        'el': 23.649778366088867,
        'is_up': True,
        'object': 'casa',
        'ra': 23.391000747680664,
    # Rise and set times in UTC
        'rise_time_posix': 1622354327,
        'rise_time': datetime.datetime(2021, 5, 30, 5, 58, 47, tzinfo=datetime.timezone.utc),
        'set_time_posix': 1622332739
        'set_time': datetime.datetime(2021, 5, 29, 23, 58, 59, tzinfo=datetime.timezone.utc),
    }
    """
    logger = logger_defaults.getModuleLogger(__name__)

    try:
        endpoint = '/source'
        response = ATARest.get(endpoint, json={'source': sourcename})

        if response['rise_time_posix']:
            response['rise_time'] = datetime.fromtimestamp(response['rise_time_posix'], timezone.utc)
        if response['set_time_posix']:
            response['set_time'] = datetime.fromtimestamp(response['set_time_posix'], timezone.utc)
            
        return response
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise
