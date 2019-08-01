#!/usr/bin/python3
import os
import sys
import serial

import threading

BAUD = 19200

# https://github.com/SETIatHCRO/antonio-feed-controller-board/blob/master/manuals/ATA%20Cooled%20Feed%20Manual%20Control%20Commands%20Ver%205a.pdf
# https://github.com/SETIatHCRO/antonio-feed-controller-board/blob/master/antonio-feed-control-v2.X/commands.c
sensors = [ 
        { "name": "controller board temp", "cmd" : "gt a0", "value_type" : "float", "units" : "deg", "min_value" : 10.0, "max_value" : 45.0 },
        { "name": "outside air temp", "cmd" : "gt a1", "value_type" : "float", "units" : "deg", "min_value" : 10.0, "max_value" : 45.0 },
        { "name": "pax box air temp", "cmd" : "gt a2", "value_type" : "float", "units" : "deg", "min_value" : 10.0, "max_value" : 45.0 },
        { "name": "exhaust temp", "cmd" : "gt a3", "value_type" : "float", "units" : "deg", "min_value" : 10.0, "max_value" : 45.0 },
        { "name": "cooler rejection temp", "cmd" : "gt a5", "value_type" : "float",  "units" : "deg", "min_value" : 10.0, "max_value" : 45.0 },
        { "name": "cooler housing temp", "cmd" : "gt a6", "value_type" : "float", "units" : "deg", "min_value" : 10.0, "max_value" : 45.0 },
        { "name": "turbo speed", "cmd" : "p398", "value_type" : "int", "units" : "rpm", "min_value" : 89900, "max_value" : 90600 },
        { "name": "turbo power", "cmd" : "p316", "value_type" : "int", "units" : "watts", "min_value" : 4.0, "max_value" : 20.0 },
        { "name": "cryo temp", "cmd" : "TC", "value_type" : "float", "units" : "deg", "min_value" : 64.0, "max_value" : 66.0 },
        { "name": "lna temp", "cmd" : "gd", "value_type" : "float", "units" : "deg", "min_value" : 65.0, "max_value" : 80.0 },
        { "name": "24v", "cmd" : "get24v", "value_type" : "float", "units" : "volts", "min_value" : 23.8, "max_value" : 24.2 },
        { "name": "48v", "cmd" : "get48v", "value_type" : "float", "units" : "volts", "min_value" : 47.8, "max_value" : 48.2 },
        { "name": "fan speed", "cmd" : "gt a1", "value_type" : "int", "units" : "rpm", "min_value" : 2800.0, "max_value" : 3100.0 }
        ]

accel = { "cmd"    : "getaccel", 
          "sep"    : "|", 
          "axis"   : [ "x", "y", "z" ], 
          "fields" : [ "min", "mean", "std", "max" ]
        }

