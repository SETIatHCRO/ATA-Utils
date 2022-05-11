#!/bin/bash

input_file="/home/sonata/pranav/plotseti.txt"
#input_file="/tmp/tmp.turbo.txt"

cat ${input_file} | while read fname
do
        echo $fname
        bash /home/sonata/scripts/scp_turboseti.bash $fname
        #bash /home/sonata/scripts/filter_seti_cands.bash $fname
        bash /home/sonata/scripts/plot_seti_cands.bash $fname
done
