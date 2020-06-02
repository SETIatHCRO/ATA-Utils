#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from astropy import units as u
from astropy.coordinates import Angle

def hour2hms(hour):
    h = Angle(hour*u.h).to_string(unit=u.h, sep=":")
    # add leading zero i.e. 0:24:43 to 00:24:43
    h_split = h.split(":")
    h_split[0] = h[0].zfill(2)
    h = ":".join(h_split)
    return h

def deg2dms(degree):
    ang = Angle(degree*u.degree).to_string(unit=u.degree, sep=":")
    # add leading zero
    ang_split = ang.split(":")
    ang_split[0] = ang_split[0].zfill(3) if ang[0] == "-" \
            else ang_split[0].zfill(2)
    ang = ":".join(ang_split)
    return ang
