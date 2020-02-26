#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import casperfpga
import adc5g

import time
import numpy as np
import struct
from ATATools import ata_control,logger_defaults
from . import snap_defaults 
import logging

def setSnapRMS(host,ant,fpga_file,rms=snap_defaults.rms,srate=snap_defaults.srate):
    snap = getSnap(host,fpga_file)
    fpga_clk = syncFpgaClock(snap,srate)
    retdict = setRMS(snap,ant,rms)
    return retdict

def getSnapRMS(host,ant,fpga_file,srate=snap_defaults.srate):
    snap = getSnap(host,fpga_file)
    fpga_clk = syncFpgaClock(snap,srate)
    rms = getRMS(snap,ant)
    return {'ant':ant,'rms':rms}

def getSnap(host, fpga_file):
    #snap = casperfpga.CasperFpga(host,transport=casperfpga.transport_tapcp.TapcpTransport)
    #we are silently omiting the logs from this call
    logger = logging.getLogger('tornado')
    logger.setLevel(logging.CRITICAL)
    snap = casperfpga.CasperFpga(host)
    snap.get_system_information(fpga_file)
    return snap

def syncFpgaClock(snap,srate=snap_defaults.srate):
    logger = logger_defaults.getModuleLogger(__name__)

    acc_len = float(snap.read_int('timebase_sync_period') / (4096 / 4))
    fpga_clk = snap.estimate_fpga_clock()
    
    logger.info('snap clock estimated at {}'.format(fpga_clk))

    logger.info( "srate = {0:.1f}".format(srate))

    check_clock = np.abs((fpga_clk*4. / srate) - 1) < 0.01

    # If bad clock, try several more times
    num_check = 0
    while(check_clock == False and num_check < snap_defaults.clock_attempts):
        num_check = num_check + 1
        time.sleep(1)
        logger.info( "Estimating FPGA clock retry {}".format(num_check))
        fpga_clk = snap.estimate_fpga_clock()
        logger.info( "Clock estimate is {0:.1f}, try {1:d}".format(fpga_clk, num_check))
        check_clock = np.abs((fpga_clk*4. / srate) - 1) < 0.01

    #If still bad clock, fail
    if(check_clock == False):
        errormsg = "unable to set up FPGA clock ({})".format(fpga_clk)
        logger.error(errormsg)
        raise RuntimeError(errormsg)

    return fpga_clk

def getRMS(snap,ant):
    logger = logger_defaults.getModuleLogger(__name__)
    num_snaps = 5
    chani = []
    chanq = []
    for i in range(num_snaps):
        all_chan_data = adc5g.get_snapshot(snap, 'ss_adc')
        chani += [all_chan_data[0::2][0::2]]
        chanq += [all_chan_data[1::2][0::2]]
    chani = np.array(chani)
    chanq = np.array(chanq)

    meas_stdx = chani.std()
    meas_stdy = chanq.std()
    retdict = {'rmsx': meas_stdx,'rmsy': meas_stdy, 'ant': ant}

    logger.info("{0!s}x: Channel I ADC mean/std-dev: {1:.2f} / {2:.2f}".format(ant, chani.mean(), meas_stdx))
    logger.info("{0!s}y: Channel Q ADC mean/std-dev: {1:.2f} / {2:.2f}".format(ant, chanq.mean(), meas_stdy))
    return retdict

