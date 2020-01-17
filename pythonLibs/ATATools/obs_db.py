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
        int
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


