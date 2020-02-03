#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tools to auto tune the PAMs

Created Jan 2020

@author: jkulpa
"""



import sys

from ah import attributes
from . import autotunecommon
from optparse import OptionParser
import numpy
import logging

defaultPowerLeveldBm = 2.0
defaultPowerToldBm = 0.5
defaultRetries = 5

def autotune(antlist,power=defaultPowerLeveldBm,retry=defaultRetries,tolerance=defaultPowerToldBm):
    """
    call to tune the pam settings, adjusting the power going to RF-Fiber converter

    Parameters
    -------------
    antlist : list
        list of antennas to check. should be short string e.g. ['1a','2c']
    power : float
        desired power level in dBm. Default 2 dBm
    retry : int
        maximum number of steps taken to adjust power. default 5
    tolerance : float
        single-sided power level tolerance (i.e. output power will be power+/-tolerance).
        default 0.5 dB
        
    Returns
    -------------
    int
        return code
    list 
        list of not tuned antennas. Antenna is present on the list if one or both polarizations are not set
        
    Raises
    -------------
        KeyError (from autotunecommon.getPolynomials)
    """
    polydict,lowerdict,upperdict,missingants = autotunecommon.getPolynomials(antlist)
    
    notTunedAnts = setPamsAutotune(antlist,polydict,lowerdict,upperdict,power,retry,tolerance)
    
    retval = 0
    if notTunedAnts:
        retval = -1
    
    return retval,notTunedAnts

def setPamsAutotune(antlist,polydict,lowerdict,upperdict,power=defaultPowerLeveldBm,retry=defaultRetries,tol=defaultPowerToldBm):
  
  logger = logging.getLogger(__name__)
  toDoList = list(antlist)
  for itercnt in range(retry):
    #antstr = ",".join(toDoList)
    if not toDoList:
      logger.info("iteration " + str(itercnt) + ": nothing to do" )
      break
    retval,detdict = attributes.get_det(ant=toDoList)
    retval,pamdict = attributes.get_pam(ant=toDoList)
    #retval,detdict = attributes.get_det(ant=antstr)
    #retval,pamdict = attributes.get_pam(ant=antstr)

    for ant in toDoList:
      powerxgot,satx = autotunecommon.getLimittedPower(ant,'x',detdict,upperdict,lowerdict)
      powerygot,saty = autotunecommon.getLimittedPower(ant,'y',detdict,upperdict,lowerdict)

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
        
  #we may as well check only the todoList
  if itercnt == (retry - 1) and toDoList:
    logger.warning("all interation passed ant there are still untuned antennas: %s" % toDoList)

  if logger.getEffectiveLevel() <= logging.INFO:
    #getting det and pam settings for each antenna
    #antstr = ",".join(antlist)
    retval,detdict = attributes.get_det(ant=antlist)
    retval,pamdict = attributes.get_pam(ant=antlist)
    #retval,detdict = attributes.get_det(ant=antstr)
    #retval,pamdict = attributes.get_pam(ant=antstr)
    for ant in antlist:
      powerxgot = 10*numpy.log10(detdict[ant + 'x'])
      powerygot = 10*numpy.log10(detdict[ant + 'y'])
      cpowx = polydict[ant + 'x'](powerxgot)
      cpowy = polydict[ant + 'y'](powerygot)
      logger.info(ant + "x: det " + str( detdict[ant + 'x'] ) + " ( " +str(powerxgot)+ " dBm) translates to " + str(cpowx)+ " dBm pam " + str(pamdict[ant + 'x']) )
      logger.info(ant + "y: det " + str( detdict[ant + 'y'] ) + " ( " +str(powerygot)+ " dBm) translates to " + str(cpowy)+ " dBm pam " + str(pamdict[ant + 'y']) )

  return toDoList

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

    res,failed = autotune(antlist,options.power,options.retry,options.tolerance)

if __name__ == '__main__':
    main()