def setRMS(snap,ant,rms=snap_defaults.rms):
    logger = logger_defaults.getModuleLogger(__name__)
    
    logger.info("Trying to tune power levels of {0!s} to RMS: {1:.2f}".format(ant, rms))
    
    assert (isinstance(ant,str) and len(ant) == 2),"ant has to be a short ant string" 

    num_snaps = 5

    atteni = 20.0
    attenq = 20.0

    retdict = {'ant':ant,'attenx' : 0, 'atteny':0, 'rmsx':0, 'rmsy':0}

    antpol_list = [ant + 'x',ant + 'y']
    for attempt in range(snap_defaults.rms_attempts):
        db_list = [atteni, attenq]

        answer = ata_control.set_atten(antpol_list, db_list)
        #if there is no attenuator, then attempt to adject the PAMs
        if "no attenuator for" in answer:
            errormsg = "no attenuator found for antpols: {}".format(','.join(antpol_list))
            logger.error(errormsg)
            raise RuntimeError(errormsg)

        retdict['attenx'] = atteni
        retdict['atteny'] = attenq

        chani = []
        chanq = []
        for i in range(num_snaps):
            all_chan_data = adc5g.get_snapshot(snap, 'ss_adc')
            chani += [all_chan_data[0::2][0::2]]
            chanq += [all_chan_data[1::2][0::2]]
        chani = np.array(chani)
        chanq = np.array(chanq)

        meas_stdx = chani.std()
        meas_stdy = chanq.std()
        retdict['rmsx'] = meas_stdx
        retdict['rmsy'] = meas_stdy

        delta_atteni = 20*np.log10(meas_stdx / rms)
        delta_attenq = 20*np.log10(meas_stdy / rms)
        
        logger.info("{0!s}x: Channel I ADC mean/std-dev/deltai: {1:.2f} / {2:.2f}, delta={3:.2f}".format(ant,
                    chani.mean(), meas_stdx, delta_atteni))
        logger.info("{0!s}y: Channel Q ADC mean/std-dev/deltai: {1:.2f} / {2:.2f}, delta={3:.2f}".format(ant,
                    chanq.mean(), meas_stdy, delta_attenq))
        
        if (np.abs(delta_atteni) < 1) and (np.abs(delta_attenq) < 1):
            logger.info( "Tuning complete for {}".format(ant))
            return retdict

        else:
            # Attenuator has 0.25dB precision
            atteni = int(4 * (atteni + delta_atteni)) / 4.0
            attenq = int(4 * (attenq + delta_attenq)) / 4.0
            if atteni > 30:
                atteni = 30
            if attenq > 30:
                attenq = 30
            if atteni < 0:
                atteni = 0
            if attenq < 0:
                attenq = 0

    logger.warning("RMS requirement for {} not met. got I: {}, Q: {} target: {}".format(ant,meas_stdx,meas_stdy,rms))
    return retdict

def getData(host,ant,ncaptures,fpga_file,freq,srate=snap_defaults.srate,ifc=snap_defaults.ifc):
    snap = getSnap(host,fpga_file)
    fpga_clk = syncFpgaClock(snap,srate)
    retdict = gatherData(snap,ant,ncaptures,srate,ifc,freq)
    retdict['host'] = host
    retdict['fpga_clk'] = fpga_clk
    retdict['fpgfile'] = fpga_file
    retdict['srate'] = srate
    return retdict

