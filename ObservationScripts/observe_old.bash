#!/bin/bash

obs_time=1200
#BASEOUTDIR=/mnt/buf0/Magnetar
BASEOUTDIR=/mnt/buf0/obs
#BASEOUTDIR=/home/sonata/data/J1935

counter=1
nobs=1

while [ $counter -le $nobs ]
do
    date_now=`TZ=America/Los_Angeles date +"%F-%H:%M:%S"`
    outdir=${BASEOUTDIR}/${date_now}
    mkdir ${outdir}
    logfile=${outdir}/obs.log

    echo "New observation: date: ${date_now}, obs no: ${counter}"

    ssh obs@tumulus 'atagetradec 1a,1f,1c,2a,2b,2h,4g,5c' &>> ${outdir}/obs.pointing
    echo "Sky frequency: " &> ${outdir}/obs.info
    ssh obs@tumulus 'atagetskyfreq a' &>> ${outdir}/obs.info
    echo "atagetfocus: " &>> ${outdir}/obs.info
    ssh obs@tumulus 'atagetfocus 1a,1f,1c,2a,2b,2h,4g,5c' &>> ${outdir}/obs.info
    echo "output of python ./attenuatorMain.py -g: " >> ${outdir}/obs.atten
    ssh gain-module1 'python ./attenuatorMain.py -g' &>> ${outdir}/obs.atten

    echo "Create buffer"
    ./create_buf.sh &>> ${logfile}
    echo "Running capture code"
    ./do_incoherent_sum.sh &>> ${logfile}
    echo "Running dbdisk"
    ./dbdisk.sh ${outdir} &>> ${logfile}
    sleep 1
    echo "syncing FPGA"
    ./sync_fpgas.py >> ${outdir}/obs.info
    echo "Done"
    
    sleep ${obs_time} 

    ./stop_fpgas.py &>> ${logfile}
    sleep 1 
    ./kill_all.sh &>> ${logfile}
    ./destroy_buf.sh &>> ${logfile}
    touch ${outdir}/obs.finished
    let counter+=1
done
