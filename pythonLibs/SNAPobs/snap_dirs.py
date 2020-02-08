#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
directory setup for snap observations
"""

from ATATools import logger_defaults
import os
import datetime

DEFAULT_DATA_DIR = "~/data"

def get_dir_obsid(obsid,defaultdir=None):
    if not defaultdir:
        defaultdir = DEFAULT_DATA_DIR
    if not obsid:
        id_string = 'singles'
    else:
        id_string = "id{0:d}".format(obsid)
    output_dir = os.path.expanduser("%s/%s" % (os.path.expanduser(defaultdir), id_string))
    return output_dir

def set_output_dir_obsid(obsid=None,defaultdir=None):
    output_dir = get_dir_obsid(obsid,defaultdir)
    set_output_dir(output_dir)

def get_dir_date(date=None,defaultdir=None):
    if not date:
        date = datetime.datetime.today()
    if not defaultdir:
        defaultdir = DEFAULT_DATA_DIR

    date_string = date.strftime('%Y%m%d')
    output_dir = os.path.expanduser("%s/day%s" % (os.path.expanduser(defaultdir), todays_date))
    return output_dir

def set_output_dir_date(date=None,defaultdir=None):
    output_dir = get_dir_date(date,defaultdir)
    set_output_dir(output_dir)

def set_output_dir(dirname):

    global snap_output_dir
    
    logger = logger_defaults.getModuleLogger(__name__)

    output_dir = os.path.expanduser(dirname)

    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    except OSError:
        logger.error("Error: Creating directory %s" %  output_dir)
        raise
    
    snap_output_dir = output_dir
    logger.info('Storage directory set to {}'.format(output_dir))

def get_output_dir():

    global snap_output_dir
    return snap_output_dir

