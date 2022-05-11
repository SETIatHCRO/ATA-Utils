#!/bin/bash
numactl -C 8 ata_udpdb ./obs.header -p 4015 -k d0d0 -i 10.11.1.151 &>> /home/obsuser/log/udpdb_frb-snap1-pi.log
