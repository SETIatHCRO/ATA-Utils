#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division

import sys
import os
import json
import plumbum
import math
from subprocess import Popen, PIPE
import mysql.connector

mydb_local =  mysql.connector.connect(
  host="localhost",
  user="sonata",
  database="ants"
)

mycursor_local = mydb_local.cursor()

mydb_remote =  mysql.connector.connect(
  host="googledb",
  user="jrseti",
  database="ants"
)
mycursor_remote = mydb_remote.cursor()

antlist = []
proc = Popen(["ssh", "obs@tumulus", "ataasciistatus -l"], stdout=PIPE, stderr=PIPE)
stdout, stderr = proc.communicate()
lines = stdout.split('\n')
for line in lines:
  if line.startswith("ant"):
    parts = line.split()
    ant = parts[0][3:]
    insert = "INSERT into dish_temp_sensors set ts=now(), ant='" + ant + "'"
    try:
        temp = float(parts[5])
        insert += ", control_box_temp=" + parts[5]
    except ValueError:
        pass
    try:
        temp = float(parts[6])
        insert += ", drive_box_temp=" + parts[6]
    except ValueError:
        pass
    try:
        temp = float(parts[7])
        insert += ", pax_box_temp=" + parts[7]
    except ValueError:
        pass
    try:
        temp = float(parts[8])
        insert += ", rim_box_temp=" + parts[8]
    except ValueError:
        pass

    print insert

    mycursor_local.execute(insert)
    mydb_local.commit()
    mycursor_remote.execute(insert)
    mydb_remote.commit()

