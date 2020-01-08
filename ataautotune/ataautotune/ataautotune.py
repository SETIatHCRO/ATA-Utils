#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tools to auto tune the PAMs

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

def setPamsAutotune(antlist,polydict,lowerdict,upperdict,power=defaultPowerLeveldBm,retry=defaultRetries,tol=defaultPowerToldBm):
  
  logger = logging.getLogger(__name__)
  toDoList = list(antlist)
  for itercnt in range(retry):
    antstr = ",".join(toDoList)
    if not toDoList:
      logger.info("iteration " + str(itercnt) + ": nothing to do" )
      break
    retval,detdict = attributes.get_det(ant=antstr)
    retval,pamdict = attributes.get_pam(ant=antstr)

    for ant in toDoList:
      powerxgot = 10*numpy.log10(detdict['ant' + ant + 'x'])
      powerygot = 10*numpy.log10(detdict['ant' + ant + 'y'])
      
      if powerxgot < lowerdict[ant + 'x']:
        powerxgot = lowerdict[ant + 'x']
        logger.info(ant + "x below polynomial limit, adjusting")
      if powerygot < lowerdict[ant + 'y']:
        powerygot = lowerdict[ant + 'y']
        logger.info(ant + "y below polynomial limit, adjusting")
      if powerxgot > upperdict[ant + 'x']:
        powerxgot = upperdict[ant + 'x']
        logger.info(ant + "x above polynomial limit, adjusting")
      if powerygot > upperdict[ant + 'y']:
        powerygot = upperdict[ant + 'y']
        logger.info(ant + "y above polynomial limit, adjusting")

      cpowx = polydict[ant + 'x'](powerxgot)
      cpowy = polydict[ant + 'y'](powerygot)

      deltax = power - cpowx
      deltay = power - cpowy

      logger.info("antenna " + ant + "x: det " + str(powerxgot) + " polval " + str(cpowx) + " delta " + str(deltax))
      logger.info("antenna " + ant + "y: det " + str(powerygot) + " polval " + str(cpowy) + " delta " + str(deltay))

      if numpy.abs(deltax) < tol and numpy.abs(deltay) < tol:
        #we may remove the antenna from the todolist.
        toDoList.remove(ant)
        logger.info("tuned " + ant + " in " + str(itercnt) + " iteration" )
      else:
        #we still need to fix it a bit. We are applying the 0.9 multiplier to limit oscilations
        #of +/- delta

        newpamx = pamdict[ant + 'x'] - 0.9 * deltax
        newpamy = pamdict[ant + 'y'] - 0.9 * deltay
        attributes.set_pam(ant=ant,x=newpamx,y=newpamy)
        

  if itercnt == (retry - 1) and toDoList:
    logger.warning("all interation passed ant there are still untuned antennas: %s" % toDoList)

  if logger.getEffectiveLevel() <= logging.INFO:
    #getting det and pam settings for each antenna
    antstr = ",".join(antlist)
    retval,detdict = attributes.get_det(ant=antstr)
    retval,pamdict = attributes.get_pam(ant=antstr)
    for ant in antlist:
      powerxgot = 10*numpy.log10(detdict['ant' + ant + 'x'])
      powerygot = 10*numpy.log10(detdict['ant' + ant + 'y'])
      cpowx = polydict[ant + 'x'](powerxgot)
      cpowy = polydict[ant + 'y'](powerygot)
      logger.info(ant + "x: det " + str( detdict['ant' + ant + 'x'] ) + " ( " +str(powerxgot)+ " dBm) translates to " + str(cpowx)+ " dBm pam " + str(pamdict[ant + 'x']) )
      logger.info(ant + "y: det " + str( detdict['ant' + ant + 'y'] ) + " ( " +str(powerygot)+ " dBm) translates to " + str(cpowy)+ " dBm pam " + str(pamdict[ant + 'y']) )

def main():

    logger = logging.getLogger('ataautotune')
    FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'


    usage = "Usage %prog [options] comma_separated_ant_names"
    parser = OptionParser(usage=usage)
    parser.add_option("-p","--power", action="store", type="float",
                    dest="power", default=defaultPowerLeveldBm,
                    help="autotune target power in dBm")
    parser.add_option("-r","--retry", action="store", type="int",
                    dest="retry", default=defaultRetries,
                    help="number of autotune steps")
    parser.add_option("-t","--tolerance", action="store", type="float",
                    dest="tolerance", default=defaultPowerToldBm,
                    help="tolerance goal in dBm")
    parser.add_option("-v", "--verbose",
                action="store_true", dest="verbose", default=False,
                help="prints additional information")

    (options, args) = parser.parse_args()

    if(options.verbose):
        logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
    else:
        logging.basicConfig(level=logging.WARNING, format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')

    trgPow = options.power;

    if len(args) < 1:
        logger.warning("no antenna string provided")
        parser.print_help()
        sys.exit(1)

    logger.info("starting with antenna string (%s). Target power %f" % (args[0],trgPow))
    
    antstr,antlist = autotunecommon.getAntennas(args[0])

    polydict,lowerdict,upperdict,missingants = autotunecommon.getPolynomials(antlist)
    
    setPamsAutotune(antlist,polydict,lowerdict,upperdict,options.power,options.retry,options.tolerance)

if __name__ == '__main__':
    main()


