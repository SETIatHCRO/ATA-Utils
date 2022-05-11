#!/home/sonata/miniconda3/envs/cfpga3/bin/python
from __future__ import print_function
import casperfpga
import sys
import time
import numpy as np
import argparse

def wait_until(utime):
    while time.time() < utime:
        time.sleep(0.05)

def main():
    parser = argparse.ArgumentParser(description="Synchronise FPGA")
    parser.add_argument("snaps", nargs="?", help="snaps hostname")
    args = parser.parse_args()

    snap_list = args.snaps
    if not snap_list:
        snap_list = ['frb-snap%i-pi'%i for i in [4]] #[3,4,5,6,8,9,10]]
    snaps = [casperfpga.CasperFpga(snap, transport=casperfpga.KatcpTransport) 
            for snap in snap_list]

    # Disable ethernet output
    for snap in snaps:
        snap.write_int("tge_en", 0)
        snap.write_int("tge_rst", 1)
        snap.write_int("tge_ctr_rst", 1)

    #grace_period = 4
    #unix_time_start = time.time() + grace_period
    #expected_synctime = int(np.ceil(unix_time_start)) + 2
    #print expected_synctime
    #time.sleep(1)
    #wait_until_time(unix_time_start-1)

    current_sync = snaps[0].read_int("sync_count")
    time.sleep(0.05)
    while(snaps[0].read_int("sync_count") == current_sync):
        time.sleep(0.05)

    for i,snap in enumerate(snaps):
        print(snap_list[i], snap.read_int("sync_count"))

    sync_time = int(np.ceil(time.time())) + 2 # Number of seconds for sync is det rmined by design
    print("  PPS passed! New sync time will be %d" % sync_time)
    for snap in snaps:
        snap.write_int("sync_arm", 1)
        snap.write_int("sync_arm", 0)
        print ("  Writing new sync time to snap memory")
        snap.write_int("sync_sync_time", sync_time)


    for snap in snaps:
        snap.write_int("tge_rst", 0)
        snap.write_int("tge_ctr_rst", 0)
        snap.write_int("tge_en", 1)


    # disconnect snaps
    #for snap in snaps:
    #    snap.disconnect()

if __name__ == "__main__":
   main()
