#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
default initialization of the loggers

Created Jan 2020

@author: jkulpa
"""



import logging

def getFileLogger(name,filename,loglevel = logging.WARNING):
    """
    Get the logger with default settings that stores the logs to the file

    Parameters
    -------------
        name : str
            the name of the logger. can be __name__
        filename : str 
            name of the file to log to.
        loglevel : logging.level
            the logging level. default is logging.WARNING

    Returns
    -------------
        logging.logger
            the requested logger

    """

    logger = logging.getLogger(name)
    FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'
    logging.basicConfig(filename=filename, filemode='a', level=loglevel, format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')

    return logger

def getModuleLogger(name):
    """
    Get the default module logger

    Parameters
    -------------
        name : str
            the name of the logger. can be __name__

    Returns
    -------------
        logging.logger
            the requested logger

    """

    logger = logging.getLogger(name)
    #FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'
    #logging.basicConfig(format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')

    return logger

def getProgramLogger(name,loglevel = logging.WARNING):
    """
    Get the logger with default settings that s

    Parameters
    -------------
        name : str
            the name of the logger. can be __name__
        loglevel : logging.level
            the logging level. default is logging.WARNING

    Returns
    -------------
        logging.logger
            the requested logger

    """

    logger = logging.getLogger(name)
    FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'
    logging.basicConfig(level=loglevel, format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')

    return logger


