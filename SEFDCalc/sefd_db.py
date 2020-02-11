#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
calculations of H5 on-off measurement sets for SEFD

Created Feb 2020

@author: jkulpa
"""

from ATATools import logger_defaults
import ATASQL
import mysql.connector

def insertSEFD(ant,freq,setid,method,ts,sefdx,sefdx_var,sefdy,sefdy_var):


    logger= logger_defaults.getModuleLogger(__name__)
    mydb = ATASQL.connectGoogleRW()
    mycursor = mydb.cursor()

    dict1 = {'ant':ant,'freq':freq,'setid':setid,'method':method,'ts':ts,
            'sefdx':sefdx,'sefdx_var':sefdx_var,
            'sefdy':sefdy,'sefdy_var':sefdy_var }

    insertcmd = ("insert into sefd_meas set ant=%(ant)s, freq=%(freq)s, setid=%(setid)s, "
                 "method=%(method)s, meastime=%(ts)s, "
                 "sefdx=%(sefdx)s, sefdx_var=%(sefdx_var)s, "
                 "sefdy=%(sefdy)s, sefdy_var=%(sefdy_var)s")

    logger.info("adding input for antenna {} and freq {}".format(ant,freq))

    updatecmd = ("update sefd_meas set "
                 "sefdx=%(sefdx)s, sefdx_var=%(sefdx_var)s, "
                 "sefdy=%(sefdy)s, sefdy_var=%(sefdy_var)s "
                 "where ant=%(ant)s and freq=%(freq)s and setid=%(setid)s and "
                 "method=%(method)s and meastime=%(ts)s ")

    try:
        mycursor.execute(insertcmd,dict1)
        mydb.commit()
    except mysql.connector.errors.IntegrityError:
        #duplicate entry?
        logger.warning("entry for ant {} freq {} exist. updating...".format(ant,freq))
        mycursor.execute(updatecmd,dict1)
        mydb.commit()

    mycursor.close()
    mydb.close()


