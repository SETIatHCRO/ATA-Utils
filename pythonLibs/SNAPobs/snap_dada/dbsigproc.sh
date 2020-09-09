#!/bin/bash

s=0
invert=0
disable_rfi=0
while getopts D:ip:m flag
do
    case "${flag}" in
        D) basedir=${OPTARG}; let s+=2 ;;
        i) invert=1; let s+=1 ;;
        p) npol=${OPTARG}; let s+=2 ;;
        m) disable_rfi=1; let s+=1
    esac
done

shift $s


NARGS=3
N=$#
for (( i=1;i<=N;i+=NARGS)); do 
    let ii=$i
    core=${!ii}
    let ii=$ii+1
    key=${!ii}
    let ii=$ii+1
    log=${!ii}

    if [ ${invert} == "1" ]; then
        flag="-i"
    else
        flag=""
    fi

    if [ ${disable_rfi} == "1" ]; then
        flag="${flag} -m"
    fi

    echo "numactl -C ${core} ata_dbsigproc -v -k ${key} -s -p ${npol} -D ${basedir} ${flag} &>> ${log}"
    numactl -C ${core} ata_dbsigproc -k ${key} -s -p ${npol} -D ${basedir} ${flag} &>> ${log} &
done
