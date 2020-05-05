#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tools to auto tune the PAMs

Created Jan 2020

@author: jkulpa
"""



import sys

from ah import attributes
import autotunecommon
from optparse import OptionParser
import numpy
import logging

defaultPowerLeveldBm = 0.0
defaultPowerToldBm = 0.5
defaultRetries = 5
satTestUpperPower = -12
detdict_upper_sat = 0.4
detdict_upper_sat_pam_val = 30

def autotune_multiprocess(antlist,power=defaultPowerLeveldBm,retry=defaultRetries,tolerance=defaultPowerToldBm):
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

    import concurrent.futures

    polydict,lowerdict,upperdict,missingants = autotunecommon.getPolynomials(antlist)
    
    nworkers = len(antlist)
    notTunedAnts = []

    with concurrent.futures.ProcessPoolExecutor(max_workers=nworkers) as executor:
    #with concurrent.futures.ThreadPoolExecutor(max_workers=nworkers) as executor:
        tlist = []
        for cant in antlist:
            #it seems that this should be submit(autotune,[cant],polydict,lowerdict,upperdict,power,retry,tolerance)
            t = executor.submit([cant],polydict,lowerdict,upperdict,power,retry,tolerance)
            tlist.append(t)

        for t in tlist:
            retlist = t.result()
            print(retlist)
            notTunedAnts.extend(retlist)
    
    print(notTunedAnts)
    retval = 0
    if notTunedAnts:
        retval = -1
    
    return retval,notTunedAnts

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
  if power < autotunecommon.minpowerinspect + tol:
    logger.error('settings error target power {} < min power check {} + tolerance {}'.format(power, autotunecommon.minpowerinspect, tol))
  toDoList = list(antlist)
  brokenList = []
  satPolList = []
  brokenPolList = []
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
      #in first iteration we may experiance saturation already
      if itercnt == 0:
        needredo=False
        newpamx = pamdict[ant + 'x']
        newpamy = pamdict[ant + 'y']
        if (satx and (detdict[ant + 'x'] > detdict_upper_sat ) ):
            #saturation on upper X, need to push pams down
            newpamx = detdict_upper_sat_pam_val
            needredo=True
        if (saty and (detdict[ant + 'y'] > detdict_upper_sat ) ):
            #saturation on upper X, need to push pams down
            newpamy = detdict_upper_sat_pam_val
            needredo=True
        if needredo:
            attributes.set_pam(ant=ant,x=newpamx,y=newpamy)
            retval,tmpdetdict = attributes.get_det(ant=ant)
            powerxgot,satx = autotunecommon.getLimittedPower(ant,'x',tmpdetdict,upperdict,lowerdict)
            powerygot,saty = autotunecommon.getLimittedPower(ant,'y',tmpdetdict,upperdict,lowerdict)
            pamdict[ant + 'x'] = newpamx
            pamdict[ant + 'y'] = newpamy


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
      elif numpy.abs(deltax) < tol and ((ant + 'y') in brokenPolList):
        toDoList.remove(ant)
        logger.info("tuned " + ant + "x in " + str(itercnt) + " iteration. y seems to have broken detector" )
      elif numpy.abs(deltay) < tol and ((ant + 'x') in brokenPolList):
        toDoList.remove(ant)
        logger.info("tuned " + ant + "y in " + str(itercnt) + " iteration. x seems to have broken detector" )
      else:
        #we still need to fix it a bit. We are applying the 0.9 multiplier to limit oscilations
        #of +/- delta
        xwasbelow=False
        ywasbelow=False
        newpamx = pamdict[ant + 'x'] - 0.9 * deltax
        newpamy = pamdict[ant + 'y'] - 0.9 * deltay
        newpamx = autotunecommon.round_five(newpamx)
        newpamy = autotunecommon.round_five(newpamy)
            
        #if det value was low and it's first iteration, we limit the change to cap and mark for check
        if cpowx < autotunecommon.minpowerinspect and itercnt == 0:
            newpamx = max(autotunecommon.minfirstiterattenuator,min(newpamx,autotunecommon.maxattenuator))
            xwasbelow=True
        else:
            newpamx = max(autotunecommon.minattenuator,min(newpamx,autotunecommon.maxattenuator))

        if cpowy < autotunecommon.minpowerinspect and itercnt == 0:
            newpamy = max(autotunecommon.minfirstiterattenuator,min(newpamy,autotunecommon.maxattenuator))
            ywasbelow=True
        else:
            newpamy = max(autotunecommon.minattenuator,min(newpamy,autotunecommon.maxattenuator))

        
        if ant + 'x' in brokenPolList:
            newpamx = newpamy

        if ant + 'y' in brokenPolList:
            newpamy = newpamx

        #saturated on the upper limit, adding to sat list and broken list
        if satx and cpowx > satTestUpperPower:
            logger.warning('antpol {}x saturated on upper limit'.format(ant))
            satPolList.append(ant+'x')
            brokenPolList.append(ant+'x')

        if saty and cpowy > satTestUpperPower:
            logger.warning('antpol {}y saturated on upper limit'.format(ant))
            satPolList.append(ant+'y')
            brokenPolList.append(ant+'y')

        if ant + 'x' in satPolList:
            newpamx = pamdict[ant + 'x']

        if ant + 'y' in satPolList:
            newpamy = pamdict[ant + 'y']

        logger.info('setting pams {0:s} to {1:.2f},{2:.2f}'.format(ant,newpamx,newpamy))
        attributes.set_pam(ant=ant,x=newpamx,y=newpamy)

        if xwasbelow or ywasbelow:
            #we had low value, need to recalculate and see if we have any broken pams
            retval,temp_detdict = attributes.get_det(ant=ant)
            if xwasbelow:
                powerxgot,satx = autotunecommon.getLimittedPower(ant,'x',temp_detdict,upperdict,lowerdict)
                tmp_cpowx = polydict[ant + 'x'](powerxgot)
                if tmp_cpowx < autotunecommon.minpowerinspect:
                    logger.warning('antpol {}x appear to have a broken detector'.format(ant))
                    brokenPolList.append(ant+'x')
                    logger.info("setting both pams to {}".format(newpamy))
                    attributes.set_pam(ant=ant,x=newpamy,y=newpamy)
            if ywasbelow:
                powerygot,saty = autotunecommon.getLimittedPower(ant,'y',temp_detdict,upperdict,lowerdict)
                tmp_cpowy = polydict[ant + 'y'](powerygot)
                if tmp_cpowy < autotunecommon.minpowerinspect:
                    logger.warning('antpol {}y appear to have a broken detector'.format(ant))
                    brokenPolList.append(ant+'y')
                    logger.info("setting both pams to {}".format(newpamx))
                    attributes.set_pam(ant=ant,x=newpamx,y=newpamx)

        #both polarizations have broken detector!
        #removing antenna from toDoList and putting it to broken list
        #also, setting a default value
        if ((ant + 'x') in brokenPolList) and ((ant + 'y' in brokenPolList)):
            logger.warning('ant {} has broken detector in both polarizations'.format(ant) )
            brokenList.append(ant)
            toDoList.remove(ant)
            attributes.set_pam(ant=ant,source='default')

        
  #we may as well check only the todoList
  if itercnt == (retry - 1) and toDoList:
    logger.warning("all interation passed ant there are still untuned antennas: %s" % toDoList)
    #checking if the detector is broken 

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
      logger.info(ant + "x: det " + str( detdict[ant + 'x'] ) + " ( " +str(powerxgot)+ " dB) translates to " + str(cpowx)+ " dBm pam " + str(pamdict[ant + 'x']) )
      logger.info(ant + "y: det " + str( detdict[ant + 'y'] ) + " ( " +str(powerygot)+ " dB) translates to " + str(cpowy)+ " dBm pam " + str(pamdict[ant + 'y']) )

  if brokenList:
      logger.warning('the broken antenna list is {}'.format(','.join(brokenList)))
  toDoList.extend(brokenList)
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
    #res,failed = autotune_multiprocess(antlist,options.power,options.retry,options.tolerance)
    

if __name__ == '__main__':
    main()


