#!/bin/bash

N=$#
for (( i=1;i<=N;i+=2)); do
    let ii=$i+1
    key=${!i}
    bufsze=${!ii}
    dada_db -k $key -b $bufsze
done
