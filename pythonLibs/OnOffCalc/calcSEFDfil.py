#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
testing flux functions
Created on Thu Jul 31 2019

@author: wfarah
"""

import OnOffCalc.flux
import OnOffCalc.misc
import numpy
import datetime
import sys
import matplotlib.pyplot as plt
import argparse
from astropy.time import Time
import numpy as np

try:
#    from blimpy.io.fil_reader import FilReader
    from sigpyproc.Readers import FilReader
except ImportError:
    sys.stderr.write("Please install blimpy: pip install blimpy\n")
    sys.exit(-1)


def calcSEFDFils(filon, filoff, source, be_verbose=False):
    """
    Calculates system SEFD based on On-Off data for n consecutive measurements

    averages the measurements (assuming ergodicity)

    Parameters
    ------------
    filon : list
        on-source sigpyproc filterbank objects

    filof : list
        off-source sigpyproc filterbank objects

    source : str
        source name


    Returns
    -------------
    array_like
        SEFD in Jy, for all measurements
    array_like
        SEFD_var in Jy, for all measurements        
    array_like
        time vector for power
    array_like
        power for meas
    list
        list of numpy.array for mask used
        
    """    

    nobs = len(filon)
    freq = filon[0].header.fcenter
    datetime_stamp = Time(filon[0].header.tstart, format='mjd').to_datetime()

    #calculating flux based on the time. If needed, various timestamps may be used
    flx = OnOffCalc.flux.sourceFlux(source, freq, datetime_stamp)
    if be_verbose:
        print("Source flux is: %.2f Jy" %flx)
    
    SEFD = numpy.zeros(nobs, dtype='float')
    SEFD_var = numpy.zeros(nobs,dtype='float')
    powOn = []
    powOff = []
    maskedArrays = []
    flxSEFD = []


    for i in range(nobs):
        data_on = filon[i].readBlock(0, filon[i].header.nsamples)
        data_off = filoff[i].readBlock(0, filon[i].header.nsamples)

        nsamp = min(data_on.shape[1], data_off.shape[1])

        data_on = data_on[:, :nsamp].T
        data_off = data_off[:, :nsamp].T

        SEFD[i], SEFD_var[i], pon, poff, mArray, flxSEFD_s = OnOffCalc.misc.calcSEFD(data_on, 
                data_off, flx, 'MADall')
        powOn.append(pon)
        powOff.append(poff)
        maskedArrays.append(mArray)
        flxSEFD.append(flxSEFD)
    
    return SEFD, SEFD_var, powOn, powOff, maskedArrays, flxSEFD


def main():
    parser = argparse.ArgumentParser(description='Compute SEFD using the '+
            'input filterbank files')
    parser.add_argument('-on', dest='on_files', required=True,
            help = 'on-source filterbank files', nargs='+', type=str)
    parser.add_argument('-off', dest='off_files', required=True,
            help = 'off-source filterbank files', nargs='+', type=str)
    parser.add_argument('-s', dest='source_name', type=str, required=True,
            help = 'source name')
    parser.add_argument('-p', dest='plot', action='store_true',
            help = 'plot on/off power')
    parser.add_argument('-v', dest='verbose', action='store_true',
            help = 'be verbose')

    args = parser.parse_args()

    # make sure we have the same number of filterbank files
    assert len(args.on_files) == len(args.off_files),\
            "Expecting same number of on and off files"

    # prepare to read data
    on_fils = [FilReader(eachFil) for eachFil in args.on_files]
    off_fils = [FilReader(eachFil) for eachFil in args.off_files]

    # some sanity checks
    assert len(set([fil.header.fch1 for fil in on_fils+off_fils])) == 1,\
            "Filterbanks do not have the same start frequency"
    assert len(set([fil.header.bandwidth for fil in on_fils+off_fils])) == 1,\
            "Filterbanks do not have the same bandwidth"
    assert len(set([fil.header.tsamp for fil in on_fils+off_fils])) == 1,\
            "Filterbanks do not have the same sampling time"

    SEFD, SEFD_var, powOn, powOff, maskedArrays, flxSEFD =\
            calcSEFDFils(on_fils, off_fils, args.source_name, args.verbose)
    print ("-"*79)
    print ("SEFD: ", SEFD)
    print ("var: ", SEFD_var)
    print ("-"*79)

    if args.plot:
        for i in range(len(powOn)):
            plt.figure(i)
            plt.plot(powOn[i], label="On")
            plt.plot(powOff[i], label="Off")
            plt.legend()
        plt.show()



if __name__ == "__main__":
    main()
