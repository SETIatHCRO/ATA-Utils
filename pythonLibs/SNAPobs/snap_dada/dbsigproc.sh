#!/bin/bash

s=0
invert=0
while getopts D:ip: flag
do
    case "${flag}" in
        D) basedir=${OPTARG}; let s+=2 ;;
        i) invert=1; let s+=1 ;;
        p) npol=${OPTARG}; let s+=2 ;;
    esac
done

shift $s


NARGS=2
N=$#
for (( i=1;i<=N;i+=NARGS)); do 
    let ii=$i
    key=${!ii}
    let ii=$ii+1
    log=${!ii}

    if [ ${invert} == "1" ]; then
        flag="-i"
    else
        flag=""
    fi
    echo "ata_dbsigproc -v -k ${key} -s -p ${npol} -D ${basedir} ${flag} &>> ${log}"
    ata_dbsigproc -k ${key} -s -p ${npol} -D ${basedir} ${flag} &>> ${log} &
done
