#!/bin/bash

basedir='/mnt/netStorage-40G/obs'
#basedir='/mnt/buf0/obs'
ant='2a'

for utc in `ls $basedir`
do
    if [ "$(ls -A $basedir/$utc)" ]; then
        if [ "$(ls -A $basedir/$utc/$ant)" ]; then
            filfile=`ls $basedir/$utc/$ant/*_x.fil`
            freq=`~/software/bl_sigproc/src/header $filfile | grep Frequency | rev | awk '{print $1}' | rev`
            source_name=`~/software/bl_sigproc/src/header $filfile | grep "Source Name" | rev | awk '{print $1}' | rev`
            #tobs=`~/software/bl_sigproc/src/header $filfile | grep "Observation length" | rev | awk '{print $1}' | rev`
            tobs=`~/software/bl_sigproc/src/header $filfile | grep "Observation length"`
            echo $utc $source_name $freq $tobs
        else
            echo "$utc has no $ant"
        fi
    else
        echo "$utc is empty..."
    fi

done