"""
Define the tolerances for the accelerator values. They are different for each axis.
These values were obtained by reviewing the accelerometer values of the 10 that
are installed at the ATA as of July 26, 2019. Note that 4j is reporting bad values,
so its vales were ignored for this purpose.

mysql> select ts,ant, accelminx,accelmeanx,accelstdx,accelmaxx from feed_sensors where (ant='1h' or ant='2e' or ant='2j' or ant='4j' or ant='1k' or ant='5b' or ant='1g' or ant='2a' or ant='2b' or ant='3l') order by ts DESC limit 10;
+---------------------+-----+-----------+------------+-----------+-----------+
| ts                  | ant | accelminx | accelmeanx | accelstdx | accelmaxx |
+---------------------+-----+-----------+------------+-----------+-----------+
| 2019-07-26 09:00:21 | 5b  |    -0.854 |     -0.823 |     0.008 |     -0.79 |
| 2019-07-26 09:00:21 | 4j  |        99 |          0 |         0 |       -99 |
| 2019-07-26 09:00:21 | 3l  |    -0.888 |     -0.855 |     0.012 |    -0.826 |
| 2019-07-26 09:00:21 | 2j  |    -0.924 |     -0.856 |      0.03 |    -0.792 |
| 2019-07-26 09:00:21 | 2e  |    -0.942 |     -0.875 |     0.027 |    -0.816 |
| 2019-07-26 09:00:21 | 2b  |    -0.884 |      -0.84 |     0.009 |      -0.8 |
| 2019-07-26 09:00:21 | 2a  |    -0.874 |     -0.854 |     0.004 |    -0.836 |
| 2019-07-26 09:00:21 | 1k  |    -0.888 |      -0.85 |     0.009 |    -0.816 |
| 2019-07-26 09:00:21 | 1h  |    -0.856 |     -0.813 |     0.011 |    -0.762 |
| 2019-07-26 09:00:21 | 1g  |     -0.92 |     -0.871 |     0.011 |     -0.83 |
+---------------------+-----+-----------+------------+-----------+-----------+
10 rows in set (0.00 sec)

mysql> select ts,ant, accelminy,accelmeany,accelstdy,accelmaxy from feed_sensors where (ant='1h' or ant='2e' or ant='2j' or ant='4j' or ant='1k' or ant='5b' or ant='1g' or ant='2a' or ant='2b' or ant='3l') order by ts DESC limit 10;
+---------------------+-----+-----------+------------+-----------+-----------+
| ts                  | ant | accelminy | accelmeany | accelstdy | accelmaxy |
+---------------------+-----+-----------+------------+-----------+-----------+
| 2019-07-26 09:00:21 | 5b  |    -0.062 |     -0.023 |     0.008 |      0.02 |
| 2019-07-26 09:00:21 | 4j  |        99 |          0 |         0 |       -99 |
| 2019-07-26 09:00:21 | 3l  |    -0.102 |      0.015 |     0.072 |     0.136 |
| 2019-07-26 09:00:21 | 2j  |    -0.022 |      0.016 |      0.01 |     0.054 |
| 2019-07-26 09:00:21 | 2e  |    -0.176 |     -0.024 |      0.09 |     0.132 |
| 2019-07-26 09:00:21 | 2b  |    -0.064 |     -0.017 |     0.013 |     0.034 |
| 2019-07-26 09:00:21 | 2a  |     -0.04 |      0.006 |      0.02 |     0.054 |
| 2019-07-26 09:00:21 | 1k  |    -0.166 |      0.003 |     0.094 |     0.194 |
| 2019-07-26 09:00:21 | 1h  |    -0.104 |      0.033 |      0.07 |     0.178 |
| 2019-07-26 09:00:21 | 1g  |    -0.124 |     -0.037 |     0.036 |     0.052 |
+---------------------+-----+-----------+------------+-----------+-----------+
10 rows in set (0.00 sec)

mysql> select ts,ant, accelminz,accelmeanz,accelstdz,accelmaxz from feed_sensors where (ant='1h' or ant='2e' or ant='2j' or ant='4j' or ant='1k' or ant='5b' or ant='1g' or ant='2a' or ant='2b' or ant='3l') order by ts DESC limit 10;
+---------------------+-----+-----------+------------+-----------+-----------+
| ts                  | ant | accelminz | accelmeanz | accelstdz | accelmaxz |
+---------------------+-----+-----------+------------+-----------+-----------+
| 2019-07-26 09:14:21 | 5b  |      0.56 |      0.605 |     0.013 |     0.644 |
| 2019-07-26 09:14:21 | 4j  |        99 |          0 |         0 |       -99 |
| 2019-07-26 09:14:21 | 3l  |     0.484 |       0.59 |     0.058 |     0.694 |
| 2019-07-26 09:14:21 | 2j  |      0.54 |      0.591 |     0.023 |     0.648 |
| 2019-07-26 09:14:21 | 2e  |     0.516 |      0.607 |     0.047 |     0.698 |
| 2019-07-26 09:14:21 | 2b  |     0.538 |      0.586 |     0.013 |     0.638 |
| 2019-07-26 09:14:21 | 2a  |      0.57 |      0.605 |     0.013 |     0.638 |
| 2019-07-26 09:14:21 | 1k  |     0.486 |      0.601 |     0.063 |     0.708 |
| 2019-07-26 09:14:21 | 1h  |     0.486 |      0.603 |      0.06 |      0.71 |
| 2019-07-26 09:14:21 | 1g  |     0.508 |      0.597 |     0.043 |     0.682 |
+---------------------+-----+-----------+------------+-----------+-----------+
10 rows in set (0.00 sec)

"""
accel_values = { "x" : { "min" : { "min" : -5.0, "max" : 5.0 },
                      "max" : { "min" : -5.0, "max" : 5.0 },
                      "mean": { "min" : -5.0, "max" : 5.0 },
                      "std" : { "min" :  0.001, "max" : 0.12 } },
              "y" : { "min" : { "min" : -5.0, "max" : 5.0 },
                      "max" : { "min" : -5.0, "max" : 5.0 },
                      "mean": { "min" : -5.0, "max" : 5.0 },
                      "std" : { "min" :  0.001, "max" : 0.12 } },
              "z" : { "min" : { "min" : -5.0, "max" : 5.0 },
                      "max" : { "min" : -5.0, "max" : 5.0 },
                      "mean": { "min" : -5.0, "max" : 5.0 },
                      "std" : { "min" :  0.001, "max" : 0.12 } }
              }

