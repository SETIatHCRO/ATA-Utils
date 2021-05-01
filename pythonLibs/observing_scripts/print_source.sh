#!/bin/bash

for f in /mnt/buf0/obs/2020-06-03-2*/*/*.fil
do
#    ~/software/bl_sigproc/src/header $f | grep "Source Name"
    ~/software/bl_sigproc/src/header $f | grep "Frequency of channel 1"
done
