#!/bin/bash

casa_script="/home/sonata/scripts/auto_casa_python.py"

Help()
{
   # Display Help
   echo "This script will automatically perform calibration on an"
   echo "observation with CASA, and will apply the solutions to the" 
   echo "current files running in the delay engine"
   echo ""
   echo "The files are located in /opt/mnt/share"
   echo "Note that this script produces .new files [ex: delays_b.txt.new]"
#   echo "The 3 required inputs, in order:"
#   echo "base:      The observation ID used for calibration [ex: uvh5_59646_25618_33731231_3c84_0001]"
#   echo "lo:        The LO used [ex: b]"
#   echo "delay:     Delays txt file currently running in the delay engine [ex: /home/sonata/corr_data/uvh5_59646_66358_34974517_3c84_0001/delays_b.txt]"
#   echo "phase:     Phase txt file currently running in the delay engine [ex: /home/sonata/corr_data/uvh5_59646_66358_34974517_3c84_0001/phases_8500MHz.txt]"
#   echo "freqb:      Central Frequency of the LOb in MHz [ex: 8500]"
#   echo "freqc:      Central Frequency of the LOc in MHz [ex: 6500]"
   echo
}

while getopts ":h" option; do
   case $option in
      h) # display Help
         Help
         exit;;
   esac
done

if [ "$#" -ne 0 ]; then
    echo "============================="
    echo "WRONG NUMBER OF PARAMETERS!!!!"
    echo "============================="
    echo
    Help
    exit
fi

base=`pwd | rev | cut -f1 -d "/" | rev` #$1
#lo=$2
#delay=/opt/mnt/share/delays_$2.txt
#phase=/opt/mnt/share/phases_$2.txt
freqb=`python -c "from ATATools import ata_control; print(ata_control.get_sky_freq('b'))"` #$2
freqc=`python -c "from ATATools import ata_control; print(ata_control.get_sky_freq('c'))"` #$3

delayb=/opt/mnt/share/delays_b.txt
phaseb=/opt/mnt/share/phases_b.txt
delayc=/opt/mnt/share/delays_c.txt
phasec=/opt/mnt/share/phases_c.txt

lob=b
loc=c
#echo $base'_'$lo'.ms'
#aoflagger $base'_'$lo'.ms' 

#/home/sonata/src/casa-6.4.0-16/bin/casa --nogui --nologger --nologfile -c ${casa_script} $base $lo
#/home/sonata/corr_data/scripts/calibrate.py --delay_table cal.$lo.K --bf_delays $delay --phase_table cal.$lo.G --bandpass_table cal.$lo.BP --bf_phases $phase --cfreq $freq

cp /home/sonata/corr_data/scripts/concat_all_b.py .
cp /home/sonata/corr_data/scripts/concat_all_c.py .

python concat_all_b.py $base
python concat_all_c.py $base

aoflagger $base'_'$lob'.ms'
/home/sonata/src/casa-6.4.0-16/bin/casa --nogui --nologger --nologfile -c ${casa_script} $base $lob
/home/sonata/corr_data/scripts/calibrate.py --delay_table cal.$lob.K --bf_delays $delayb --phase_table cal.$lob.G --bandpass_table cal.$lob.BP --bf_phases $phaseb --cfreq $freqb

aoflagger $base'_'$loc'.ms' 
/home/sonata/src/casa-6.4.0-16/bin/casa --nogui --nologger --nologfile -c ${casa_script} $base $loc
/home/sonata/corr_data/scripts/calibrate.py --delay_table cal.$loc.K --bf_delays $delayc --phase_table cal.$loc.G --bandpass_table cal.$loc.BP --bf_phases $phasec --cfreq $freqc
