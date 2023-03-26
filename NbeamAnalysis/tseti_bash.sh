#!/bin/bash
STARTTIME=$(date +%s)
echo " "
echo "running turboSETI bash script with fscrunch..." 
echo " "
echo $(date)
echo " "
# activate the environment containing turboSETI
source /opt/mnt/bin/source_conda.sh
source activate turboseti
echo " "
# define the base directory where the tree of project observations are stored
# NOTE: This script assumes a directory tree structure of: BASE_DATA_DIR/2022-10-27*/*trappist/seti_node*/*.fil
BASE_DATA_DIR=/mnt/datac-netStorage-40G/projects/p004
for obs in $BASE_DATA_DIR/2022-10-27*
do
    OBS_START_TIME=$(date +%s)
    for fil_dir in $obs/*trappist*
    do
        INT_START_TIME=$(date +%s)
        for node in $fil_dir/seti-node*
        do
            NODE_START_TIME=$(date +%s)
            OUTDIR=/mnt/buf0/PPO/${node#$BASE_DATA_DIR/}
            mkdir -p $OUTDIR
            python ~/scripts/fscrunch.py $node -o $OUTDIR -M 15 -s 10 -f 2 >/dev/null
            NODE_END_TIME=$(date +%s)
            echo " "
            echo "It took $(($NODE_END_TIME - $NODE_START_TIME)) seconds to complete this node..."
            echo " "
        done
        INT_END_TIME=$(date +%s)
        echo " "
        echo "It took $(($INT_END_TIME - $INT_START_TIME)) seconds to complete this integration block..."
        echo " "
    done
    OBS_END_TIME=$(date +%s)
    echo " "
    echo "It took $(($OBS_END_TIME - $OBS_START_TIME)) seconds to complete this night of observations..."
    echo " "
done
echo " "
echo $(date)
echo " "
ENDTIME=$(date +%s)
echo "It took $(($ENDTIME - $STARTTIME)) seconds to complete this task..."
echo " "
echo "Game over. Thanks for playing." 
echo " "