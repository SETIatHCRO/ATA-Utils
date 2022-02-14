fpgfile="/home/obsuser/src/ata_snap_rfsoc/ata_rfsoc/zrf_volt_4ant/outputs/zrf_volt_4ant_2021-07-13_1845.fpg"
#cfg="/home/obsuser/src/ata_snap_rfsoc/ataconfig_single_volt_corr_test.yml"
cfg="/home/obsuser/src/ata_snap_rfsoc/ataconfig_single_volt_test_linerate.yml"

rfsoc_feng_init.py --eth_volt -s rfsoc1-ctrl-1 ${fpgfile} ${cfg} -p 10000,10000,10000,10000,10000,10000,10000,10000 -j 0,1,2,3 -i 0,1,2,3 -s
rfsoc_feng_init.py --eth_volt -s rfsoc2-ctrl-1 ${fpgfile} ${cfg} -p 10000,10000,10000,10000,10000,10000,10000,10000 -j 0,1,2,3 -i 4,5,6,7 -s
rfsoc_feng_init.py --eth_volt -s rfsoc3-ctrl-1 ${fpgfile} ${cfg} -p 10000,10000,10000,10000,10000,10000,10000,10000 -j 0,1,2,3 -i 8,9,10,11 -s
rfsoc_feng_init.py --eth_volt -s rfsoc4-ctrl-1 ${fpgfile} ${cfg} -p 10000,10000,10000,10000,10000,10000,10000,10000 -j 0,1,2,3 -i 12,13,14,15 -s
rfsoc_feng_init.py --eth_volt -s rfsoc5-ctrl-1 ${fpgfile} ${cfg} -p 10000,10000,10000,10000,10000,10000,10000,10000 -j 0,1,2,3 -i 16,17,18,19 -s
