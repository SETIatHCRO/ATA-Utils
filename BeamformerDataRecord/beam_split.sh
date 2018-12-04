#!/bin/sh
sudo hashpipe -o ip1=$2 -o port1=$3 -o ip2=$4 -o port2=$5  -o p2_decimante=$6 -p ./beam_split beam_split_thread &
#sudo hashpipe -o ip1=$2 -p ./beam_split beam_split_thread &
sudo hashpipe -o port=$1 -p ./beam_read beam_read_thread  
