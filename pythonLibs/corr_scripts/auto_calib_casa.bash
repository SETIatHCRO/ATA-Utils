#!/bin/bash

casa_script="/home/sonata/scripts/auto_casa_python.py"

Help()
{
   # Display Help
   echo "This script will automatically perform calibration on an"
   echo "observation with CASA, and will apply the solutions to the" 
   echo "current files running in the delay engine"
   echo
   echo "The 5 required inputs, in order:"
   echo "base:      The observation ID used for calibration (ex: uvh5_59646_25618_33731231_3c84_0001)"
   echo "lo:        The LO used (ex: b)"
   echo "delay:     Delays txt file currently running in the delay engine (ex: /home/sonata/corr_data/uvh5_59646_66358_34974517_3c84_0001/delays_b.txt)"
   echo "phase:     Phase txt file currently running in the delay engine (ex: /home/sonata/corr_data/uvh5_59646_66358_34974517_3c84_0001/phases_8500MHz.txt)"
   echo "freq:      Central Frequency of the LO in MHz (ex: 8500)"
   echo
}

while getopts ":h" option; do
   case $option in
      h) # display Help
         Help
         exit;;
   esac
done

if [ "$#" -ne 5 ]; then
    echo "============================="
    echo "WRONG NUMBER OF PARAMETERS!!!!"
    echo "============================="
    echo
    Help
    exit
fi

base=$1
lo=$2
delay=$3
phase=$4
freq=$5

echo $base'_'$lo'.ms'
aoflagger $base'_'$lo'.ms' 
/home/sonata/src/casa-6.4.0-16/bin/casa --nogui --nologger --nologfile -c ${casa_script} $base $lo
/home/sonata/corr_data/scripts/calibrate.py --delay_table cal.$lo.K --bf_delays $delay --phase_table cal.$lo.G --bandpass_table cal.$lo.BP --bf_phases $phase --cfreq $freq
