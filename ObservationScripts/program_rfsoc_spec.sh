#!/bin/bash
#cmd="/home/obsuser/miniconda3/envs/rfsoc/bin/rfsoc_feng_init.py"
#fpgfile="./ata_rfsoc/zrf_spec/outputs/zrf_spec_2021-04-28_1629.fpg"

#$cmd rfsoc1 $fpgfile -s 
#$cmd rfsoc1 $fpgfile -s --skipprog


cmd=rfsoc_feng_init.py
#cmd=/home/obsuser/miniconda3/envs/rfsoc/bin/rfsoc_feng_init.py

#fpgfile="./ata_rfsoc/zrf_spec_4ant/outputs/zrf_spec_4ant_2021-05-23_2326.fpg"
#fpgfile="./ata_rfsoc/zrf_spec_4ant/outputs/zrf_spec_4ant_2021-06-05_1337.fpg"
#fpgfile="./ata_rfsoc/zrf_spec_4ant/outputs/zrf_spec_4ant_2021-06-14_1301.fpg"
#fpgfile="./ata_rfsoc/zrf_spec_4ant/outputs/zrf_spec_4ant_2021-07-14_1501.fpg"
fpgfile=`cat $ATASHAREDIR/share/ata.cfg | grep SNAPFPG | awk '{print $2}'`
echo $fpgfile
cfg="/home/obsuser/src/ata_snap_rfsoc/ataconfig_single_sink.yml"

$cmd -i 0 1 2 3 -s rfsoc1-ctrl-1 $fpgfile $cfg --eth_spec -p 4031,4032,4033,4034

$cmd -i 0 1 2 3 -s rfsoc2-ctrl-1 $fpgfile $cfg --eth_spec -p 4041,4042,4043,4044

$cmd -i 0 1 2 3 -s rfsoc3-ctrl-1 $fpgfile $cfg --eth_spec -p 4051,4052,4053,4054

$cmd -i 0 1 2 3 -s rfsoc4-ctrl-1 $fpgfile $cfg --eth_spec -p 4061,4062,4063,4064

$cmd -i 0 1 2 3 -s rfsoc5-ctrl-1 $fpgfile $cfg --eth_spec -p 4071,4072,4073,4074
