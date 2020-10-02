#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
testing flux functions
Created on Tue Dec 24 2019

@author: jkulpa
"""

import subprocess
import socket
from . import logger_defaults

RF_SWITCH_HOST = "if-switch"
RF_SWITCH_HOST_IP = "if-switch"
RF_SWITCH_USER = 'sonata'
ATTEN_HOST = "if-switch"
ATTEN_HOST_IP = "if-switch"
ATTEN_USER = 'sonata'
OBS_HOST = 'control'
OBS_USER = 'obs'

def scpFileControl(fromfile, todir):
    """
    Scp 'fromfile; from current host to the directory 'todir' on
    control machine

    Parameters
    ----------
    fromfile : str
        file to scp
    todir    : str
        directory on remote host

    Returns
    -------------
    string
        standard output of the process
    string
        standard error of the process
    """
    cmd = "scp {fromfile:s} {user:s}@{host:s}:{todir}".format(
            fromfile=fromfile, user=OBS_USER, host=OBS_HOST,
            todir=todir)
    cmd_args = cmd.split(" ")
    p = subprocess.Popen(cmd_args,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    str_out, str_err = p.communicate()
    p.wait()
    if(p.returncode):
        logger = logger_defaults.getModuleLogger(__name__)
        logger.warning("process '%s' returned error\n %s" % (cmd_args,str_err))
        raise RuntimeError("process %s failed" % cmd_args)

    return str_out,str_err


def callProg(myargs):
    """
    Call process and waits for it to finish. Throws RuntimeError if process did not
    finished with 0 code. 

    Parameters
    -------------
    myargs : string list
        program name with arguments, e.g. ['ls','-la']
        
    Returns
    -------------
    string
        standard output of the process
    string
        standard error of the process
        
    Raises
    -------------
        RuntimeError
    """
    
    p = subprocess.Popen(myargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    str_out,str_err = p.communicate()
    p.wait()
    if(p.returncode):
        logger = logger_defaults.getModuleLogger(__name__)
        logger.warning("process '%s' returned error\n %s" % (myargs,str_err)) 
        raise RuntimeError("process %s failed" % myargs)

    return str_out,str_err

def callProgIgnoreError(myargs):
    """
    Call process and waits for it to finish.

    Parameters
    -------------
    myargs : string list
        
    Returns
    -------------
    string
        standard output of the process
    string
        standard error of the process
        
    Raises
    -------------
    
    """
    p = subprocess.Popen(myargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    str_out,str_err = p.communicate()
    p.wait()
    if(p.returncode):
        logger = logger_defaults.getModuleLogger(__name__)
        logger.warning("process '%s' returned error\n %s" % (myargs,str_err)) 

    return str_out,str_err

def callObsIgnoreError(myargs):
    """
    Call process and ensure it is run on OBS machine

    Parameters
    -------------
    myargs : string list
        
    Returns
    -------------
    string
        standard output of the process
    string
        standard error of the process
        
    """
    if socket.gethostname() == OBS_HOST:
        str_out,str_err = callProgIgnoreError(myargs);
    else:
        str_out,str_err = callProgIgnoreError( ['ssh', OBS_USER +'@' + OBS_HOST ] + myargs )
        
    return str_out,str_err

def callObs(myargs):
    """
    Call process and ensure it is run on OBS machine

    Parameters
    -------------
    myargs : string list
        
    Returns
    -------------
    string
        standard output of the process
    string
        standard error of the process
        
    Raises
    -------------
    
    """
    if socket.gethostname() == OBS_HOST:
        str_out,str_err = callProg(myargs);
    else:
        str_out,str_err = callProg( ['ssh', OBS_USER +'@' + OBS_HOST ] + myargs )
        
    return str_out,str_err

def callSwitch(myargs):
    """
    Call process and ensure it is run on SWITCH machine

    Parameters
    -------------
    myargs : string list
        
    Returns
    -------------
    string
        standard output of the process
    string
        standard error of the process
        
    Raises
    -------------
    """
    if socket.gethostname() == RF_SWITCH_HOST:
        str_out,str_err = callProg(myargs);
    else:
        str_out,str_err = callProg( ['ssh', RF_SWITCH_USER +'@' + RF_SWITCH_HOST_IP ] + myargs )
        
    return str_out,str_err

def callSwitch(myargs):
    """
    Call process and ensure it is run on ATTEN machine

    Parameters
    -------------
    myargs : string list
        
    Returns
    -------------
    string
        standard output of the process
    string
        standard error of the process
        
    Raises
    -------------
    """
    if socket.gethostname() == ATTEN_HOST:
        str_out,str_err = callProg(myargs);
    else:
        str_out,str_err = callProg( ['ssh', ATTEN_USER +'@' + ATTEN_HOST_IP ] + myargs )
        
    return str_out,str_err
