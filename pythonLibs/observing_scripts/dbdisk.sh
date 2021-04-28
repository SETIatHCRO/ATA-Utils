#!/bin/csh

echo $1

#mkdir $1/snap1 $1/snap2 $1/snap3 $1/snap4 $1/snap5 $1/snap6 $1/snap8 $1/snap9 $1/snap10
mkdir $1/snap3 $1/snap4 $1/snap5 $1/snap6 $1/snap9

#dada_dbdisk -k d0d0 -D $1/snap1 -s -z &
#dada_dbdisk -k d1d1 -D $1/snap2 -s -z &
dada_dbdisk -k d2d2 -D $1/snap3 -s -z &
dada_dbdisk -k d3d3 -D $1/snap4 -s -z &
dada_dbdisk -k d4d4 -D $1/snap5 -s -z &
dada_dbdisk -k d5d5 -D $1/snap6 -s -z &
#dada_dbdisk -k d7d7 -D $1/snap8 -s -z &
dada_dbdisk -k d8d8 -D $1/snap9 -s -z &
#dada_dbdisk -k d9d9 -D $1/snap10 -s -z &


#mkdir $1/ICS
#dada_dbdisk -k dada -D $1/ICS -s -z &
