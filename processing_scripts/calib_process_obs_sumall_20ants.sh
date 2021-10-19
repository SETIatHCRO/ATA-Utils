#!/bin/bash

NPROC=16
#NPROC=2
clfd="/home/obsuser/miniconda3/envs/ATAobs/bin/clfd"

todir=/mnt/datax-netStorage-40G/psr_backend/

for ant in [1-9]*; do
    ((i=i%NPROC)); ((i++==0)) && wait
    ~/scripts/decimator.bash $locdir $ant &
done
wait

for ant in [1-9]*; do
    pushd ${ant}
    echo "dspsr -kata -A -L 20 -Lmin 15 -t ${NPROC} decimated.fil"
    dspsr -kata -A -L 20 -Lmin 15 -t ${NPROC} decimated.fil
    popd
done

mkdir ics

#~/scripts/sumfils_wrapper.py `ls -d [1-9]*` -p ${NPROC}
numactl -N 0 ~/scripts/sumfils/sumfils */decimated.fil -o ./ics/ics.fil -p $NPROC

pushd ics
dspsr -kATA -A -L 20 -Lmin 15 -t ${NPROC} ics.fil
popd

utc=`pwd | rev | cut -d "/" -f 1 | rev`
name=`psredit -c "name" -Q */*.a.ar | cut -d " " -f 2`

paz -Z "0 730" -Z "3600 4095" -m */*.ar
${clfd} */*.ar
psrplot -pfreq+ -N5x5 -jDT */*ar.clfd -g 4096x3072 -Dall.png/png

psrplot -pfreq+ -N5x5 -jDT */*ar.clfd -D/xs

cp all.png ${utc}_${name}.png

#channels=C01HKMMQVUZ
curl -F file=@./${utc}_${name}.png -F channels=C6KK9EX70 -H "Authorization: Bearer xoxp-18246494320-18247803318-911958760085-cf70d8641df97c4d8fda4a85516daf89" https://slack.com/api/files.upload

pam -T -F -e ".clfd.tf" */*.ar.clfd

psrstat -c "snr=pdmp,snr" -jDTF */*.ar.clfd
psrstat -c "snr=pdmp,snr" -jDTF */*.ar.clfd > snr.txt

cat pdmp.per

rm [1-9]*/202*.fil

mv /mnt/buf0/obs/${utc} "${todir}" &
