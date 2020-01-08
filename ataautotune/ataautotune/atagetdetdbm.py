#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
get ata detection (pam) values in dBm

Created Jan 2020

@author: jkulpa
"""



import sys

sys.path.append('/home/obs/bin/')
from ah import attributes
import autotunecommon
from optparse import OptionParser
import numpy
import logging
import re
import pdb

defaultPowerLeveldBm = 2.0
defaultPowerToldBm = 0.5
defaultRetries = 5

def getDetdBm(antlist,polydict,lowerdict,upperdict,missingants):
  
  logger = logging.getLogger(__name__)
  antstr = ",".join(antlist)
  retval,detdict = attributes.get_det(ant=antstr)

  antDD = []

  for ant in antlist:
    powerxgot = 10*numpy.log10(detdict['ant' + ant + 'x'])
    powerygot = 10*numpy.log10(detdict['ant' + ant + 'y'])
    
    wassatx = False
    wassaty = False

    if powerxgot < lowerdict[ant + 'x']:
      powerxgot = lowerdict[ant + 'x']
      wassatx = True
      logger.warning(ant + "x below polynomial limit, adjusting")
    if powerygot < lowerdict[ant + 'y']:
      wassaty = True
      powerygot = lowerdict[ant + 'y']
      logger.info(ant + "y below polynomial limit, adjusting")
    if powerxgot > upperdict[ant + 'x']:
      wassatx = True
      powerxgot = upperdict[ant + 'x']
      logger.info(ant + "x above polynomial limit, adjusting")
    if powerygot > upperdict[ant + 'y']:
      wassaty = True
      powerygot = upperdict[ant + 'y']
      logger.info(ant + "y above polynomial limit, adjusting")

    cpowx = polydict[ant + 'x'](powerxgot)
    cpowy = polydict[ant + 'y'](powerygot)

    ismissing = ant in missingants

    antDD.append({'ant': ant, 'powx': cpowx, 'powy': cpowy, 'satx': wassatx, 'saty': wassaty, 'accurate': not ismissing,'rawx':detdict['ant' + ant + 'x'], 'rawy': detdict['ant' + ant + 'y']})

  return antDD
    

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

    polydict,lowerdict,upperdict,missingants = autotunecommon.getPolynomials(antlist)
    
    resdict = getDetdBm(antlist,polydict,lowerdict,upperdict,missingants)

    fstring = u'ant{ant:s}\t{powx:+1.6f}\t{satx:d}\t\t{rawx:1.6f}\t{powy:+1.6f}\t{saty:d}\t\t{rawy:1.6f}\t{accurate:d}'
    print("antenna\tx pol [dBm]\tsat flag x\tx pol raw\ty pol [dBm]\tsat flag y\ty pol raw\twas measured")
    for row in resdict:
        print(fstring.format(**row))

if __name__ == '__main__':
    main()


