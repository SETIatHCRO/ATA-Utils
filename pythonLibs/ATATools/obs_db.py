#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
operations on observator (obs) database

Created Jan 2020

@author: jkulpa
"""

from . import logger_defaults
from . import ata_control
import ATASQL

def getRecType(string):
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

def getRecBackend(string):
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
    int
        observation set id

    """

    logger= logger_defaults.getModuleLogger(__name__)

    mydb = ATASQL.connectObsDb()
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

def initAntennasTable(recid,antlist,sources,azs=0.0,els=0.0, getpams=True):
    """
    Populates the antenna table with sources, azimuths and elevations, and by default with pam values


    Parameters
    -------------
    recid : int
        recording id
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

    mydb = ATASQL.connectObsDb()
    mycursor = mydb.cursor()

    insertcmdpams = ("insert into rec_ants set id=%(id)s, ant=%(ant)s, az=%(az)s, el=%(el)s, "
                     "source=%(src)s, pamx=%(pamx)s, pamy=%(pamy)s, pamdetx=%(pamdetx)s, pamdety=%(pamdety)s")

    insertcmdnopams = ("insert into rec_ants set id=%(id)s, ant=%(ant)s, az=%(az)s, el=%(el)s, "
                     "source=%(src)s")

    if getpams:
        try:
            logger.info("getting pam values")
            pamvals = ata_control.get_pams(antlist)
            detvals = ata_control.get_dets(antlist)
        except:
            logger.exception("unable to get pams, ignoring flag")
            getpams = False

    #this is not the cleanest way. Probably the itertools.izip should be used
    for x in range(nants):
        cant = antlist[x]
        dict1 = {'id': recid, 'ant': cant, 'az': azs[x], 'el': els[x], 'src': sources[x]}
        if getpams:
            insertcmd = insertcmdpams
            dict1['pamx'] = pamvals['ant' + cant + 'x']
            dict1['pamy'] = pamvals['ant' + cant + 'y']
            dict1['pamdetx'] = detvals['ant' + cant + 'x']
            dict1['pamdety'] = detvals['ant' + cant + 'y']
        else:
            insertcmd = insertcmdnopams

        logger.info("commiting for ant {}".format(cant))
        mycursor.execute(insertcmd,dict1)
        mydb.commit()

    mycursor.close()
    mydb.close()
    


def initRecording(frequency,obstype,obsbackend,description,observer="unknown",setid=None):
    """
    Crates new recording entry and retruns new recording id

    Parameters
    -------------
    frequency: float
        center frequency
    obstype : str
        type of the recording. see getRecType
    obsbackend : str
        backend of the recording. see getRecBackend
    description : str
        observation description
    observer : str
        observer description. default unknown
    setid : int
        id of observation set. If observation does not belong to a set, leave None. default None

    Returns
    -------------
    int
        recording id

    Raises
    -------------
    KeyError

    """

    logger= logger_defaults.getModuleLogger(__name__)

    mydb = ATASQL.connectObsDb()
    mycursor = mydb.cursor()

    if setid:
        insertcmd = ("insert into recordings set freq=%(freq)s, type=%(obstype)s, backend=%(obsbackend)s, observer=%(observer)s, description=%(desc)s, setid=%(setid)s")
        dict1 = {'freq': frequency, 'obstype' : getRecType(obstype), 'obsbackend' : getRecBackend(obsbackend), 'observer' : observer, 'desc' : description, 'setid' : setid}
    else:
        insertcmd = ("insert into recordings set freq=%(freq)s, type=%(obstype)s, backend=%(obsbackend)s, observer=%(observer)s, description=%(desc)s")
        dict1 = {'freq': frequency, 'obstype' : getRecType(obstype), 'obsbackend' : getRecBackend(obsbackend), 'observer' : observer, 'desc' : description}

    logger.info("adding new observation {}".format( str(dict1) ))
    mycursor.execute(insertcmd,dict1)
    mydb.commit()
    myid = mycursor.lastrowid

    logger.info("got id {}".format(myid))

    mycursor.close()
    mydb.close()

    return myid

def startRecording(obsid):
    """
    updates recording start time of obsid recording to now()
    """
    logger= logger_defaults.getModuleLogger(__name__)

    mydb = ATASQL.connectObsDb()
    mycursor = mydb.cursor()
    
    insertcmd = ("update recordings set tstart=now(), status='STARTED' where id=%(id)s")
    dict1 = {'id': obsid}

    logger.info("updating start time of the recording")
    mycursor.execute(insertcmd,dict1)
    mydb.commit()

    mycursor.close()
    mydb.close()


def stopRecording(obsid):
    """
    updates recording stop time of obsid recording to now()
    """
    logger= logger_defaults.getModuleLogger(__name__)

    mydb = ATASQL.connectObsDb()
    mycursor = mydb.cursor()
    
    insertcmd = ("update recordings set tstop=now(), status='STOPPED' where id=%(id)s")
    dict1 = {'id': obsid}

    logger.info("updating stop time of the recording")
    mycursor.execute(insertcmd,dict1)
    mydb.commit()

    mycursor.close()
    mydb.close()

def markRecordingsBAD(obsid_list):
    """
    mark recordings as bad. 
    """

    logger= logger_defaults.getModuleLogger(__name__)
    if not obsid_list:
        logger.warning('List is empty!')
        return

    if not isinstance(obsid_list,list) and len(obsid_list) == 1:
        obsid_list = [obsid_list]

    mydb = ATASQL.connectObsDb()
    mycursor = mydb.cursor()

    insertcmd_part = ("update recordings set status='BAD' where id in (%s)")
    #in_p=', '.join(map(lambda x: '%s', obsid_list))
    in_p=', '.join(['%s'] * len(obsid_list))
    insertcmd = insertcmd_part % in_p;
    
    logger.info("changing status of recordings {} to BAD".format(', '.join(map(str,obsid_list))))

    mycursor.execute(insertcmd,obsid_list)
    mydb.commit()
    
    mycursor.close()
    mydb.close()

def markRecordingsOK(obsid_list):
    """
    mark recordings as ok. 
    """
    logger= logger_defaults.getModuleLogger(__name__)
    if not obsid_list:
        logger.warning('List is empty!')
        return

    if not isinstance(obsid_list,list) and len(obsid_list) == 1:
        obsid_list = [obsid_list]


    mydb = ATASQL.connectObsDb()
    mycursor = mydb.cursor()

    insertcmd_part = ("update recordings set status='OK' where id in (%s)")
    #in_p=', '.join(map(lambda x: '%s', obsid_list))
    in_p=', '.join(['%s'] * len(obsid_list))
    insertcmd = insertcmd_part % in_p;
    
    logger.info("changing status of recordings {} to OK".format(', '.join(map(str,obsid_list))))

    mycursor.execute(insertcmd,obsid_list)
    mydb.commit()
    
    mycursor.close()
    mydb.close()

def getSetData(setid):
    """
    Get description and timestamp of data set

    Parameters
    -------------
        setid : int
            

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

    mydb = ATASQL.connectObsDb()
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

