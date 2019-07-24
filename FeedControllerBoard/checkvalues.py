#!/usr/bin/python3
import os
import sys
import serial

import threading

rs_test_mode = False
rs_test_error_count = 0
rs_test_total_bytes = 0

def read_serial_thread(ser):

    global rs_test_mode
    global rs_test_error_count
    global rs_test_total_bytes 

    print("read_serial_thread started...")

    while True:
        try:
            line = str(ser.readline(), 'ascii')
        except:
            continue;
        if len(line) > 0:
            print("%s" % line, end="")
            if rs_test_mode == True and line.startswith("rs") == False:
                if line.startswith("END"):
                    rs_test_mode = False
                    print("Test ended, errors=%d, total bytes=%d" % (rs_test_error_count, rs_test_total_bytes))
                    #sys.exit(0)
                else:
                    #print("len=%d, %s" % (len(line), line[:0]))
                    if len(line) != 12 or line[:10] != "0123456789":
                        rs_test_error_count += 1;
                    rs_test_total_bytes += len(line)
                    



if len(sys.argv) != 3:
    print("Syntax: %s <serial port file> <baud>" % sys.argv[0])
    sys.exit(0)

serial_port_file = sys.argv[1]
baud = int(sys.argv[2])

print("Opening %s at baud %d" % (serial_port_file, baud))

ser = serial.Serial(serial_port_file, baud, timeout=1)

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



