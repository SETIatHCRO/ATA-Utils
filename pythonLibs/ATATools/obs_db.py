#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
operations on observator (obs) database

Created Jan 2020

@author: jkulpa
"""

import logging
from  ATASQL import connect

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

    logger = logging.getLogger(__name__)
    FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'
    logging.basicConfig(format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')

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

    logger = logging.getLogger(__name__)
    FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'
    logging.basicConfig(format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')

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


