#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

"""
defaults values for snap observations
"""

rms = 16.0
rms_attempts = 5
srate = 2048.0
clock_attempts = 5
ifc = 512.0
mux_sel = {'auto':0, 'cross':1}
bw = srate/2 #MHz
nchan = 4096
base_name = "frb-snap"
template_header = "template_header.txt"
discone_name = 'rfi'

#if 'PSRHOME' in os.environ:
#    baseshare = os.environ['PSRHOME']
#elif 'ATASHAREDIR'  in os.environ:
if 'ATASHAREDIR' in os.environ:
    baseshare = os.environ['ATASHAREDIR']
else:
    raise RuntimeError("Env variable $ATASHAREDIR, is not set, please run: "
            "'export ATASHAREDIR=\"/opt/mnt\"'")

share_dir = os.path.join(baseshare, 'share')

redishost='redishost'