def updateAttenRMSVals(cobsid,attendict):
    """
    update the antennas information with a given dictionary
    dictionary example: 
    { '1a': {'attenx': 17, 'rmsy': 0.3544, 'rmsx': 12.2489, 'atteny': 0},
      '2a': {'attenx': 30, 'rmsy': 0.3846, 'rmsx': 26.9986, 'atteny': 0}   }

    """

    logger= logger_defaults.getModuleLogger(__name__)

    mydb = ATASQL.connectObsDb()
    mycursor = mydb.cursor()

    insertcmd = ("update rec_ants set dsp_atten_x=%(attenx)s, dsp_atten_y=%(atteny)s, "
            "dsp_rms_x=%(rmsx)s, dsp_rms_y=%(rmsy)s where ant=%(ant)s and id=%(id)s")

    for ant in attendict.keys():
        cdict = attendict[ant].copy()
        logger.info("updating attenuators/rms row for ant {} and recording id {}".format(ant,cobsid))
        cdict['ant'] = ant
        cdict['id']=cobsid
        mycursor.execute(insertcmd,cdict)
        mydb.commit()

    mycursor.close()
    mydb.close()

def updateAttenVals(cobsid,attendict):
    """
    update the antennas information with a given dictionary
    dictionary example: 
    { '1a': {'attenx': 17, 'atteny': 0},
      '2a': {'attenx': 30, 'atteny': 0}   }

    """

    logger= logger_defaults.getModuleLogger(__name__)

    mydb = ATASQL.connectObsDb()
    mycursor = mydb.cursor()

    insertcmd = ("update rec_ants set dsp_atten_x=%(attenx)s, dsp_atten_y=%(atteny)s where ant=%(ant)s and id=%(id)s")

    for ant in attendict.keys():
        cdict = {'ant' : ant, 'id':cobsid, 'attenx': attendict[ant]['attenx'], 'atteny': attendict[ant]['atteny']}
        logger.info("updating attenuators row for ant {} and recording id {}".format(ant,cobsid))
        mycursor.execute(insertcmd,cdict)
        mydb.commit()

    mycursor.close()
    mydb.close()

def updateRMSVals(cobsid,attendict):
    """
    update the antennas information with a given dictionary
    dictionary example: 
    { '1a': {'rmsy': 0.3544, 'rmsx': 12.2489},
      '2a': {'rmsy': 0.3846, 'rmsx': 26.9986}   }

    """

    logger= logger_defaults.getModuleLogger(__name__)

    mydb = ATASQL.connectObsDb()
    mycursor = mydb.cursor()

    insertcmd = ("update rec_ants set dsp_rms_x=%(rmsx)s, dsp_rms_y=%(rmsy)s where ant=%(ant)s and id=%(id)s")

    for ant in attendict.keys():
        cdict = {'ant' : ant, 'id':cobsid, 'rmsx': attendict[ant]['rmsx'], 'rmsy': attendict[ant]['rmsy']}
        logger.info("updating rms row for ant {} and recording id {}".format(ant,cobsid))
        mycursor.execute(insertcmd,cdict)
        mydb.commit()

    mycursor.close()
    mydb.close()

