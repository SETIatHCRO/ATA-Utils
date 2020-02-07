#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tools to auto tune the PAMs

Created Jan 2020

@author: jkulpa
"""



import sys

import numpy
import logging
import re
import ATASQL
from mysql.connector import Error 

#the minimal attenuator value that can be set
minattenuator = 0.0
#the minimal attenuator value than can be set if the initial detected power is low
minfirstiterattenuator = 10.0
#if the power is lower than that, we set min attenuator to minfirstiterattenuator and need to check the output power
minpowerinspect = -15.0 
maxattenuator = 63.0
defaultPax = 'PB-000'
validAntennas = ['1a','1b','1c','1d','1e','1f', '1g', '1h', '1j', '1k', '2a', '2b',
                 '2c', '2d', '2e', '2f', '2g', '2h', '2j', '2k', '2l', '2m', '3c',
                 '3d', '3e', '3f', '3g', '3h', '3j', '3l', '4e', '4f', '4g', '4h',
                 '4j', '4k', '4l', '5b', '5c', '5e', '5g', '5h']

def round_twentyfive(num):
    return round(num*4.0)*0.25

def round_five(num):
        return round(num*2.0)*0.5


def getLimittedPower(ant,pol,detdict,upperdict,lowerdict):
    powergot = 10*numpy.log10(detdict[ant + pol])

    logger = logging.getLogger(__name__)

    wassat = False
    if powergot < lowerdict[ant + pol]:
        powergot = lowerdict[ant + pol]
        wassat = True
        logger.info(ant + pol + " below polynomial limit, adjusting")
    if powergot > upperdict[ant + pol]:
        powergot = upperdict[ant + pol]
        wassat = True
        logger.info(ant + pol + " above polynomial limit, adjusting")

    return powergot,wassat

def getPolynomials(alist):
    """
    Function return 
    
    input: alist - list of antennas. must in short format, i.e. ['1a','1b']
    returns: antpol dictionary of polynomials, lower and upper bound 
    """
    
    
    logger = logging.getLogger(__name__)
    logger.info("connecting to database")
    
    mydb = ATASQL.connectATAROnly()
    cursor = mydb.cursor()
    
    queryPart = ("select feed_parts.ant,pbmeas.pax_box_sn,pbmeas.pol,pbmeas.iscoherent,pbmeas.lowdet,pbmeas.highdet,pbmeas.p0,pbmeas.p1,pbmeas.p2,pbmeas.p3,pbmeas.p4,pbmeas.p5 "
                 "from (pbmeas inner join feed_parts on pbmeas.pax_box_sn = feed_parts.pax_box_sn) where pbmeas.type='cw' "
                 "and feed_parts.ant in (%s);")
    
    in_p=', '.join(['%s'] * len(alist)) 
    #in_p=', '.join(map(lambda x: '%s', alist))
    query = queryPart % in_p;
    cursor.execute(query, alist)
    
    #getting the values from the database. Only measured antennas would be returned here
    antennasgot = {}
    polydict={}
    lowerdict = {}
    upperdict = {}
    for (ant,sn,pol,isc,low,high,p0,p1,p2,p3,p4,p5) in cursor:
        antennasgot[ant] = 1
        antpol = ant + pol;
        polydict[antpol] = numpy.poly1d([p5,p4,p3,p2,p1,p0]);
        lowerdict[antpol] = low;
        upperdict[antpol] = high;
        if not isc:
          logger.warning("antenna's " + ant + pol + " pambox is marked for uncertain measurement")
    
    #checking if both polarizations are there. 
    for ant in antennasgot:
        if not ant + 'x' in polydict or not ant + 'y' in polydict:
            logger.warning("missing polarization for "  + ant)
            raise KeyError("missing polarization for "  + ant)
            
    #we need to see if we have all data gathered
    missingAnts = list(set(alist) - set(antennasgot))
    
    if missingAnts:
        logger.info("we are missing following antennas %s" % missingAnts)
        #we have some missing ants. lets check if we have already downloaded the default Antenna
        logger.info("no default antenna in the set, quering default pax {}".format(defaultPax))
        #next querry to get default antenna data
        query = ("select pax_box_sn,pol,iscoherent,lowdet,highdet,p0,p1,p2,p3,p4,p5 "
                 "from pbmeas where type='cw' and pax_box_sn = %(defpax)s")
        dict1={'defpax':defaultPax}
        cursor.execute(query, dict1)
        defaultdictpoly = {}
        defaultdictlower = {}
        defaultdictupper = {}
        for (sn,pol,isc,low,high,p0,p1,p2,p3,p4,p5) in cursor:
            defaultdictpoly[pol] = numpy.poly1d([p5,p4,p3,p2,p1,p0]);
            defaultdictlower[pol] = low;
            defaultdictupper[pol] = high;
           
        #do we have both polarization of default one?
        if not 'x' in defaultdictpoly or not 'y' in defaultdictpoly:
            logger.warning("missing polarization for "  + defaultPax)
            raise KeyError("missing polarization for "  + defaultPax)
                
        #now we have a new dictionary, we may fill the remaining parts
        for ant in missingAnts:
            polydict[ant + 'x'] = defaultdictpoly['x'] 
            lowerdict[ant + 'x'] = defaultdictlower['x']
            upperdict[ant + 'x'] = defaultdictupper['x']
            polydict[ant + 'y'] = defaultdictpoly['y'] 
            lowerdict[ant + 'y'] = defaultdictlower['y']
            upperdict[ant + 'y'] = defaultdictupper['y']
            
    return polydict,lowerdict,upperdict,missingAnts;
    

#select feed_parts.ant,pbmeas.pax_box_sn,pbmeas.pol,pbmeas.iscoherent,pbmeas.lowdet,pbmeas.highdet,pbmeas.p0,pbmeas.p1,pbmeas.p2,pbmeas.p3,pbmeas.p4,pbmeas.p5 from (pbmeas inner join feed_parts on pbmeas.pax_box_sn = feed_parts.pax_box_sn) where pbmeas.type='cw' and feed_parts.ant in ('3c');

def checkIfValidAntenna(antennalist):
    for ant in antennalist:
        if ant not in validAntennas:
            logger = logging.getLogger(__name__)
            logger.warning('Antenna ' + ant + ' is not a valid antenna name')
            raise KeyError('Antenna ' + ant + ' is not a valid antenna name')

def cleanAntennaString(antstring):
    antstringout = re.sub(r'ant', '', antstring)
    #print(antstring)
    #print(antstringout)
    return antstringout

def splitAntennaString(antstring):
    antenna = antstring.split(',')
    checkIfValidAntenna(antenna)
    return antenna


def getAntennas(arg):
  """
  clear and uniform the antenna string. check if antenna exist. 
  
  Parameters
  -------------
  arg : str
      comma separated list of antenna names, both long and short may be mixed
        
  Returns
  -------------
  str
      string of short antenna names
  list 
      list of short antenna names
        
  Raises
  -------------
      KeyError (antenna not on the list)
  """
  antstr = cleanAntennaString(arg);
  antlist = splitAntennaString(antstr);
  return antstr,antlist