def pad_string(string, max_len, center=False):
    new_string = string
    length = len(new_string)
    while length < max_len:
        new_string += " "
        length = len(new_string)

    if center:
        trailing_spaces_count = 0;
        i = len(new_string) - 1
        while new_string[i] == ' ':
            i -= 1
        num_spaces = len(new_string) - i
        i = 0;
        new_string = ""
        while i < num_spaces/2:
            new_string += " ";
            i += 1
        new_string += string
        i = 0
        while i < num_spaces/2:
            new_string += " "
            i += 1

    return new_string[0:max_len]

def print_help():

    print("")
    print("Syntax: %s <serial port file>" % sys.argv[0])
    print("")
    print("Sensor values measured, and tolerances:")
    print("")
    print("| %s|%s|%s|%s|" % (pad_string("Sensor", 22, True), pad_string("Units", 8, True), pad_string("max", 10, True), pad_string("min", 10, True)))

    for sensor in sensors:
        name = pad_string(sensor['name'], 22)
        units = pad_string(sensor['units'], 8, True)
        max_value = pad_string(str(sensor['max_value']), 10, True)
        min_value = pad_string(str(sensor['min_value']), 10, True)
        print("| %s|%s|%s|%s|" % (name, units, min_value, max_value))
    print("")
    print("Accelerometer values:")
    print("")
    print("|%s|%s|%s|%s|" % (pad_string("axis",7,True), pad_string("Field", 7, True), pad_string("Min", 8, True), pad_string("Max", 8, True)))
    for axis in accel['axis']:
        for field in accel["fields"]:
            print("|%s|%s|%s|%s|" % (pad_string(axis,7, True), pad_string(field,7,True), pad_string(str(accel_values[axis][field]["min"]),8,True), pad_string(str(accel_values[axis][field]["max"]), 8,True)))
    print("")


if len(sys.argv) != 2:
    print_help()
    exit(0)

def check_accel_value_within_range(axis, field, value):

    min_value = accel_values[axis][field]["min"];
    max_value = accel_values[axis][field]["max"];

    if value < min_value or value > max_value:
        return False

    return True


