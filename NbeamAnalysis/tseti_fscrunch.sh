#!/bin/bash
STARTTIME=$(date +%s)
echo " "
echo "running turboSETI bash script with fscrunch..." 
echo " "
echo $(date)
echo " "
# activate the environment containing turboSETI
source /opt/mnt/bin/source_conda.sh
source activate turboseti
echo " "

# Check if both input and output directory names are provided as arguments
if [ $# -lt 2 ]
then
  echo "Usage: $0 <input directory> <base output directory>"
  exit 1
fi

# Store the input and base output directory names in variables
indir=("${@:1:$#-1}")
outdir=${!#}

if [[ ${outdir} != */ ]];then
    outdir=$outdir/
    echo $outdir
fi

# Check if the input directory exists
if [ ! -d $indir ]
  then
    echo "Directory $indir does not exist."
    exit 1
fi

for dir in ${indir[@]}
do
  # Recursively search for '*.fil' files in the input directory
  find $indir -type f -name '*.fil' -print0 | while read -d $'\0' fil; do
      # Create the output directory with the same structure as the input directory
      relpath=$(realpath --relative-to=$indir $(dirname $fil))
      mkdir -p "$outdir/$relpath"
      
      # Execute turboSETI through fscrunch.py for each '*.fil' file found
      python ~/scripts/NbeamAnalysis/fscrunch.py $fil -o $outdir/$relpath -M 15 -s 10 -f 2
      
      # Remove the .h5 files from the output directory
      rm -f "$outdir/$relpath"/*.h5
  done
done

echo " "
echo $(date)
echo " "
ENDTIME=$(date +%s)
echo "It took $(($ENDTIME - $STARTTIME)) seconds to complete this task..."
echo " "
echo "Game over. Thanks for playing." 
echo " "