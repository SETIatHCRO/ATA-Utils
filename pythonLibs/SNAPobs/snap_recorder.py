#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

    logger.info( "srate = %.1f" % (srate))

    check_clock = np.abs((fpga_clk*4. / srate) - 1) < 0.01

    # If bad clock, try several more times
    num_check = 0
    while(check_clock == False and num_check < snap_defaults.clock_attempts):
        num_check = num_check + 1
        time.sleep(1)
        logger.info( "Estimating FPGA clock retry %d" % (num_check))
        fpga_clk = snap.estimate_fpga_clock()
        logger.info( "%s: Clock estimate is %.1f, try %d" % (fpga_clk, num_check))
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
    return retdict

def gatherData(snap,ant,ncaptures,srate,ifc,rfc=None):

    logger = logger_defaults.getModuleLogger(__name__)

    out = {}
    out['ant'] = ant

    if not rfc or rfc == 0.0:
        rfc = ata_control.get_sky_freq()
        logger.info("no rfc provided. rfc readed from the ata sky frequency: {}".format(rfc))
    
    out['rfc'] = rfc

    #additional context information
    #TODO: is it necessary
    out['ata_status_info'] = ata_control.get_ascii_status()
    out['ata_pam_dict'] = ata_control.get_pams([ant])
    out['ata_det_dict'] = ata_control.get_dets([ant])

    acc_len = float(snap.read_int('timebase_sync_period') / (4096 / 4))

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
    out['auto0'] = []
    out['auto0_timestamp'] = []
    out['auto0_of_count'] = []
    out['fft_of0'] = []
    out['auto1'] = []
    out['auto1_timestamp'] = []
    out['auto1_of_count'] = []
    out['fft_of1'] = []

    for i in range(ncaptures):

        for a_set in ant_settings:
            logger.info( "%s: Setting snapshot select to %s (%d)" % (ant, a_set, snap_defaults.mux_sel[a_set]))
            snap.write_int('vacc_ss_sel', snap_defaults.mux_sel[a_set])
            logger.info( "%s: Grabbing data (%d of %d)" % (ant, i+1, ncaptures))
            x,t = snap.snapshots.vacc_ss_ss.read_raw()
            d = np.array(struct.unpack('>%dL' % (x['length']/4), x['data'])) / acc_len
            frange = np.linspace(out['rfc'] - (srate - ifc), out['rfc'] - (srate - ifc) + srate/2., d.shape[0])
            out['frange'] = frange
            out['auto0'] += [d[0::2]]
            out['auto0_timestamp'] += [t]
            out['auto0_of_count'] += [snap.read_int('power_vacc0_of_count')]
            out['fft_of0'] += [snap.read_int('fft_of')]
            out['auto1'] += [d[1::2]]
            out['auto1_timestamp'] += [t]
            out['auto1_of_count'] += [snap.read_int('power_vacc1_of_count')]
            out['fft_of1'] += [snap.read_int('fft_of')]

    return out 


