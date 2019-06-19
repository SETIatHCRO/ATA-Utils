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
    #ant5h  Running  AzEl        180.00,18.00  0.00,-0.00   
    #parts = line[55:-1].split()
    parts = line[len("ant1a  Running  AzEl    180.00,18.00  -0.00,0.00   "):-1].split()
    ant = line.split()[0][3:]
    insert = "INSERT into dish_temp_sensors set ts=now(), ant='" + ant + "'"
    try:
        temp = float(parts[0])
        insert += ", control_box_temp=" + parts[0]
    except ValueError:
        pass
    try:
        temp = float(parts[1])
        insert += ", drive_box_temp=" + parts[1]
    except ValueError:
        pass
    try:
        temp = float(parts[2])
        insert += ", pax_box_temp=" + parts[2]
    except ValueError:
        pass
    try:
        print len(parts)
        if len(parts) > 3:
          temp = float(parts[3])
          insert += ", rim_box_temp=" + parts[3]
    except ValueError:
        pass

    print insert

    #sys.exit(0)

    mycursor_local.execute(insert)
    mydb_local.commit()
    mycursor_remote.execute(insert)
    mydb_remote.commit()

