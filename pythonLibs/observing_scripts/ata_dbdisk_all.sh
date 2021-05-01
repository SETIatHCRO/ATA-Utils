#!/bin/bash

#echo $1


while getopts d: flag
do
    case "${flag}" in
        d) basedir=${OPTARG};;
    esac
done
echo "Basedir: $basedir";

shift 2


buf_counter=0
i=1
for ant in $@
do
    snap_name=`cat ${HOME}/share/ata_snap.tab | grep $ant | awk '{printf $1}' | cut -d "-" -f2`
    mkdir $basedir/$snap_name
    dada_dbdisk -k d${buf_counter}d${buf_counter} -D $basedir/$snap_name -s -z &
    let buf_counter+=1
done


#while [ $i -le "$#" ]
#do
#    if [ $i = "1" ]; then
#        basedir=${1}
#        let i+=1
#        continue
#    fi
#    ant=${${i}}
#    snap_name=`cat ${HOME}/share/ata_snap.tab | grep $ant | awk '{printf $1}' | cut -d "-" -f2`
#    echo $name_name
#    echo mkdir $basedir/
#    let buf_counter+=1
#    let i+=1
#done


#mkdir $1/snap1 $1/snap2 $1/snap3 $1/snap4 $1/snap5 $1/snap6 $1/snap8 $1/snap9 $1/snap10
#mkdir $1/snap3 $1/snap4 $1/snap5 $1/snap6 $1/snap9

#dada_dbdisk -k d0d0 -D $1/snap1 -s -z &
#dada_dbdisk -k d1d1 -D $1/snap2 -s -z &
#dada_dbdisk -k d2d2 -D $1/snap3 -s -z &
#dada_dbdisk -k d3d3 -D $1/snap4 -s -z &
#dada_dbdisk -k d4d4 -D $1/snap5 -s -z &
#dada_dbdisk -k d5d5 -D $1/snap6 -s -z &
#dada_dbdisk -k d7d7 -D $1/snap8 -s -z &
#dada_dbdisk -k d8d8 -D $1/snap9 -s -z &
#dada_dbdisk -k d9d9 -D $1/snap10 -s -z &


#mkdir $1/ICS
##dada_dbdisk -k dada -D $1/ICS -s -z &
