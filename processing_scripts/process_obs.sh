#!/bin/bash

#fromdir=/mnt/buf0/Magnetar
fromdir=/mnt/buf0/obs
todir=/mnt/datax-netStorage-40G/frb_backend
#todir=/mnt/datay-netStorage-40G/new_obs
#todir=/mnt/buf0/proc
#filename=obs.finished
filename=obs.heimdall
decimate=/home/sonata/scripts/decimate_delete.bash

var=$((0))

NPROC=12

while true
do
    for locdir in `ls -d ${fromdir}/*`
    do
        if [ -e ${locdir}/${filename} ]; then
            date_start=`date`
            utc=`echo ${locdir} | rev | cut -d "/" -f1 | rev`
            echo ${utc}
            cd ${locdir}

            i=0
            for ant in [1-9]*; do
                ((i=i%NPROC)); ((i++==0)) && wait
                numactl -N 0 ~/scripts/decimator.bash $locdir $ant &
            done
            wait
            numactl -N 0 rm */202*.fil
            mkdir ics
            echo "Sum filbanks"

            if [ -e "obs.sumall" ]; then
                echo "Sum All"
                numactl -N 0 ~/scripts/sumfils/sumfils */decimated.fil -o ./ics/ics.fil -p $NPROC
                cd ./ics
                echo "Heimdall ics.fil"

                numactl -N 0 heimdall -f ics.fil -zap_chans 0 730 -zap_chans 3600 4096
                cat *.cand > all_candidates.dat
                rm *.cand
                echo "plotting ics.fil candidates"
                numactl -N 0 ~/scripts/plot_cands_individual.py -c ./all_candidates.dat -f ics.fil -u ${utc} -z 0 730 -z 3600 4096
                cd ../
                numactl -N 0 rm */decimated.fil

            else

                numactl -N 0 ~/scripts/sumfils_wrapper.py `ls -d [1-9]*` -p $NPROC

                cd ./ics
                echo "Heimdall ics_a.fil"
                numactl -N 0 heimdall -f ics_a.fil -zap_chans 0 730 -zap_chans 3600 4096
                cat *.cand > all_candidates_a.dat
                rm *.cand

                echo "Heimdall ics_b.fil"
                numactl -N 0 heimdall -f ics_b.fil -zap_chans 0 730 -zap_chans 3600 4096
                cat *.cand > all_candidates_b.dat
                rm *.cand

                echo "Heimdall ics_c.fil"
                numactl -N 0 heimdall -f ics_c.fil -zap_chans 0 730 -zap_chans 3600 4096
                cat *.cand > all_candidates_c.dat
                rm *.cand


                echo "plotting ics_a.fil candidates"
                numactl -N 0 ~/scripts/plot_cands_individual.py -c ./all_candidates_a.dat -f ./ics_a.fil -u ${utc}_a -z 0 730 -z 3600 4096
                echo "plotting ics_b.fil candidates"
                numactl -N 0 ~/scripts/plot_cands_individual.py -c ./all_candidates_b.dat -f ./ics_b.fil -u ${utc}_b -z 0 730 -z 3600 4096
                echo "plotting ics_c.fil candidates"
                numactl -N 0 ~/scripts/plot_cands_individual.py -c ./all_candidates_c.dat -f ./ics_c.fil -u ${utc}_c -z 0 730 -z 3600 4096
                cd ../
                numactl -N 0 rm */decimated.fil
            fi

            cd ${fromdir}
            numactl -N 0 mv "${locdir}" /mnt/buf0/proc
            numactl -N 0 mv /mnt/buf0/proc/${utc} "${todir}" &
            echo "Done with ${locdir}"
            echo "Started at:"
            echo ${date_start}
            echo "Ended at:"
            echo "`date`"
        fi
    done
    sleep 10
done
