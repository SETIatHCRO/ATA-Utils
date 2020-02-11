#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
save functions for snap uvh5 file
"""

from ATATools import logger_defaults,ata_constants,ata_control
from . import snap_dirs
import pyuvdata
from astropy.time import Time
import datetime
import numpy
import datetime
import os

def create_snap_uvdata(snapdict,azoffset,eloffset,recid,setid=None):
    logger_defaults.getModuleLogger(__name__)
    obj = pyuvdata.UVData()

    ant = snapdict['ant']
    ashape = numpy.shape(snapdict['auto0'])

    #obj.latitude = ata_constants.ATA_LAT
    #obj.longitude = ata_constants.ATA_LON
    #obj.altitude = ata_constants.ATA_ELEV
    obj.telescope_location = pyuvdata.uvutils.XYZ_from_LatLonAlt(ata_constants.ATA_LAT/180.0*numpy.pi,ata_constants.ATA_LON/180.0*numpy.pi,ata_constants.ATA_ELEV) 
    obj.telescope_name = ata_constants.ATA_NAME
    obj.instrument = ata_constants.ATA_NAME + snapdict['host']
    if azoffset == 0 and eloffset == 0:
        obj.object_name = snapdict['source']
    else:
        obj.object_name = '{0:s}_off_{1:03.1f}_{2:03.1f}'.format(snapdict['source'],azoffset,eloffset)
    obj.history = 'Snap Waterfall measurement'
    obj.phase_type = 'phased'
    obj.Nants_data = 1
    obj.Nants_telescope = len(ata_constants.ant_names)
    aind = ata_constants.ant_names.index(ant)
    obj.ant_1_array = numpy.array([aind] * ashape[0])
    obj.ant_2_array = numpy.array([aind] * ashape[0])
    obj.baseline_array = pow(2,16) + (numpy.array([aind] * ashape[0])+1) * 2049
    obj.antenna_names = ata_constants.ant_names
    obj.antenna_numbers = list(range(len(ata_constants.ant_names)))
    obj.Nbls = 1
    obj.Nblts = ashape[0] #should be the same as snapdict['ncaptures']
    obj.Nfreqs = ashape[1]
    obj.Npols = 2
    #that may be wrong
    obj.Ntimes = ashape[0]
    obj.Nspws = 1
    obj.uvw_array = numpy.zeros((ashape[0],3),dtype=float)
    tt = Time(snapdict['auto0_timestamp'],format='unix',location=(ata_constants.ATA_LON,ata_constants.ATA_LAT,ata_constants.ATA_ELEV))
    #obj.time_array = tt.to_value('mjd', 'long')
    obj.time_array = tt.mjd
    #utils.get_lst_for_time?
    obj.lst_array = numpy.array(tt.sidereal_time('apparent'))/12*numpy.pi
    obj.integration_time = [ashape[1]/(snapdict['srate']*1e6)] *ashape[0]
    tmparray = numpy.zeros((1,len(snapdict['frange'])))
    tmparray[0][:] = snapdict['frange']*1e6
    obj.freq_array = tmparray
    #obj.channel_width = snapdict['srate']/2
    obj.channel_width = (snapdict['frange'][1]-snapdict['frange'][0])*1e6
    #i am not sure about that
    obj.spw_array=[1]
    #-5 is XX, -6 is YY
    obj.polarization_array = [-5,-6]
    obj.vis_units = 'uncalib'
    obj.nsample_array = numpy.ones((ashape[0],1,ashape[1],2),dtype=float)
    obj.flag_array = numpy.zeros((ashape[0],1,ashape[1],2),dtype=bool)
    obj.data_array = numpy.zeros((ashape[0],1,ashape[1],2),dtype=numpy.complex64)
    xx = numpy.array(snapdict['auto0'],dtype=numpy.complex64)
    obj.data_array[:,0,:,0] = xx
    yy = numpy.array(snapdict['auto1'],dtype=numpy.complex64)
    obj.data_array[:,0,:,1] = yy
    #now we have all required parameters, let's fill the extra keywords
    apos_dict = ata_control.get_ant_pos(ata_constants.ant_names)
    obj.antenna_positions = numpy.zeros((len(ata_constants.ant_names),3),dtype=float)
    for ii in range(len(ata_constants.ant_names)):
        cant = ata_constants.ant_names[ii]
        obj.antenna_positions[ii][0] = apos_dict[cant][1]
        obj.antenna_positions[ii][1] = apos_dict[cant][0]
        obj.antenna_positions[ii][2] = apos_dict[cant][2]

    #optional arguments
    obj.timesys = datetime.datetime.utcfromtimestamp(snapdict['auto0_timestamp'][0]).strftime('%Y-%m-%d %H:%M:%S')

    if 'ra' in snapdict:
        obj.phase_center_ra = snapdict['ra']/12*numpy.pi
    else:
        obj.phase_center_ra = 0
    if 'dec' in snapdict:
        obj.phase_center_dec = snapdict['dec']/180*numpy.pi
    else:
        obj.phase_center_dec = 0
    #J2000.0
    obj.phase_center_epoch = 2000.0

    #now we are creating an extra keywords dictionary
    ek = {}
    ek['ata_version'] = '0.2'
    ek['fft_shift'] = snapdict['fft_shift']
    ek['adc0_bitsnaps'] = snapdict['adc0_bitsnaps']
    ek['adc1_bitsnaps'] = snapdict['adc1_bitsnaps']
    ek['adc0_mean'] = snapdict['adc0_stats']['mean']
    ek['adc0_dev'] = snapdict['adc0_stats']['dev']
    ek['adc1_mean'] = snapdict['adc1_stats']['mean']
    ek['adc1_dev'] = snapdict['adc1_stats']['dev']
    ek['lfft_of0'] = len(snapdict['fft_of0'])
    for ii in range(len(snapdict['fft_of0'])):
        ek['fft_of0_' +str(ii)] = snapdict['fft_of0'][ii]
    ek['lfft_of1'] = len(snapdict['fft_of1'])
    for ii in range(len(snapdict['fft_of1'])):
        ek['fft_of1_' +str(ii)] = snapdict['fft_of1'][ii]
    ek['lauto0_of_count'] = len(snapdict['auto0_of_count'])
    for ii in range(len(snapdict['auto0_of_count'])):
        ek['auto0_of_count_' +str(ii)] = snapdict['auto0_of_count'][ii]
    ek['lauto1_of_count'] = len(snapdict['auto1_of_count'])
    for ii in range(len(snapdict['auto1_of_count'])):
        ek['auto1_of_count_' +str(ii)] = snapdict['auto1_of_count'][ii]
    ek['srate'] = snapdict['srate']
    ek['fpga_clk'] = snapdict['fpga_clk']
    ek['rfc'] = snapdict['rfc']
    ek['ifc'] = snapdict['ifc']
    ek['fpgfile'] = snapdict['fpgfile']
    if not setid:
        ek['setid'] = -1
    else:
        ek['setid'] = setid
    ek['recid'] = recid
    ek['ant'] = ant
    if 'az' in snapdict:
        ek['ant_az'] = snapdict['az']
    else:
        ek['ant_az'] = 0.0
    if 'el' in snapdict:
        ek['ant_el'] = snapdict['el']
    else:
        ek['ant_el'] = 0.0

    obj.extra_keywords = ek
    return obj

def saveFile(filepart,snapdict,azoffset,eloffset,recid,setid):
    logger_defaults.getModuleLogger(__name__)
    uvdat = create_snap_uvdata(snapdict,azoffset,eloffset,recid,setid=None)
    filename = os.path.join(snap_dirs.get_output_dir(),'snap_' + str(recid) + '_' + filepart + '_' + snapdict['ant'] + '.h5')
    uvdat.write_uvh5(filename)

if __name__== "__main__":
    import pickle
    f = open('testing_save1a.pkl','rb')
    snapdict = pickle.load( f )
    f.close()
    cc = create_snap_uvdata(snapdict,0,0)

