#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
directory setup for snap observations
"""

from ATATools import logger_defaults
import os
import datetime

DEFAULT_DATA_DIR = "~/data"

def set_output_dir_obsid(defaultdir=None,obsid):

    if not defaultdir:
        defaultdir = DEFAULT_DATA_DIR

    id_string = "{0:d}".format(obsid)
    output_dir = os.path.expanduser("%s/id%s" % (os.path.expanduser(defaultdir), id_string))
    set_output_dir(dirname)


def set_output_dir_date(defaultdir=None,date=None):

    if not date:
        date = datetime.datetime.today()
    if not defaultdir:
        defaultdir = DEFAULT_DATA_DIR

    date_string = date.strftime('%Y%m%d')
    output_dir = os.path.expanduser("%s/day%s" % (os.path.expanduser(defaultdir), todays_date))
    set_output_dir(dirname)

def set_output_dir(dirname):

    global snap_output_dir
    
    logger = logger_defaults.getModuleLogger(__name__)

    output_dir = dirname

    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    except OSError:
        logger.error("Error: Creating directory %s" %  output_dir)
        raise
    
    logger.info('Storage directory set to {}'.format(output_dir))

def get_output_dir():

    global snap_output_dir
    return snap_output_dir

