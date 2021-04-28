#!/home/sonata/miniconda3/envs/cfpga/bin/python
import casperfpga
import sys
import time
import numpy as np
import argparse

def main():
    parser = argparse.ArgumentParser(description="Stop FPGAs ethernet output")
    parser.add_argument("snaps", nargs="?", help="snaps hostname")
    args = parser.parse_args()

    snap_list = args.snaps
    if not snap_list:
        snap_list = ['frb-snap%i-pi'%i for i in [1,2, 3,4,5,6,8,9,10]]
    snaps = [casperfpga.CasperFpga(snap, 
        transport=casperfpga.KatcpTransport) for snap in snap_list]

    for i,snap in enumerate(snaps):
        snap.write_int("tge_en", 0)

if __name__ == "__main__":
    main()
