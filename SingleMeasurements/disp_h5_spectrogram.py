#!/usr/bin/env python3

import sys
import logging
import time
from optparse import OptionParser

from ATATools import logger_defaults,ata_positions
from ATAobs import obs_h5
import pyuvdata
import OnOffCalc.misc
from astropy.time import Time
from pkg_resources import parse_version
import numpy
import matplotlib.pyplot as plt

def main():

    # Define the argumants
    parser = OptionParser(usage= 'Usage %prog [options] filename',
            description='Plot the waterfall plot from the file')

    #parser.add_argument('hosts', type=str, help = hostnamesHelpString)
    parser.add_option('-f', dest='flags', action="store_true", default=False,
                        help ='Use flags for displaying')
    parser.add_option('-v', '--verbose', dest='verbose', action="store_true", default=False,
                        help ="More on-screen information")
    parser.add_option('-p', '--pass-band', dest='do_passband', action="store_true", default=False,
                        help ="Plot only the passband data")
    parser.add_option('-u', '--utc', dest='do_utc', action="store_true", default=False,
                        help ="convert time to UTC")
    parser.add_option('--db', dest='do_db', action="store_true", default=False,
                        help ="plot in logarithmic scale")

    (options,args) = parser.parse_args()

    if(options.verbose):
        logger = logger_defaults.getProgramLogger("SNAP_OBS",loglevel=logging.INFO)
    else:
        logger = logger_defaults.getProgramLogger("SNAP_OBS",loglevel=logging.WARNING)

    if len(args) != 1:
        logger.warning("need file name")
        parser.print_help()
        sys.exit(1)

    use_flags = options.flags
    use_passband = options.do_passband
    use_utc = options.do_utc
    db_scale = options.do_db
    filename = args[0]
    
    plotWaterfalls(filename, db_scale, use_flags, use_passband, use_utc)

    exit()

def plotWaterfalls(filename, db_scale=True, use_flags=True, use_passband=False, use_utc=False):
    logger = logger_defaults.getModuleLogger(__name__)

    UV = pyuvdata.UVData()
    UV.read_uvh5(filename)
    if (not obs_h5.checkIfWaterfall(UV)):
        logger.error("file {} does not contain waterfall data".format(filename))

    if use_passband:
        freqvec = OnOffCalc.misc.getDatarange(UV.Nfreqs)
    else:
        freqvec = numpy.array(range(UV.Nfreqs))

    freq_mhz = UV.freq_array[0,freqvec]/1e6

    if use_utc:
        if parse_version(UV.extra_keywords['ata_version']) <= parse_version('0.2'):
            #MJD
            tt=Time(UV.time_array,format='mjd')
        else:
            #JD
            tt=Time(UV.time_array,format='jd')
        timevec = tt.unix
        tlab = 'time (utc) [s]'
    else:
        timevec = UV.time_array
        if parse_version(UV.extra_keywords['ata_version']) <= parse_version('0.2'):
            tlab = 'Time (mjd)'
        else:
            tlab = 'Time (jd)'

    if db_scale:
        dbstr = '(dB)'
        dtoplotx = 10*numpy.log10(UV.data_array[:,0,freqvec,0].real.copy())
        dtoploty = 10*numpy.log10(UV.data_array[:,0,freqvec,1].real.copy())
    else:
        dbstr = '(lin)'
        dtoplotx = UV.data_array[:,0,freqvec,0].real.copy()
        dtoploty = UV.data_array[:,0,freqvec,1].real.copy()
    
    if use_flags:
        dflgx = UV.flag_array[:,0,freqvec,0]
        dflgy = UV.flag_array[:,0,freqvec,1]
        dtoplotx[dflgx] = numpy.nan
        dtoploty[dflgy] = numpy.nan

    antstr = UV.antenna_names[UV.ant_1_array[0]]
    
    ldata = UV.extra_keywords['lfft_of0']
    for ii  in range(ldata):
        xxval = UV.extra_keywords['fft_of0_{}'.format(ii)]
        if xxval:
            logger.warning('fft_of0[{}] nonzero'.format(ii))
    ldata = UV.extra_keywords['lfft_of1']
    for ii  in range(ldata):
        xxval = UV.extra_keywords['fft_of1_{}'.format(ii)]
        if xxval:
            logger.warning('fft_of1[{}] nonzero'.format(ii))
    ldata = UV.extra_keywords['lauto0_of_count']
    for ii  in range(ldata):
        xxval = UV.extra_keywords['auto0_of_count_{}'.format(ii)]
        if xxval:
            logger.warning('auto0_of_count[{}] nonzero'.format(ii))
    ldata = UV.extra_keywords['lauto1_of_count']
    for ii  in range(ldata):
        xxval = UV.extra_keywords['auto1_of_count_{}'.format(ii)]
        if xxval:
            logger.warning('auto1_of_count[{}] nonzero'.format(ii))


    dataExtent = [freq_mhz[0],freq_mhz[-1],len(timevec)-1,0]
    #fig, ax = plt.subplots(1,3,sharey=True)
    fig, ax = plt.subplots(1,2,sharey=True)
    mp1=ax[0].imshow(dtoplotx,aspect='auto', interpolation='none', extent=dataExtent)
    mp2=ax[1].imshow(dtoploty,aspect='auto', interpolation='none', extent=dataExtent)
    ax[0].set_xlabel('freq [MHz]')
    ax[1].set_xlabel('freq [MHz]')
    ax[0].set_ylabel('snap no')
    ax[1].set_ylabel('snap no')
    ax[0].set_title(antstr + ' X pol' + dbstr)
    ax[1].set_title(antstr + ' Y pol' + dbstr)
    fig.colorbar(mp1,ax=ax[0])
    fig.colorbar(mp2,ax=ax[1])
    #ax[2].plot(timevec,range(len(timevec)))
    #ax[2].set_ylabel('snap no')
    #ax[2].set_xlabel(tlab)
    plt.show()
    
    #import pdb
    #pdb.set_trace()
    plt.plot(range(len(timevec)-1),numpy.diff(timevec))
    plt.title('Difference of ' +tlab +'between each data snap' )
    plt.show()

if __name__== "__main__":
    main()