'''

logger = ata_control.setup_logger()
ata_control.set_output_dir()

logger.info("Recorder started")

#logger = logging.getLogger(snap_onoffs_contants.LOGGING_NAME)
#logger.setLevel(logging.INFO)
#sh = logging.StreamHandler(sys.stdout)
#fmt = logging.Formatter('[%(asctime)-15s] %(message)s')
#sh.setFormatter(fmt)
#logger.addHandler(sh)

parser = argparse.ArgumentParser(description='Plot ADC Histograms and Spectra',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('host', type=str,
                    help = 'Hostname / IP of SNAP')
parser.add_argument('fpgfile', type=str,
                    help = '.fpgfile to program')
parser.add_argument('-s', dest='srate', type=float, default=900.0,
                    help ='Sample rate in MHz for non-interleaved band. Used for spectrum axis scales')
parser.add_argument('-n', dest='ncaptures', type=int, default=16,
                    help ='Number of data captures (for each correlation product)')
parser.add_argument('-r', dest='rfc', type=float, default=0.0,
                    help ='RF centre frequency in MHz. 0 => Grab the frequency from the ATA control system')
parser.add_argument('-i', dest='ifc', type=float, default=629.1452,
                    help ='IF centre frequency in MHz')
parser.add_argument('-c', dest='comment', type=str, default="",
                    help ='comment to be appended at the end of the filename (eg, a source name)')
parser.add_argument('-p', dest='path', type=str, default="~/data",
                    help ='Directory in which to record data')
parser.add_argument('-a', dest='ant', type=str, default=None,
                    help ='ATA Antenna string (used for getting monitoring data')
parser.add_argument('-t', dest='target_rms', type=float, default=None,
        help ='Target RMS to achieve by tweaking USB attenuators. Default: Do not tune')
parser.add_argument('-x', dest='source', type=str, default=None,
                    help ='name of the source')
parser.add_argument('-o', dest='obsid', type=int, default=None,
                    help ='observation id number')

args = parser.parse_args()
out = vars(args).copy()

if args.rfc == 0.0:
    logger.info( "%s: Reading Sky center frequency from the ATA control system" % args.ant)
    out["rfc"] = ata_control.get_sky_freq()
    logger.info( "%s: Frequency is %.1f MHz" % (args.ant, out["rfc"]))

logger.info("%s: Trying to get ATA status information" % args.ant)
try:
    out['ata_status'] = ata_control.get_ascii_status()
    logger.info("%s: Succeeded -- status will be written into the output file" % args.ant)
except:
    logger.info( "%s: !!!!!!!!!!!!!!!!!!!!!!!!" % args.ant)
    logger.info( "%s: !!!!!!   Failed   !!!!!!" % args.ant)
    logger.info( "%s: !!!!!!!!!!!!!!!!!!!!!!!!" % args.ant)

#Not needed
#if args.ant is not None:
#    ata_control.get_pam_status(args.ant)
RedisManager.get_instance().set_and_pub('snap_state_%s'%args.host, { 'state' : 'snap_init', 'snap' : args.host  }, 'onoff_state')

datadir = os.path.expanduser(args.path)

if not os.path.isdir(datadir):
    logger.info( "%s: Chosen data directory: %s does not exist. Create it and run this script again!" % (args.ant, datadir))
    exit()

filename = os.path.join(datadir, "%d_rf%.2f_n%d_%s.pkl" % (time.time(), out['rfc'], args.ncaptures, args.comment))
logger.info( "%s: Output filename is %s" % (args.ant, filename))

logger.info( "%s: Using RF center frequency of %.2f" % (args.ant, out['rfc']))
logger.info( "%s: Using IF center frequency of %.2f" % (args.ant, args.ifc))

logger.info( "%s: Connecting to %s" % (args.ant, args.host))
snap = casperfpga.CasperFpga(args.host)
logger.info( "%s: Interpretting design data for %s with %s" % (args.ant, args.host, args.fpgfile))
snap.get_system_information(args.fpgfile)


logger.info( "%s: Figuring out accumulation length" % args.ant)
acc_len = float(snap.read_int('timebase_sync_period') / (4096 / 4))
logger.info( "%s: Accumulation length is %f" % (args.ant, acc_len))


logger.info( "%s: Estimating FPGA clock" % args.ant)
fpga_clk = snap.estimate_fpga_clock()
out['fpga_clk'] = fpga_clk
logger.info( "%s: Clock estimate is %.1f" % (args.ant, fpga_clk))
logger.info( "%s: args.srate = %.1f" % (args.ant, args.srate))

check_clock = np.abs((fpga_clk*4. / args.srate) - 1) < 0.01

# If bad clock, try several more times
num_check = 0
max_check = 5
while(check_clock == False and num_check < max_check):
    num_check = num_check + 1
    time.sleep(1)
    logger.info( "%s: Estimating FPGA clock retry %d" % (args.ant, num_check))
    fpga_clk = snap.estimate_fpga_clock()
    out['fpga_clk'] = fpga_clk
    logger.info( "%s: Clock estimate is %.1f, try %d" % (args.ant, fpga_clk, num_check))
    logger.info( "%s: args.srate = %.1f" % (args.ant, args.srate))
    check_clock = np.abs((fpga_clk*4. / args.srate) - 1) < 0.01

#If still bad clock, send email and exit
if(check_clock == False):
    ata_control.send_email("Clock error", "%s: bad clock estimate %.1f"% (args.ant, fpga_clk))
    sys.exit(1)

#assert np.abs((fpga_clk*4. / args.srate) - 1) < 0.01

mux_sel = {'auto':0, 'cross':1}

result = { "type" : "recorder_atten" }
first = True
is_pam = False

if args.target_rms is not None:
    logger.info("%s: Trying to tune power levels to RMS: %.2f" % (args.ant, args.target_rms))

    max_attempts = 5
    num_snaps = 5
    #atteni = snap_obs_db.get_atten_db("%sx"%args.ant, args.source, float(out["rfc"]))
    #attenq = snap_obs_db.get_atten_db("%sy"%args.ant, args.source, float(out["rfc"]))
    atteni = 0.0
    attenq = 0.0
    logger.info("%s: default x dB=%.2f, y dB=%.2f" % (args.ant, atteni, attenq))

    try:
        for attempt in range(max_attempts):
            #ata_control.set_atten_by_ant(args.ant + "x", atteni)
            #ata_control.set_atten_by_ant(args.ant + "y", attenq)
            atten_ants = "%s%s,%s%s" % (args.ant, "x", args.ant, "y")
            atten_db = "%2f,%.2f" % (atteni, attenq)

            #Throw an error and return 1 if set_atten fails. I did have a time where
            #the server "bserver1" needed to be rebooted, the USB port on one
            #of the attenuators was not working, a reboot fixed it. - JR
            try:
                answer = ata_control.set_atten(atten_ants, atten_db)
                #if there is no attenuator, then attempt to adject the PAMs
                if "no attenuator for" in answer:
                      is_pam = True
                      if(first == True):
                        logger.info("%s: No attenuator connected, setting pams to %s" % (args.ant, atten_db))
                        ata_control.set_pam_attens(args.ant, 0.0, 0.0)
                        first = False
                      else:
                        ata_control.set_pam_attens(args.ant, atteni, attenq)
            except RuntimeError, err:
                #except Exception, err:
                logger.info("Error in snap_record.py, exiting: %s" % repr(err))
                ata_control.send_email("atten problem", repr(err))
                sys.exit(1)
                #print ("ERROR ant %s set_pam_attens" % args.ant)
                #continue

            # Store attenuation values used
            out['attenx'] = atteni
            out['atteny'] = attenq
            chani = []
            chanq = []
            for i in range(num_snaps):
                all_chan_data = adc5g.get_snapshot(snap, 'ss_adc')
                chani += [all_chan_data[0::2][0::2]]
                chanq += [all_chan_data[1::2][0::2]]
            chani = np.array(chani)
            chanq = np.array(chanq)

            delta_atteni = 20*np.log10(chani.std() / args.target_rms)
            delta_attenq = 20*np.log10(chanq.std() / args.target_rms)
        
            logger.info("%sx: Channel I ADC mean/std-dev/deltai: %.2f / %.2f, delta=%.2f" % \
                    (args.ant, chani.mean(), chani.std(), delta_atteni))
            logger.info("%sy: Channel Q ADC mean/std-dev/deltaq: %.2f / %.2f, delta=%.2f" % \
                    (args.ant, chanq.mean(), chanq.std(), delta_attenq))
        
            if (delta_atteni < 1) and (delta_attenq < 1):
                logger.info( "%s: Tuning complete" % args.ant)
                snap_obs_db.record_atten("%sx"%args.ant, args.obsid, args.source, float(out["rfc"]), atteni)
                snap_obs_db.record_atten("%sy"%args.ant, args.obsid, args.source, float(out["rfc"]), attenq)
                result['ant'] = args.ant
                if(is_pam == True):
                      result['pam_atten_x'] = atteni
                      result['pam_atten_y'] = attenq
                else:
                      result['mini_atten_x'] = atteni
                      result['mini_atten_y'] = attenq
                result['freq'] = out['rfc']
                break
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
                logger.info( "%s: New X-attenuation: %.3f" % (args.ant, atteni))
                logger.info( "%s: New Y-attenuation: %.3f" % (args.ant, attenq))
                result['ant'] = args.ant
                if(is_pam == True):
                      result['pam_atten_x'] = atteni
                      result['pam_atten_y'] = attenq
                else:
                      result['mini_atten_x'] = atteni
                      result['mini_atten_y'] = attenq
                result['freq'] = out['rfc']
    except Exception, err:
        # For some reason the Attenuation setting routine failed.
        # Use -1 attenuation values to indicate this so that data files
        # can be flagged.
        logger.info( "%s: Attenuator tuning failed! err=%s" % (args.ant, repr(err)))
        traceback.print_exc(file=sys.stdout)
        sys.exit(-1)
        out['attenx'] = -1
        out['atteny'] = -1

logger.info( "%s: Grabbing ADC statistics to write to file" % args.ant)
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

logger.info( "%s: ADC0 mean/dev: %.2f / %.2f" % (args.ant, out["adc0_stats"]["mean"], out["adc0_stats"]["dev"]))
logger.info( "%s: ADC1 mean/dev: %.2f / %.2f" % (args.ant, out["adc1_stats"]["mean"], out["adc1_stats"]["dev"]))

out['fft_shift'] = snap.read_int('fft_shift')
if args.ant is not None:
    try:
        out['pam_stats'] = ata_control.get_pam_status(args.ant)
    except:
        pass

ants = ['auto']
out['auto0'] = []
out['auto0_timestamp'] = []
out['auto0_of_count'] = []
out['fft_of0'] = []
out['auto1'] = []
out['auto1_timestamp'] = []
out['auto1_of_count'] = []
out['fft_of1'] = []

for i in range(args.ncaptures):
    RedisManager.get_instance(False).set_and_pub('snap_state_%s'%args.host, { 'state' : 'snap_record', 'snap' : args.host, 'capture_num' : i  }, 'onoff_state')

    for ant in ants:
        logger.info( "%s: Setting snapshot select to %s (%d)" % (args.ant, ant, mux_sel[ant]))
        snap.write_int('vacc_ss_sel', mux_sel[ant])
        logger.info( "%s: Grabbing data (%d of %d)" % (args.ant, i+1, args.ncaptures))
        x,t = snap.snapshots.vacc_ss_ss.read_raw()
        #d = np.array(struct.unpack('>%dl' % (x['length']/4), x['data'])) / acc_len
        d = np.array(struct.unpack('>%dL' % (x['length']/4), x['data'])) / acc_len
        frange = np.linspace(out['rfc'] - (args.srate - args.ifc), out['rfc'] - (args.srate - args.ifc) + args.srate/2., d.shape[0])
        out['frange'] = frange
        out['auto0'] += [d[0::2]]
        out['auto0_timestamp'] += [t]
        out['auto0_of_count'] += [snap.read_int('power_vacc0_of_count')]
        out['fft_of0'] += [snap.read_int('fft_of')]
        out['auto1'] += [d[1::2]]
        out['auto1_timestamp'] += [t]
        out['auto1_of_count'] += [snap.read_int('power_vacc1_of_count')]
        out['fft_of1'] += [snap.read_int('fft_of')]

logger.info( "%s: Dumping data to %s" % (args.ant, filename))
pkl.dump(out, open(filename, 'w'))

if(is_pam ==  True):
    logger.info(result)

RedisManager.get_instance().set_and_pub('snap_state_%s'%args.host, { 'state' : 'snap_idle', 'snap' : args.host }, 'onoff_state')

sys.exit(0)


'''

