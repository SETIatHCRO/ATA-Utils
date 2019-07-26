#!/usr/bin/python3
import os
import sys
import serial

import threading

BAUD = 19200

sensors = 
        [ 
        { "name": "controller board temp", "cmd" : "gt a0", "value_type" : "float", "units" : "deg", "min_value" : 10.0, "max_value" : 100.0 },
        { "name": "outside air temp", "cmd" : "gt a1", "value_type" : "float", "units" : "deg", "min_value" : 10.0, "max_value" : 100.0 },
        { "name": "pax box air temp", "cmd" : "gt a2", "value_type" : "float", "units" : "deg", "min_value" : 10.0, "max_value" : 100.0 },
        { "name": "exhaust temp", "cmd" : "gt a3", "value_type" : "float", "units" : "deg", "min_value" : 10.0, "max_value" : 100.0 },
        { "name": "cooler rejection temp", "cmd" : "gt a5", "value_type" : "units" : "deg", "float", "min_value" : 10.0, "max_value" : 100.0 },
        { "name": "cooler housing temp", "cmd" : "gt a6", "value_type" : "units" : "deg", "float", "min_value" : 10.0, "max_value" : 100.0 },
        { "name": "turbo speed", "cmd" : "gt a1", "value_type" : "float", "units" : "deg", "min_value" : 10.0, "max_value" : 100.0 },
        { "name": "turbo popwer", "cmd" : "gt a1", "value_type" : "float", "units" : "watts", "min_value" : 10.0, "max_value" : 100.0 },
        { "name": "cryo temp", "cmd" : "TC", "value_type" : "float", "units" : "deg", "min_value" : 10.0, "max_value" : 100.0 },
        { "name": "lna temp", "cmd" : "gt a1", "value_type" : "float", "units" : "deg", "min_value" : 10.0, "max_value" : 100.0 },
        { "name": "24v", "cmd" : "gt a1", "value_type" : "float", "units" : "volts", "min_value" : 10.0, "max_value" : 100.0 },
        { "name": "48v", "cmd" : "gt a1", "value_type" : "float", "units" : "volts", "min_value" : 10.0, "max_value" : 100.0 },
        { "name": "fan speed", "cmd" : "gt a1", "value_type" : "int", "units" : "rpm", "min_value" : 2800.0, "max_value" : 3100.0 }
        ]

accel = { "cmd"    : "getaccel", 
          "sep"    : "|", 
          "axis"   : [ "x", "y", "z" ], 
          "fields" : [ "min", "max", "mean", "std" ],
          "min"    : { "min" : 0.0, "max" : 100.0 },
          "max"    : { "min" : 0.0, "max" : 100.0 },
          "mean"   : { "min" : 0.0, "max" : 100.0 },
          "std"    : { "min" : 0.0, "max" : 100.0 }
        }

if len(sys.argv) != 2:
    print("Syntax: %s <serial port file>" % sys.argv[0])
    sys.exit(0)
serial_port_file = sys.argv[1]
print("Opening %s at baud %d" % (serial_port_file, BAUD))

ser = serial.Serial(serial_port_file, baud, timeout=1)


# Gather the sensor information
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
    if value < min_malue || value > max_value:
        sensor['in_range'] = False
    
# Get the aaccelerometer info


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



