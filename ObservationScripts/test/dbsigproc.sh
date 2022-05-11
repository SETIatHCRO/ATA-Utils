#!/bin/bash
numactl -C 4 ata_dbsigproc -k d0d0 -s -p 1 -D ./ -i -m &>> /home/obsuser/log/dbsigproc_frb-snap1-pi.log
