#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is a dummy package if you are using that not in ATA, modify it 
and put in no-repository folder

Created on Tue Dec 17 2019

@author: jkulpa
"""

import os
import sys
import logging 
import requests
from six.moves import configparser

address ='PUT_YOUR_ADDRESS'
keyfile ='PUT_YOUR_FILE.KEY'

def postSlackMsg(msg):
    logger = logging.getLogger(__name__)
    try:
        data = '{"text":"%s"}' % msg;
        headers = {'Content-type': 'application/json'}
        configParser = configparser.RawConfigParser()

        configParser.read(os.path.expanduser(keyfile))

        key = configParser.get('slack','key')
        
        response = requests.post(address+key,headers=headers,data=data)
        logger.info("Message sent to slack bot.")
    except:
        logger.exception("Unable to sent message to slack bot.")

