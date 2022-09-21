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
   echo
   echo "You can run /home/sonata/apply_solutions.bash to apply the current"
   echo "solutions after running this script"
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

# eg: base=uvh5_59824_56671_93982116_3c147_0001
base=`pwd | rev | cut -f1 -d "/" | rev`

delayb=./delays_b.txt
phaseb=./phases_b.txt
delayc=./delays_c.txt
phasec=./phases_c.txt

lob=b
loc=c

cp /home/sonata/corr_data/scripts/concat_all_b.py .
cp /home/sonata/corr_data/scripts/concat_all_c.py .

python concat_all_b.py $base
python concat_all_c.py $base

uvh5_info_lob=`python /home/sonata/scripts/get_uvh5_info.py $base'_'$lob'.uvh5' -f -s`
uvh5_info_loc=`python /home/sonata/scripts/get_uvh5_info.py $base'_'$loc'.uvh5' -f -s`

freqb=`echo ${uvh5_info_lob} | cut -f1 -d " "`
freqc=`echo ${uvh5_info_loc} | cut -f1 -d " "`
source_name=`echo ${uvh5_info_lob} | cut -f2 -d " "`

# aoflagger + the whole casa script
aoflagger $base'_'$lob'.ms'
/home/sonata/src/casa-6.4.0-16/bin/casa --nogui --nologger -c ${casa_script} $base $lob
/home/sonata/scripts/calibrate.py --delay_table cal.$lob.K --bf_delays $delayb --phase_table cal.$lob.G --bandpass_table cal.$lob.BP --bf_phases $phaseb --cfreq $freqb

aoflagger $base'_'$loc'.ms' 
/home/sonata/src/casa-6.4.0-16/bin/casa --nogui --nologger -c ${casa_script} $base $loc
/home/sonata/scripts/calibrate.py --delay_table cal.$loc.K --bf_delays $delayc --phase_table cal.$loc.G --bandpass_table cal.$loc.BP --bf_phases $phasec --cfreq $freqc

# Produce the phase vs freq plots
montage -geometry +30+30 -tile 2x2 uvh5_*.png observation.png

# now let's do the SEFD / Tsys plots

flux_density_b=`python /home/ssheikh/Observing_Tools/flux_density_retriever_pb2017.py "${source_name^^}" ${freqb}`
flux_density_c=`python /home/ssheikh/Observing_Tools/flux_density_retriever_pb2017.py "${source_name^^}" ${freqc}`
echo "Flux density, LOb:" $flux_density_b "--- Skyfreq: " ${freqb} "GHz"
echo "Flux density, LOc:" $flux_density_c "--- Skyfreq: " ${freqc} "GHz"

/home/sonata/scripts/gain_plot.py cal.b.G --flux ${flux_density_b} --freq ${freqb} --lo b --wout weights_b.txt
/home/sonata/scripts/gain_plot.py cal.c.G --flux ${flux_density_c} --freq ${freqc} --lo c --wout weights_c.txt

montage -geometry +30+30 -tile 2x2 sefd_tsys_LOb.png sefd_tsys_LOc.png beamweights_LOb.png beamweights_LOc.png calibration.png
echo ""

# now create the antenna weight binary file for beamformer
/home/sonata/scripts/gain_list_to_weights.py weights_b.txt --weights_new weights_b.bin.new
/home/sonata/scripts/gain_list_to_weights.py weights_c.txt --weights_new weights_c.bin.new

echo "===================================================================="
echo "Script is done at this point!"
echo ""
echo "Now trying to plot the solutions."
echo "If this script never returned, and no plots are appearing, it's "
echo "probably either that your internet is bad, or X11 portforwarding is "
echo "broken. "
echo "In any case, you can safely ctrl-c me"
echo "===================================================================="

ret=`identify -format '%w %h' observation.png`
width=`echo $ret | cut -f1 -d " "`
height=`echo $ret | cut -f1 -d " "`
new_width=`echo "$width/2" | bc`
new_height=`echo "$height/2" | bc`
display -resize ${new_width}x${new_height} observation.png

ret=`identify -format '%w %h' calibration.png`
width=`echo $ret | cut -f1 -d " "`
height=`echo $ret | cut -f1 -d " "`
new_width=`echo "$width/2" | bc`
new_height=`echo "$height/2" | bc`
display -resize ${new_width}x${new_height} calibration.png
