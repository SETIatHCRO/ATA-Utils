#!/bin/sh

#accum=262144
accum=160
mac_addr="e41d2d073fe1"
netmask="10.11.1"
recv="151"
#FPGAfile="/home/sonata/ata_snap/snap_adc5g_spec_rpi/outputs/snap_adc5g_spec_rpi_2020-05-25_0811.fpg"
FPGAfile="/home/obsuser/snap_adc5g_spec_rpi_2020-06-17_0959.fpg"

#~/snap_initialize.py snap-0 ~/ATA/FPGAfirmware/snap_adc5g_spec_2018-07-07_1844.fpg --destip ${netmask}.${recv} --destmac ${mac_addr} --destport 4014 -e ${netmask}.171 -a ${accum}
#~/snap_initialize3.py frb-snap1-pi ${FPGAfile} --destip ${netmask}.${recv} --destmac ${mac_addr} --destport 4015 -e ${netmask}.161 -a ${accum} -s
#~/snap_initialize3.py frb-snap2-pi ${FPGAfile} --destip ${netmask}.${recv} --destmac ${mac_addr} --destport 4016 -e ${netmask}.162 -a ${accum} -s
#~/snap_initialize3.py frb-snap3-pi ${FPGAfile} --destip ${netmask}.${recv} --destmac ${mac_addr} --destport 4017 -e ${netmask}.163 -a ${accum} -s
~/snap_initialize3.py frb-snap4-pi ${FPGAfile} --destip ${netmask}.${recv} --destmac ${mac_addr} --destport 4018 -e ${netmask}.164 -a ${accum} -s
#~/snap_initialize3.py frb-snap5-pi ${FPGAfile} --destip ${netmask}.${recv} --destmac ${mac_addr} --destport 4019 -e ${netmask}.165 -a ${accum} -s
#~/snap_initialize3.py frb-snap6-pi ${FPGAfile} --destip ${netmask}.${recv} --destmac ${mac_addr} --destport 4020 -e ${netmask}.166 -a ${accum} -s
#~/snap_initialize3.py frb-snap7-pi ${FPGAfile} --destip ${netmask}.${recv} --destmac ${mac_addr} --destport 4021 -e ${netmask}.167 -a ${accum} -s
#~/snap_initialize3.py frb-snap8-pi ${FPGAfile} --destip ${netmask}.${recv} --destmac ${mac_addr} --destport 4022 -e ${netmask}.168 -a ${accum} -s
#~/snap_initialize3.py frb-snap9-pi ${FPGAfile} --destip ${netmask}.${recv} --destmac ${mac_addr} --destport 4023 -e ${netmask}.169 -a ${accum} -s
#~/snap_initialize3.py frb-snap10-pi ${FPGAfile} --destip ${netmask}.${recv} --destmac ${mac_addr} --destport 4024 -e ${netmask}.170 -a ${accum} -s
#~/snap_initialize3.py frb-snap11-pi ${FPGAfile} --destip ${netmask}.${recv} --destmac ${mac_addr} --destport 4025 -e ${netmask}.171 -a ${accum} -s
