#!/bin/bash

#basedir="/home/sonata/corr_data/uvh5_multisource_azel/uvh5*"
basedir="uvh5*"
casa_script="/home/sonata/scripts/casa_python_script.py"

for dir in $basedir;
do	
    echo "$dir"
  	
  for file in $dir;
  do   base=$file/$file
       echo $base 	
	~/src/casa-6.4.0-16/bin/casa --nogui --nologger --nologfile -c ${casa_script} $base $file
	~/src/casa-6.4.0-16/bin/python3 ~/corr_data/scripts/write_delay_res.py $file
  done
done

