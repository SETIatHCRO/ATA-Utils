#!/bin/bash

while getopts d: flag
do
    case "${flag}" in
        d) basedir=${OPTARG};;
    esac
done
echo "Basedir: $basedir";

shift 2



logbasedir=`cat /home/sonata/share/ata.cfg | grep LOGDIR | awk '{print $2}'`

vars=$@
ants=(`echo ${vars}`)

#ata_dbsumdb d0d0 d1d1 d2d2 d3d3 -o dada -d


cpu_counter=1
buf_counter=0
for ant in "${ants[@]}"
do
    snap_name=`cat ${HOME}/share/ata_snap.tab | grep $ant | awk '{printf $1}'`
    recv_host=`cat ${HOME}/share/ata_snap.tab | grep $ant | awk '{printf $4}'`
    recv_port=`cat ${HOME}/share/ata_snap.tab | grep $ant | awk '{printf $5}'`
    numactl -C $cpu_counter ata_udpdb ./spectrometer_header.txt -p ${recv_port} -k d${buf_counter}d${buf_counter} -i ${recv_host} &>> "${logbasedir}/udpdb_${snap_name}.log" &
    let cpu_counter+=1
    let buf_counter+=1
done


#numactl -C 1 ata_udpdb  ./spectrometer_header.txt -p 4015 -k d0d0 -i ${netmask}.180  &>> "${logbasedir}/snap1.log"  & 
#numactl -C 2 ata_udpdb  ./spectrometer_header.txt -p 4016 -k d1d1 -i ${netmask}.180  &>> "${logbasedir}/snap2.log"  &
#numactl -C 3 ata_udpdb  ./spectrometer_header.txt -p 4017 -k d2d2 -i ${netmask}.180  &>> "${logbasedir}/snap3.log"  &
#numactl -C 4 ata_udpdb  ./spectrometer_header.txt -p 4018 -k d3d3 -i ${netmask}.180  &>> "${logbasedir}/snap4.log"  &
#numactl -C 5 ata_udpdb  ./spectrometer_header.txt -p 4019 -k d4d4 -i ${netmask}.180  &>> "${logbasedir}/snap5.log"  &
#numactl -C 6 ata_udpdb  ./spectrometer_header.txt -p 4020 -k d5d5 -i ${netmask}.180  &>> "${logbasedir}/snap6.log"  &
#numactl -C 7 #ata_udpdbf ./spectrometer_header.txt -p 4021 -k d6d6 -i ${netmask}.180  &>> "${logbasedir}/snap7.log"  &
#numactl -C 8 ata_udpdb  ./spectrometer_header.txt -p 4022 -k d7d7 -i ${netmask}.180  &>> "${logbasedir}/snap8.log"  &
#numactl -C 9 ata_udpdb  ./spectrometer_header.txt -p 4023 -k d8d8 -i ${netmask}.180  &>> "${logbasedir}/snap9.log"  &
#numactl -C 10 ata_udpdb  ./spectrometer_header.txt -p 4024 -k d9d9 -i ${netmask}.180  &>> "${logbasedir}/snap10.log" & 
