#!/bin/bash
basedir=/mnt/buf0/obs

locdir=$1
ant=$2

cd $locdir/$ant
pwd
echo "decimator entered $1 $2"

CMD="ls 202*.fil"
${CMD} #> $locdir/$ant/
retval=$?

file="202*.fil"
#${file} 

nsamps=`header 202*.fil | grep "Number of samples" | awk '{print $5}'`
#${nsamps}


if [ ${retval} -eq 0 ];               
then
    if [ -s ${file} ];
    then
        if [ ${nsamps} -ne 0 ];
        then
            the_decimator -b 8 -I 30 202*.fil -o decimated
            echo "WARNING: not downsampling data"
            mkdir decimator_output
            mv *.ts0 *.bps0 *.bp0 decimator_output
        else 
            echo "WARNING: Filterbank file for Antenna ${ant} has no samples"
        fi
    else
        echo "WARNING: Antenna ${ant} contains an empty filterbank file"
    fi
else 
    echo "WARNING: Antenna ${ant} has no filterbank file" 
fi
