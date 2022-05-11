#!/bin/bash

input_file="/home/sonata/pranav/input_guppi.txt"

is_empty () {
fil=$1
while IFS= read line
do
  if [[ $line =~ ^#.* ]];
  then
    # lins starts with #, let's continue
    continue
  else
    # line doesnt start with #, so it's not empty, return immediately
    echo 1
    return
  fi
done <"$fil"
echo 0
}

touch /home/sonata/pranav/no_hit_h5.txt
touch /home/sonata/pranav/candidate_h5.txt

cat ${input_file} | while read fname
do
    #echo $fname
    for node in seti-node1.0 seti-node2.0 seti-node2.1 seti-node3.0 seti-node3.1 seti-node4.0 seti-node4.1 seti-node5.0 seti-node5.1 seti-node6.0 seti-node6.1 seti-node7.0 seti-node7.1 seti-node8.0
    do
        #echo $node
        cd /mnt/dataz-netStorage-40G/turboseti/$fname/$node/
        
        file=$fname.rawspec.0000.dat
        retval=`is_empty "$file"`
        echo $retval
        if [[ $retval == 0 ]];
        then
            #This txt file will contain h5 files that have no candidates
            echo $fname/$node/$fname.rawspec.0000.h5 >> /home/sonata/pranav/no_hit_h5.txt;  
        else 
            #This txt file contains h5 files that have candidates
            echo $fname/$node/$fname.rawspec.0000.h5 >> /home/sonata/pranav/candidate_h5.txt;
        fi
        
        cd ../..

    done
done    
