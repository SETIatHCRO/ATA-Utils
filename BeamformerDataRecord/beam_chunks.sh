#!/bin/sh
sudo hashpipe -o output_dir=$2 -o filename_prefix=$3 -o output_port=$4 -p ./beam_chunks beam_chunks_thread &
sudo hashpipe -o port=$1 -p ./beam_read beam_read_thread  
