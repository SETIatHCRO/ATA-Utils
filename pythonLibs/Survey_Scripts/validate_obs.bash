#!/bin/bash

casa_script="/home/sonata/scripts/validate_casa_python.py"

Help()
{
   # Display Help
   echo "This script will validate the existing solution by displaying"
   echo "the montage image of the phases as a function of frequency"
   echo ""
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
freqb=`python -c "from ATATools import ata_control; print(ata_control.get_sky_freq('b'))"` #$2
freqc=`python -c "from ATATools import ata_control; print(ata_control.get_sky_freq('c'))"` #$3

delayb=/opt/mnt/share/delays_b.txt
phaseb=/opt/mnt/share/phases_b.txt
delayc=/opt/mnt/share/delays_c.txt
phasec=/opt/mnt/share/phases_c.txt

lob=b
loc=c

cp /home/sonata/corr_data/scripts/concat_all_b.py .
cp /home/sonata/corr_data/scripts/concat_all_c.py .

python concat_all_b.py $base
python concat_all_c.py $base

/home/sonata/src/casa-6.4.0-16/bin/casa --nogui --nologger --nologfile -c ${casa_script} $base $lob

/home/sonata/src/casa-6.4.0-16/bin/casa --nogui --nologger --nologfile -c ${casa_script} $base $loc

montage -geometry +30+30 -tile 2x2 *.png observation.png
display observation.png
