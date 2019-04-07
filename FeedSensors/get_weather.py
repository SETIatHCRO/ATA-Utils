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

"""
7-Apr-19 9:44:11.520
Pressure (mb) = 678.40
InsideTemp (deg C) = 23.89
InsideHumidity (%) = 21.00
OutsideTemp (deg C) = 14.30
OutsideHumidity (%) = 51.00
WindSpeedAvg (mph) = 9.42
WindSpeedStd (mph) = 3.44
WindSpeedMax (mph) = 18.70
WindSpeedMin (mph) = 0.40
WindDirectionAvg (deg) = 162.60
RainRate (in / hr) = 0.00
Sunrise = 6:40
Sunset = 19:37
"""

proc = Popen(["ssh", "obs@tumulus", "ataweather -l"], stdout=PIPE, stderr=PIPE)
stdout, stderr = proc.communicate()
lines = stdout.split('\n')
insert = "insert into weather set ts=now(), "
for line in lines:
  parts = line.split()
  if "Pressure" in line:
    insert += 'pressure_mb=' + parts[3] + ', '
  if "InsideTemp" in line:
    insert += 'inside_temp_c=' + parts[4] + ', '
  if "InsideHumidity" in line:
    insert += 'inside_humidity_pct=' + parts[3] + ', '
  if "OutsideTemp" in line:
    insert += 'outside_temp_c=' + parts[4] + ', '
  if "OutsideHumidity" in line:
    insert += 'outside_humidity_pct=' + parts[3] + ', '
  if "WindSpeedAvg" in line:
    insert += 'windspeed_avg_mph=' + parts[3] + ', '
  if "WindSpeedStd" in line:
    insert += 'windspeed_std_mph=' + parts[3] + ', '
  if "WindSpeedMax" in line:
    insert += 'windspeed_max_mph=' + parts[3] + ', '
  if "WindSpeedMin" in line:
    insert += 'windspeed_min_mph=' + parts[3] + ', '
  if "WindDirectionAvg" in line:
    insert += 'windspeed_dir_avg_deg=' + parts[3] + ', '
  if "RainRate" in line:
    insert += 'rain_rate_in_hr=' + parts[5]

cmd = insert
print cmd
#proc = Popen(["echo", 'echo "' + cmd + ';"', "| mysql ants"], stdout=PIPE, stderr=PIPE)
#stdout, stderr = proc.communicate()
#print stdout

mydb =  mysql.connector.connect(
  host="localhost",
  user="sonata",
  database="ants"
)

mycursor = mydb.cursor()
mycursor.execute(cmd)
mydb.commit()

mydb =  mysql.connector.connect(
  host="googledb",
  user="jrseti",
  database="ants"
)

mycursor = mydb.cursor()
mycursor.execute(cmd)
mydb.commit()


