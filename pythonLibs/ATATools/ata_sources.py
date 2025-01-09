#!/usr/bin/python3

"""
Python library to obtain state and positions of various
astronomical/satellite objects
"""

from datetime import datetime, timezone, timedelta
import pytz

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


def check_radec(ra, dec):
    """
    Get visibility status of a ra, dec pointing

    Parameters
    ----------
    ra : float
        Right ascension [in decimal hours]
    dec: float
        Declination [in decimal degrees]

    Returns
    -------
    dictionary of Ra/DEC attributes

    Examples
    --------
    >>> info = check_radec(23.390774, 58.807776)
    >>> print(info)
    {
        'object': 'RADec[23.390774,58.807776]',
        'is_up': True,
        'az': 327.242431640625,
        'el': 25.636306762695312,
        'ra': 23.39077256355449,
        'dec': 58.80778438531889,
    # Rise and set times in UTC
        'rise_time_posix': 1718082627,
        'set_time_posix': 1718061064,
        'rise_time': datetime.datetime(2024, 6, 11, 5, 10, 27, tzinfo=datetime.timezone.utc),
        'set_time': datetime.datetime(2024, 6, 10, 23, 11, 4, tzinfo=datetime.timezone.utc)
    }
    """
    logger = logger_defaults.getModuleLogger(__name__)

    radec = [ra, dec]
    try:
        endpoint = '/source'
        response = ATARest.get(endpoint, json={'radec': radec})

        if response['rise_time_posix']:
            response['rise_time'] =\
                    datetime.fromtimestamp(response['rise_time_posix'],
                            timezone.utc)
        if response['set_time_posix']:
            response['set_time'] =\
                    datetime.fromtimestamp(response['set_time_posix'],
                            timezone.utc)

        return response
    except Exception as e:
        logger.error('{:s} got error: {:s}'.format(endpoint, str(e)))
        raise

def is_timezone_aware(dt: datetime) -> bool:
    """Checks if a datetime object is timezone aware."""
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def check_source_str(dt, radec=None, sourcename=None):
    """
    Get visibility status of a ra/dec pair, or a source

    Parameters
    ----------
    dt : datetime.datetime
        datetime object of when the source want to be checked

    ra,dec : List
        Right ascension and Declination [decimal hours, decimal degrees]
    sourcename: str
        Name of source (sat, solar system body, astronomical catalog name)

    Returns
    -------
    str that can be printed for info

    Examples
    --------
    >>> info = check_source_str(source='3c286')
    >>> print(info)
    3c286 is not up.
    RA, Dec = 13.518969, 30.509155
    Az, El = (315.913, -3.247): Sat Dec 14 16:27:37 PST 2024 (LST 21:57:46.67).
    Rises > 16.5 deg          : Sun Dec 15 01:44:15 PST 2024 (LST 07:15:55.40).
    Sets  < 16.5 deg          : Sun Dec 15 14:14:54 PST 2024 (LST 19:48:37.71).
    """
    from astropy.coordinates import EarthLocation
    from astropy import units as u
    from astropy.time import Time
    from astropy.utils.iers import LeapSeconds

    LONGITUDE = "-121:28:14.65"
    LATITUDE  = "40:49:02.75"
    ALTITUDE  = 1019.222
    OBSERVATORY = EarthLocation(lon=LONGITUDE,
            lat=LATITUDE, height=ALTITUDE)

    DATETIME_FMT = "%a %b %d %H:%M:%S %Z %Y"

    PST_TZ = pytz.timezone('US/PACIFIC')

    LEAP_SEC    = LeapSeconds.auto_open()['tai_utc'][-1]
    LEAP_SEC_DT = timedelta(seconds=float(LEAP_SEC))

    if (radec is not None) and (sourcename is not None):
        raise RuntimeError('Provide only "source" or "RA/Dec" pair')

    if sourcename:
        assert type(sourcename) == str
        source = check_source(sourcename)
    elif radec:
        assert type(radec) == list
        source = check_radec(*radec)

    assert type(dt) == datetime
    assert is_timezone_aware(dt), "Make sure dt is timezone aware"

    output_str="\n"

    if source['is_up']:
        output_str += "%s is up.\n" %source['object']
    else:
        if 'rise_time' not in source:
            output_str += "%s is never up.\n" %source['object']
        else:
            output_str += "%s is not up.\n" %source['object']

    # Ra Dec line
    output_str += "RA, Dec = %.6f, %.6f\n" %(source['ra'],
            source['dec'])

    # Az El line
    date = dt + LEAP_SEC_DT
    date_no_ls = dt
    azel_str = "Az, El = (%.3f, %.3f)" %(source['az'],
            source['el'])
    output_str += azel_str
    lst_now = Time(date_no_ls, location=OBSERVATORY).sidereal_time('mean')
    lst_now_str = lst_now.to_string(sep=":", precision=2, pad=True)
    output_str += ": %s" %date.strftime(DATETIME_FMT)
    output_str += " (LST %s).\n" %lst_now_str

    # Rise time line
    if 'rise_time' in source:
        rises_str = "Rises > 16.5 deg"
        # make it match the above line
        rises_str += " "*(len(azel_str) - len(rises_str))
        source_rise_time = source['rise_time'].astimezone(PST_TZ) + LEAP_SEC_DT
        source_rise_time_no_ls = source['rise_time'].astimezone(PST_TZ)
        rises_str += ": %s" %source_rise_time.strftime(DATETIME_FMT)
        lst_rise = Time(source_rise_time_no_ls,
                location=OBSERVATORY).sidereal_time('mean')
        lst_rise_str = lst_rise.to_string(sep=":", precision=2, pad=True)
        output_str += rises_str
        output_str += " (LST %s).\n" %lst_rise_str

    # Set time line
    if 'set_time' in source:
        set_str = "Sets  < 16.5 deg"
        # make it match the above line
        set_str += " "*(len(azel_str) - len(set_str))
        source_set_time = source['set_time'].astimezone(PST_TZ) + LEAP_SEC_DT
        source_set_time_no_ls = source['set_time'].astimezone(PST_TZ)
        set_str += ": %s" %source_set_time.strftime(DATETIME_FMT)
        lst_set = Time(source_set_time_no_ls,
                location=OBSERVATORY).sidereal_time('mean')
        lst_set_str = lst_set.to_string(sep=":", precision=2, pad=True)
        output_str += set_str
        output_str += " (LST %s).\n" %lst_set_str

    # Now let's return
    return output_str
