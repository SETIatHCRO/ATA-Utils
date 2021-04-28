#!/bin/bash

n=3
i=0

while [ $i -le $n ]
do
    ./observe_onoff.py 1000 4000 500
    ./observe_onoff.py 4000 8000 500
    ./observe_onoff.py 8000 11000 500
    i=$[$i+1]
done

./observe.py


n=3
i=0

while [ $i -le $n ]
do
    ./observe_onoff.py 1000 4000 500
    ./observe_onoff.py 4000 8000 500
    ./observe_onoff.py 8000 11000 500
    i=$[$i+1]
done
