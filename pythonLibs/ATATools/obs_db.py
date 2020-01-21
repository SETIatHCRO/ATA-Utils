#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
operations on observator (obs) database

Created Jan 2020

@author: jkulpa
"""

from  ATASQL import connect
import logger_defaults
import ata_control

def getObsType(string):
    """
    supported types: frb, calibration, on-off, pulsar, other        
    """
    lstring = string.lower()
    if lstring in ['frb']:
        return 'FRB'
    elif lstring in ['calibration','cal']:
        return 'CALIBRATION'
    elif lstring in ['onoff','on-off']:
        return 'ON-OFF'
    elif lstring in ['pulsar']:
        return 'PULSAR'
    else:
        return 'OTHER'

def getBackend(string):
    """
    supported backends: frb, beamformer, correlator, snap
    """
    lstring = string.lower()
    if lstring in ['bf','beamformer']:
        return 'BEAMFORMER'
    elif lstring in ['frb']:
        return 'FRB'
    elif lstring in ['correlator']:
        return 'CORRELATOR'
    elif lstring in ['snap']:
        return 'SNAP'
    else:
        raise KeyError('Unknown backend')

def getNewObsSetID(description="n/a"):
    """
    Get new unique observation set ID

    Parameters
    -------------
    description : str
        optional description of the set. default is "n/a"

    Returns
    -------------
    long
        observation set id

    """

    logger= logger_defaults.getModuleLogger(__name__)

    mydb = connect.connectObsDb()
    mycursor = mydb.cursor()

    insertcmd = ("insert into obs_sets set description=%(des)s")
    dict1 = {'des': description}

    logger.info("adding description {0!s}".format(description))
    
    mycursor.execute(insertcmd,dict1)
    mydb.commit()
    myid = mycursor.lastrowid

    logger.info("got id {}".format(myid))

    mycursor.close()
    mydb.close()

    return myid

def initAntennasTable(obsid,antlist,sources,azs=0.0,els=0.0, getpams=True):
    """
    Populates the antenna table with sources, azimuths and elevations, and by default with pam values


    Parameters
    -------------
    obsid : long
        observation id
    antlist : str list
        list of antennas, short names, ie ['1a','2b']
    sources : str list or str
        list of sources per antenna, or single string for all antennas
    azs : float list or float
        list of azimut offsets of azimut offset for all antennas from the source
    els : float list or float
        list of elevation offests or azimut offest for all antennas from the source
    getpams : bool
        flag if pam values should be read and updated

    """

    #if input is a single object, mutliply it by number of antennas
    nants = len(antlist)
    if not isinstance(sources,list):
        sources = [sources] * nants;

    if not isinstance(azs,list):
        azs = [azs] * nants;

    if not isinstance(els,list):
        els = [els] * nants;

    
    logger= logger_defaults.getModuleLogger(__name__)

    mydb = connect.connectObsDb()
    mycursor = mydb.cursor()

    insertcmdpams = ("insert into obs_ants set id=%(id)s, ant=%(ant)s, az=%(az)s, el=%(el)s, "
                     "source=%(src)s, pamx=%(pamx)s, pamy=%(pamy)s")

    insertcmdnopams = ("insert into obs_ants set id=%(id)s, ant=%(ant)s, az=%(az)s, el=%(el)s, "
                     "source=%(src)s")

    if getpams:
        try:
            logger.info("getting pam values")
            pamvals = ata_control.get_pams(antlist)
        except:
            logger.exception("unable to get pams, ignoring flag")
            getpams = False

    #this is not the cleanest way. Probably the itertools.izip should be used
    for x in xrange(nants):
        cant = antlist[x]
        dict1 = {'id': obsid, 'ant': cant, 'az': azs[x], 'el': els[x], 'src': sources[x]}
        if getpams:
            insertcmd = insertcmdpams
            dict1['pamx'] = pamvals[cant + 'x']
            dict1['pamy'] = pamvals[cant + 'y']
        else:
            insertcmd = insertcmdnopams

        logger.info("commiting for ant {}".format(cant))
        mycursor.execute(insertcmd,dict1)
        mydb.commit()

    mycursor.close()
    mydb.close()
    


def initObservation(frequency,obstype,obsbackend,description,observer="unknown",setid=None):
    """
    Crates new observation entry and retruns new observation

    Parameters
    -------------
    frequency: float
        center frequency
    obstype : str
        type of the observation. see getObsType
    obsbackend : str
        backend of the observation. see getObsBackend
    description : str
        observation description
    observer : str
        observer description. default unknown
    setid : long
        id of observation set. If observation does not belong to a set, leave None. default None

    Returns
    -------------
    long
        observation id

    Raises
    -------------
    KeyError

    """

    logger= logger_defaults.getModuleLogger(__name__)

    mydb = connect.connectObsDb()
    mycursor = mydb.cursor()

    if setid:
        insertcmd = ("insert into observations set freq=%(freq)s, type=%(obstype)s, backend=$(obsbackend)s, observer=%(observer)s, description=%(desc)s, setid=%(setid)s")
        dict1 = {'freq': frequency, 'obstype' : getObsType(obstype), 'obsbackend' : getObsBackend(obsbackend), 'observer' : observer, 'desc' : description, 'setid' : setid}
    else:
        insertcmd = ("insert into observations set freq=%(freq)s, type=%(obstype)s, backend=$(obsbackend)s, observer=%(observer)s, description=%(desc)s")
        dict1 = {'freq': frequency, 'obstype' : getObsType(obstype), 'obsbackend' : getObsBackend(obsbackend), 'observer' : observer, 'desc' : description}

    logger.info("adding new observation {}".format( str(dict1) ))
    mycursor.execute(insertcmd,dict1)
    mydb.commit()
    myid = mycursor.lastrowid

    logger.info("got id {}".format(myid))

    mycursor.close()
    mydb.close()

    return myid

def startObservation(obsid):
    """
    updates observation start time of obsid observation to now()
    """
    logger= logger_defaults.getModuleLogger(__name__)

    mydb = connect.connectObsDb()
    mycursor = mydb.cursor()
    
    insertcmd = ("update observations set tstart=now(), status='STARTED' where id=%(id)s")
    dict1 = {'id': obsid}

    logger.info("updating start time of the observation")
    mycursor.execute(insertcmd,dict1)
    mydb.commit()

    mycursor.close()
    mydb.close()


def stopObservation(obsid):
    """
    updates observation stop time of obsid observation to now()
    """
    logger= logger_defaults.getModuleLogger(__name__)

    mydb = connect.connectObsDb()
    mycursor = mydb.cursor()
    
    insertcmd = ("update observations set tstop=now(), status='STOPPED' where id=%(id)s")
    dict1 = {'id': obsid}

    logger.info("updating stop time of the observation")
    mycursor.execute(insertcmd,dict1)
    mydb.commit()

    mycursor.close()
    mydb.close()

def markObservationsBAD(obsid_list):
    """
    mark observations as bad. 
    """

    if not isinstance(obsid_list,list) and len(obsid_list) == 1:
        obsid_list = [obsid_list]

    logger= logger_defaults.getModuleLogger(__name__)

    mydb = connect.connectObsDb()
    mycursor = mydb.cursor()

    insertcmd_part = ("update observations set status='BAD' where id in (%s)")
    in_p=', '.join(map(lambda x: '%s', obsid_list))
    insertcmd = insertcmd_part % in_p;
    
    logger.info("changing status of observations {} to BAD".format(', '.join(obsid_list)))

    mycursor.execute(insertcmd,obsid_list)
    mydb.commit()
    
    mycursor.close()
    mydb.close()

def markObservationsOK(obsid_list):
    """
    mark observations as ok. 
    """

    if not isinstance(obsid_list,list) and len(obsid_list) == 1:
        obsid_list = [obsid_list]

    logger= logger_defaults.getModuleLogger(__name__)

    mydb = connect.connectObsDb()
    mycursor = mydb.cursor()

    insertcmd_part = ("update observations set status='OK' where id in (%s)")
    in_p=', '.join(map(lambda x: '%s', obsid_list))
    insertcmd = insertcmd_part % in_p;
    
    logger.info("changing status of observations {} to OK".format(', '.join(obsid_list)))

    mycursor.execute(insertcmd,obsid_list)
    mydb.commit()
    
    mycursor.close()
    mydb.close()

def getSetData(setid):
    """
    Get description and timestamp of data set

    Parameters
    -------------
        setid : long
            

    Returns
    -------------
        str
            description
        datetime
            timestamp

    Raises
    -------------
        KeyError

    """

    logger= logger_defaults.getModuleLogger(__name__)

    mydb = connect.connectObsDb()
    mycursor = mydb.cursor()

    insertcmd = ("select ts,description from obs_sets where id=%(myid)s")
    dict1 = {'myid': setid}

    logger.info("fetching info from set {}".format(setid))
    
    mycursor.execute(insertcmd,dict1)
    row = mycursor.fetchone()
    if not row:
        logger.error("Key {} not found in database".format(setid))
        raise KeyError("ID not found in the database")


    descr = row[1]
    ts = row[0]
    logger.info("SET {}: at {} ( {} )".format(setid,ts,descr))

    mycursor.close()
    mydb.close()

    return ts,descr


