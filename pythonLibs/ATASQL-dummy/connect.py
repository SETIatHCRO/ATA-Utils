#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A dummy package to connect to SQL, the real implementation should not be in repository

Created on Tue Dec 17 2019

@author: jkulpa
"""

import mysql.connector
import logging
import os
from six.moves import configparser

def connectWHEREVER():
    logger = logging.getLogger(__name__)

    try:
        mydb = mysql.connector.connect(
            host=FILLORPROVIDE_HOST,
            user=FILLORPROVIDE_USER,
            database=FILLORPROVIDE_DATABASE,
            """
            add other necessery like password, ssl_ca, ssl_key,ssl,
            ssl_verify_cert or whatever else you need
            """
            )
        return mydb
    except Exception:
        logger.exception("connecting to database(rw) failed")
        raise