def gatherData(snap,ant,ncaptures,srate,ifc,rfc=None):

    logger = logger_defaults.getModuleLogger(__name__)

    out = {}
    out['ant'] = ant
    out['ifc'] = ifc

    if not rfc or rfc == 0.0:
        rfc = ata_control.get_sky_freq()
        logger.info("no rfc provided. rfc readed from the ata sky frequency: {}".format(rfc))
    
    out['rfc'] = rfc

    #additional context information
    #TODO: is it necessary
    out['ata_status_info'] = ata_control.get_ascii_status()
    out['ata_pam_dict'] = ata_control.get_pams([ant])
    out['ata_det_dict'] = ata_control.get_dets([ant])

    tb_syn_period = snap.read_int('timebase_sync_period')
    acc_len = float(tb_syn_period / (4096 / 4))
    int_time = float(4.0*tb_syn_period/(srate*1e6))
    out['tint'] = int_time

    logger.info( "%s: Grabbing ADC statistics to write to file" % ant)
    adc0 = []
    adc1 = []
    for i in range(10):
        all_chan_data = adc5g.get_snapshot(snap, 'ss_adc')
        adc0 += [all_chan_data[0::2][0::2]]
        adc1 += [all_chan_data[1::2][0::2]]

    adc0 = np.array(adc0)
    adc1 = np.array(adc1)

    out["adc0_bitsnaps"] = adc0
    out["adc1_bitsnaps"] = adc1
    out["adc0_stats"] = {"mean": adc0.mean(), "dev": adc0.std()}
    out["adc1_stats"] = {"mean": adc1.mean(), "dev": adc1.std()}

    logger.info( "%s: ADC0 mean/dev: %.2f / %.2f" % (ant, out["adc0_stats"]["mean"], out["adc0_stats"]["dev"]))
    logger.info( "%s: ADC1 mean/dev: %.2f / %.2f" % (ant, out["adc1_stats"]["mean"], out["adc1_stats"]["dev"]))

    out['fft_shift'] = snap.read_int('fft_shift')

    ant_settings = ['auto']
    #out['auto0'] = []
    #out['auto0_timestamp'] = []
    #out['auto0_of_count'] = []
    #out['fft_of0'] = []
    #out['auto1'] = []
    #out['auto1_timestamp'] = []
    #out['auto1_of_count'] = []
    #out['fft_of1'] = []

    a_set = ant_settings[0]
    logger.info( "%s: Setting snapshot select to %s (%d)" % (ant, a_set, snap_defaults.mux_sel[a_set]))
    snap.write_int('vacc_ss_sel', snap_defaults.mux_sel[a_set])
    for ii in range(ncaptures):

        logger.info( "%s: Grabbing data (%d of %d)" % (ant, ii+1, ncaptures))
        x,t = snap.snapshots.vacc_ss_ss.read_raw()
        d = np.array(struct.unpack('>%dL' % (x['length']/4), x['data'])) / acc_len

        if ii == 0:
            data0 = np.zeros((ncaptures,d.shape[0]//2))
            data1 = np.zeros((ncaptures,d.shape[0]//2))
            tarray = np.zeros(ncaptures)
            data0cnt = np.zeros(ncaptures)
            data1cnt = np.zeros(ncaptures)
            fft0cnt = np.zeros(ncaptures)
            fft1cnt = np.zeros(ncaptures)
            frange = np.linspace(out['rfc'] - (srate - ifc), out['rfc'] - (srate - ifc) + srate/2., d.shape[0]//2)

        data0[ii,:] = d[0::2]
        data1[ii,:] = d[1::2]
        tarray[ii] = t
        data0cnt[ii] = snap.read_int('power_vacc0_of_count')
        fft0cnt[ii] = snap.read_int('fft_of')
        data1cnt[ii] = snap.read_int('power_vacc1_of_count')
        #is this read necessary?
        fft1cnt[ii] = snap.read_int('fft_of')
        #out['auto0'] += [d[0::2]]
        #out['auto0_timestamp'] += [t]
        #out['auto0_of_count'] += [snap.read_int('power_vacc0_of_count')]
        #out['fft_of0'] += [snap.read_int('fft_of')]
        #out['auto1'] += [d[1::2]]
        #out['auto1_timestamp'] += [t]
        #out['auto1_of_count'] += [snap.read_int('power_vacc1_of_count')]
        #out['fft_of1'] += [snap.read_int('fft_of')]

    out['frange'] = frange
    out['auto0'] = data0
    out['auto0_timestamp'] = tarray
    out['auto0_of_count'] = data0cnt
    out['fft_of0'] = fft0cnt
    out['auto1'] = data1
    out['auto1_timestamp'] = tarray
    out['auto1_of_count'] = data1cnt
    out['fft_of1'] = fft1cnt

    logger.info("recording finished for {}".format(ant))
    return out 

def selectMux(snap,a_sel):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info( "Setting snapshot select to %s (%d)" % (a_sel, snap_defaults.mux_sel[a_sel]))
    snap.write_int('vacc_ss_sel', snap_defaults.mux_sel[a_sel])

def get_log_data(snap, a_sel, rfc, srate=snap_defaults.srate, ifc=snap_defaults.ifc):
    x,t = snap.snapshots.vacc_ss_ss.read_raw()
    d = np.array(struct.unpack('>%dL' % (x['length']/4), x['data']))
    # Calculate Frequency scale of plots
    # d array holds twice as many values as there are freq channels (either xx & yy, or xy_r & xy_i
    frange = np.linspace(rfc - (srate - ifc), rfc - (srate - ifc) + srate/2., d.shape[0]//2)
    # Make two plots -- either xx, yy. Or abs(xy), phase(xy)
    if a_sel == "auto":
        xx = d[0::2]
        yy = d[1::2]
        return frange, 10*np.log10(xx), 10*np.log10(yy)
        #return frange, xx, yy
    else:
        xy = np.array(d[0::2] + 1j*d[1::2], dtype=np.complex32)
        return frange, 10*np.log10(np.abs(xy)), np.angle(xy)


if __name__ == "__main__":
    import logging
    ncaptures = 60
    host = 'snap0'
    ant = '1c'
    logger = logging.getLogger("main")
    fh = logging.FileHandler('/tmp/python.log',mode='w')
    lf = logging.Formatter(fmt='%(asctime)s.%(msecs)03d %(levelname)s %(name)s: %(message)s',datefmt='%Y-%m-%d,%H:%M:%S')
    fh.setFormatter(lf)
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    fpga_file = snap_defaults.spectra_snap_file
    snap = getSnap(host,fpga_file)
    fpga_clk = syncFpgaClock(snap,snap_defaults.srate)
    logger = logging.getLogger('tftpy')
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)
    casperfpga.transport_tapcp.set_log_level(logging.DEBUG)
    logger = logging.getLogger('casperfpga.transport_tapcp')
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)
    retdict = gatherData(snap,ant,ncaptures,snap_defaults.srate,snap_defaults.ifc)
    tdiff = np.diff(retdict['auto0_timestamp'])-retdict['tint']
    import matplotlib.pyplot as plt
    plt.plot(tdiff)
    plt.show()
    import pdb
    pdb.set_trace()
