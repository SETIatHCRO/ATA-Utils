#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

"""
defaults values for snap observations
"""

spectra_snap_file = "/home/sonata/dev/ata_snap/snap_adc5g_spec/outputs/snap_adc5g_spec_2018-06-23_1048.fpg"
plot_snap_file = "/home/sonata/dev/ata_snap/snap_adc5g_spec/outputs/snap_adc5g_spec_2018-07-07_1844.fpg"
rms = 16.0
rms_attempts = 5
#srate = 900.0
srate = 1024.0
clock_attempts = 5
#ifc = 629.1452
#ifc = 450.0000
ifc = 512.0
mux_sel = {'auto':0, 'cross':1}
#bw = srate/2 #MHz
#nchan = 2048
bw = srate #MHz
nchan = 4096
base_name = "frb-snap"
template_header = "template_header.txt"
discone_name = 'rfi'

if 'PSRHOME' not in os.environ:
    raise RuntimeError("Env variable $PSRHOME is not set, please run: "
            "'export PSRHOME=\"/home/obsuser\"'")
share_dir = os.path.join(os.environ['PSRHOME'], 'share')

redishost='redishost'
