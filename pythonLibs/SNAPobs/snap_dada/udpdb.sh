#!/bin/bash
# example: frb-snap1 sandbox1 4015 1 /some/header/file.txt dada /some/log/file.log

NARGS=7
N=$#
# future me, I'm sorry...
for (( i=1;i<=N;i+=NARGS)); do 
    let ii=$i
    snap_name=${!ii}
    let ii=$ii+1
    rxhost=${!ii}
    let ii=$ii+1
    rxport=${!ii}
    let ii=$ii+1
    cpucore=${!ii}
    let ii=$ii+1
    headerfile=${!ii}
    let ii=$ii+1
    key=${!ii}
    let ii=$ii+1
    log=${!ii}

    echo "numactl -C ${cpucore} ata_udpdb ${headerfile} -p ${rxport} -k ${key} -i ${rxhost} &>> ${log}" 
    numactl -C ${cpucore} ata_udpdb ${headerfile} -p ${rxport} -k ${key} -i ${rxhost} &>> ${log} &
done
