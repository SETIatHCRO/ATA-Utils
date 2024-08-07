#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import numpy as np
import struct
from ATATools import ata_control,logger_defaults
from . import snap_defaults,snap_recorder
import matplotlib.pyplot as plt

def handle_close(evt):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("figure closed")
    evt.canvas.figure.was_closed = True

def plotAuto(host,rfc=None,fpga_file=snap_defaults.plot_snap_file,srate=snap_defaults.srate,ifc=snap_defaults.ifc):
    snap = getSelectSnap(host,fpga_file,srate,sel='auto')

    if not rfc or rfc == 0.0:
        rfc = ata_control.get_sky_freq()
        logger = logger_defaults.getModuleLogger(__name__)
        logger.info("no rfc provided. rfc readed from the ata sky frequency: {}".format(rfc))

    plt.ion()
    fig, ax = plt.subplots(2,1)
    fig.was_closed = False
    fig.canvas.mpl_connect('close_event', handle_close)

    while(not fig.was_closed):
        frange, d0, d1 = snap_recorder.get_log_data(snap, 'auto', rfc, srate,ifc)
        ax[0].clear()
        ax[1].clear()
        ax[0].plot(frange, d0)
        ax[1].plot(frange, d1)
        ax[0].set_ylabel("Power [dB arb. ref.]")
        ax[1].set_ylabel("Power [dB arb. ref.]")
        ax[1].set_xlabel("Frequency [MHz]")
        plt.show()
        plt.pause(0.001)

def plotWaterfall(host,wlen,rfc=None,fpga_file=snap_defaults.plot_snap_file,srate=snap_defaults.srate,ifc=snap_defaults.ifc):
    snap = getSelectSnap(host,fpga_file,srate,sel='auto')

    if not rfc or rfc == 0.0:
        rfc = ata_control.get_sky_freq()
        logger = logger_defaults.getModuleLogger(__name__)
        logger.info("no rfc provided. rfc readed from the ata sky frequency: {}".format(rfc))

    plt.ion()
    fig, ax = plt.subplots(1,2)
    fig.was_closed = False
    fig.canvas.mpl_connect('close_event', handle_close)

    frange, d0, d1 = snap_recorder.get_log_data(snap, 'auto', rfc, srate,ifc)
    dataX = np.zeros((wlen,len(d0)))
    dataY = np.zeros((wlen,len(d1)))
    dataExtent = [frange[0],frange[-1],wlen-1,0]
    dataX[0,:] = d0
    dataY[0,:] = d1

    while(not fig.was_closed):
        ax[0].clear()
        ax[1].clear()
        mp1=ax[0].imshow(dataX,aspect='auto',interpolation='none', extent=dataExtent)
        mp2=ax[1].imshow(dataY,aspect='auto',interpolation='none', extent=dataExtent)
        ax[0].set_ylabel("snap no")
        ax[0].set_xlabel("Frequency [MHz]")
        ax[1].set_xlabel("Frequency [MHz]")
        ax[0].set_title('X pol')
        ax[0].set_title('Y pol')
        plt.show()
        plt.pause(0.001)
        frange, d0, d1 = snap_recorder.get_log_data(snap, 'auto', rfc, srate,ifc)
        dataX[1:,:] = dataX[0:-1,:]
        dataY[1:,:] = dataY[0:-1,:]
        dataX[0,:] = d0
        dataY[0,:] = d1


def plotCross(host,rfc=None,fpga_file=snap_defaults.plot_snap_file,srate=snap_defaults.srate,ifc=snap_defaults.ifc):
    snap = getSelectSnap(host,fpga_file,srate,sel='cross')

    if not rfc or rfc == 0.0:
        rfc = ata_control.get_sky_freq()
        logger = logger_defaults.getModuleLogger(__name__)
        logger.info("no rfc provided. rfc readed from the ata sky frequency: {}".format(rfc))

    plt.ion()
    fig, ax = plt.subplots(2,1)
    fig.was_closed = False
    fig.canvas.mpl_connect('close_event', handle_close)

    while(not fig.was_closed):
        frange, d0, d1 = snap_recorder.get_log_data(snap, 'cross', rfc, srate,ifc)
        ax[0].clear()
        ax[1].clear()
        ax[0].plot(frange, d0)
        ax[1].plot(frange, d1)
        ax[0].set_ylabel("Power [dB arb. ref.]")
        ax[1].set_ylabel("Phase [radians]")
        ax[1].set_xlabel("Frequency [MHz]")
        plt.show()
        plt.pause(0.001)

def getSelectSnap(host,fpga_file,srate=snap_defaults.srate,sel='auto'):
    snap = snap_recorder.getSnap(host,fpga_file)
    fpga_clk = snap_recorder.syncFpgaClock(snap,srate)
    snap_recorder.selectMux(snap,sel)
    return snap

