#!/bin/bash


NARGS=1
N=$#
for (( i=1;i<=N;i+=NARGS)); do 
    let ii=$i
    key=${!ii}
    
    echo "dada_dbnull -k ${key} -s -z -d"
    dada_dbnull -k ${key} -s -z -d
done
