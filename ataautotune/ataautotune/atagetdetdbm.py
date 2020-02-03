#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
get ata detection (pam) values in dBm

Created Jan 2020

@author: jkulpa
"""



import sys

from ah import attributes
from . import autotunecommon
from optparse import OptionParser
import numpy
import logging
import re
import pdb

def getDetdBm_dict(antlist,polydict,lowerdict,upperdict,missingants):
  
  logger = logging.getLogger(__name__)
  #antstr = ",".join(antlist)
  #retval,detdict = attributes.get_det(ant=antstr)
  retval,detdict = attributes.get_det(ant=antlist)

  antDD = []

  for ant in antlist:
    powerxgot,wassatx = autotunecommon.getLimittedPower(ant,'x',detdict,upperdict,lowerdict)
    powerygot,wassaty = autotunecommon.getLimittedPower(ant,'y',detdict,upperdict,lowerdict)
    
    cpowx = polydict[ant + 'x'](powerxgot)
    cpowy = polydict[ant + 'y'](powerygot)

    ismissing = ant in missingants

    antDD.append({'ant': ant, 'powx': cpowx, 'powy': cpowy, 'satx': wassatx, 'saty': wassaty, 'accurate': not ismissing,'rawx':detdict[ant + 'x'], 'rawy': detdict[ant + 'y']})

  return antDD
    

def getDetdBm(antlist):
    """
    Calculated power of the PAX box detector in dBm based on polynomial approximation.

    Parameters
    -------------
    antlist : list
        list of antennas to check. should be short string e.g. ['1a','2c']
        
    Returns
    -------------
    int
        return code
    list dict
        list of dictionaries for each antenna. Dictionary includes power (x and y), raw values, polynomial saturation flag and information if antenna was measured
        
    Raises
    -------------
           KeyError (from autotunecommon.getPolynomials)
    """
    polydict,lowerdict,upperdict,missingants = autotunecommon.getPolynomials(antlist)
    
    resdict = getDetdBm_dict(antlist,polydict,lowerdict,upperdict,missingants)
    
    return (0,resdict)

def main():

    logger = logging.getLogger('atagetdetdbm')
    FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'


    usage = "Usage %prog [options] comma_separated_ant_names"
    parser = OptionParser(usage=usage)
    parser.add_option("-v", "--verbose",
                action="store_true", dest="verbose", default=False,
                help="prints additional information")

    (options, args) = parser.parse_args()

    if(options.verbose):
        logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
    else:
        logging.basicConfig(level=logging.WARNING, format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')

    if len(args) < 1:
        logger.warning("no antenna string provided")
        parser.print_help()
        sys.exit(1)

    antstr,antlist = autotunecommon.getAntennas(args[0])

    retval,resdict = getDetdBm(antlist)

    fstring = u'ant{ant:s}\t{powx:+1.6f}\t{satx:d}\t\t{rawx:1.6f}\t{powy:+1.6f}\t{saty:d}\t\t{rawy:1.6f}\t{accurate:d}'
    print("antenna\tx pol [dBm]\tsat flag x\tx pol raw\ty pol [dBm]\tsat flag y\ty pol raw\twas measured")
    for row in resdict:
        print(fstring.format(**row))

if __name__ == '__main__':
    main()


