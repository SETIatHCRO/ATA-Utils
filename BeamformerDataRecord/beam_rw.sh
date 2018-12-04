#!/bin/sh
sudo hashpipe -o file=$2 -p ./beam_write beam_write_thread &
sudo hashpipe -o port=$1 -p ./beam_read beam_read_thread  
