#!/bin/bash

#input_file="~/pranav/tmp.txt"
#input_file="/home/sonata/corr_data/mjd59623_3c273.txt"
#input_file="/home/sonata/corr_data/mjd59623_3c295.txt"
input_file="/home/sonata/corr_data/scp_list.txt"

cat ${input_file} | while read fname
do
        echo $fname
        #bash /home/sonata/corr_data/scripts/scp_data_2lo_rt.bash $fname
	bash /home/sonata/corr_data/scripts/scp_data_2lo_rt_net.bash $fname
        cd /mnt/dataz-netStorage-40G/corr_data/${fname}
        cp /home/sonata/corr_data/scripts/concat_all_b.py ./
        HDF5_USE_FILE_LOCKING='FALSE' python concat_all_b.py $fname
	cp /home/sonata/corr_data/scripts/concat_all_c.py ./
	HDF5_USE_FILE_LOCKING='FALSE' python concat_all_c.py $fname
done
