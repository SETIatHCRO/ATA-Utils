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

mydb =  mysql.connector.connect(
  host="localhost",
  user="sonata",
  database="ants"
)
mycursor = mydb.cursor()

# Create a list of viable atennas. Use ataasciistatus to get a list of viable ant,
# weed out the ones without valid PaxBoxTemps
antlist = []
proc = Popen(["ssh", "obs@tumulus", "ataasciistatus -l"], stdout=PIPE, stderr=PIPE)
stdout, stderr = proc.communicate()
lines = stdout.split('\n')
for line in lines:
  if line.startswith("ant"):
    parts = line.split()
    ant = parts[0][3:]
    #print parts[7]
    try:
        float(parts[7])
    except ValueError:
        #print "SKIP Not a working ant"
        continue
    mycursor.execute('select sn from feed_sn where sn<>"" and ant="' + ant + '"' );
    for result in mycursor:
        sn = result[0]
        antlist.append((ant, sn))

#print antlist

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


# Get the LNA values of each ant
for antinfo in antlist:
    ant = antinfo[0]
    sn = antinfo[1]
    print ant + ", " + sn
    proc = Popen(["ssh", "obs@tumulus", "atagetlnas " + ant], stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    # ['X-pol:', '  vg 0.25', '  vd 1.5', '  vm -0.8', '  id 60.5', 'Y-pol:', '  vg 0.46', '  vd 1.49', '  vm -0.8', '  id 59.9', '']
    lines = stdout.split('\n')
    print lines
    insert = "insert into lna_values set ts=CONVERT_TZ(now(),'UTC','America/Los_Angeles'), sn='" + sn + "'";
    if len(lines) == 11:
        x_vg = lines[1].strip().split()[1]
        x_vd = lines[2].strip().split()[1]
        x_vm = lines[3].strip().split()[1]
        x_id = lines[4].strip().split()[1]
        y_vg = lines[6].strip().split()[1]
        y_vd = lines[7].strip().split()[1]
        y_vm = lines[8].strip().split()[1]
        y_id = lines[9].strip().split()[1]
        insert += ", x_vg=" + x_vg
        insert += ", x_vd=" + x_vd
        insert += ", x_vm=" + x_vm
        insert += ", x_id=" + x_id
        insert += ", y_vg=" + y_vg
        insert += ", y_vd=" + y_vd
        insert += ", y_vm=" + y_vm
        insert += ", y_id=" + y_id
    print insert
    mycursor_local.execute(insert)
    mydb_local.commit()
    
    mycursor_remote.execute(insert)
    mydb_remote.commit()