# -1.250  -1.045   0.036  -0.840|-0.250  -0.027   0.104   0.186|-0.242  -0.107   0.057   0.038
def  accel_parse(line):

    sep = accel['sep']
    parts = line.split(sep)
    parts_x = parts[0].split()
    parts_y = parts[1].split()
    parts_z = parts[2].split()
    values_x = [ float(parts_x[0]), float(parts_x[1]), float(parts_x[2]), float(parts_x[3]) ]
    values_y = [ float(parts_y[0]), float(parts_y[1]), float(parts_y[2]), float(parts_y[3]) ]
    values_z = [ float(parts_z[0]), float(parts_z[1]), float(parts_z[2]), float(parts_z[3]) ]
    values = { "x" : values_x, "y" : values_y, "z" : values_z }
    i = 0
    for field in accel["fields"]:
        in_range = check_accel_value_within_range('x', field, values_x[i])
        accel_values["x"][field]["value"] = values_x[i]
        accel_values["x"][field]["in_range"] = in_range

        in_range = check_accel_value_within_range('y', field, values_y[i])
        accel_values["y"][field]["value"] = values_y[i]
        accel_values["y"][field]["in_range"] = in_range

        in_range = check_accel_value_within_range('z', field, values_z[i])
        accel_values["z"][field]["value"] = values_z[i]
        accel_values["z"][field]["in_range"] = in_range

        i += 1

    all_good = True
    print("")
    print("Accelerometer values:")
    print("")
    print("|%s|%s|%s|%s|%s|%s|" % (pad_string("axis",7,True), pad_string("Field", 7, True), pad_string("Min", 8, True), pad_string("Max", 8, True), pad_string("Value", 8, True), pad_string("In Range", 12, True)))
    for axis in accel['axis']:
        for field in accel["fields"]:
            print("|%s|%s|%s|%s|%s|%s|" % (pad_string(axis,7, True), pad_string(field,7,True), pad_string(str(accel_values[axis][field]["min"]),8,True), pad_string(str(accel_values[axis][field]["max"]), 8,True), pad_string(str(accel_values[axis][field]["value"]),8,True), pad_string(str(accel_values[axis][field]["in_range"]),12,True)))
            if accel_values[axis][field]["in_range"] == False:
                all_good = True

    print("")
    if not all_good:
        print("FAIL - Some accerometer values not within range!!")
        return
    print("PASS - All accelerometer values within range")
    print("")

    return

if sys.argv[1] == "test":
    line = "-1.250  -1.045   0.036  -0.840|-0.250  -0.027   0.104   0.186|-0.242  -0.107   0.057   0.038"
    print(line)
    accel_parse(line)
    exit(0)

serial_port_file = sys.argv[1]
print("Opening %s at baud %d" % (serial_port_file, BAUD))
ser = serial.Serial(serial_port_file, baud, timeout=1)

# Query the sensor values and find if in range
all_sensors_good = True
for sensor in sensors:
    cmd = sensor['cmd'] + "\n"
    ser.write(cmd.encode())
    line = str(ser.readline(), 'ascii')
    value_type = sensor['value_type']
    value  = None
    if value_type == 'float':
        value = float(line)
    if value_type == 'int':
        value = int(line)
    min_value = sensor['min_value']
    max_value = sensor['min_value']
    sensor['in_range'] = True
    if value < min_value or value > max_value:
        all_sensors_good = False
        sensor['in_range'] = False

print("")
print("| %s|%s|%s|%s|%s|%s|" % (pad_string("Sensor", 22, True), pad_string("Units", 8, True), pad_string("max", 10, True), pad_string("min", 10, True), pad_string("Value", 8, True), pad_string("In Range", 12, True)))

for sensor in sensors:
    name = pad_string(sensor['name'], 22)
    units = pad_string(sensor['units'], 8, True)
    max_value = pad_string(str(sensor['max_value']), 10, True)
    min_value = pad_string(str(sensor['min_value']), 10, True)
    value = pad_string(str(sensor['value']), 8, True)
    in_range = pad_string(str(sensor['in_range']), 12, True)
    print("| %s|%s|%s|%s|%s|%s|" % (name, units, min_value, max_value, value, in_range))

if not all_sensors_good:
    print("FAIL - Some values not within range!!")
else:
    print("PASS - All sensor values within range")
    
# Get the aaccelerometer values
cmd = accel['cmd']
ser.write(cmd.encode())
line = str(ser.readline(), 'ascii')
accel_parse(line)



line = str(ser.readline(), 'ascii')
t = threading.Thread(target=read_serial_thread, args=(ser,))
t.daemon = True
t.start()


while True:

    line = input("") + "\r\n"
    #print(line)
    if line.startswith("rs"):
        rs_test_mode = True
        rs_test_error_count = 0
        rs_test_total_bytes = 0
    ser.write(line.encode())
    #print("Len=%d" % len(line.encode()))



