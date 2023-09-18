#!/bin/bash

# This script takes 2 inputs, .fil file directory and an output directory.
# Runs turboSETI with command line tools on the .fil files to search for hits.
# Creates subfolders with .dat files in the output directory.

# Edit the turboSETI command line as necessary.
# Change fil to h5 for the newer ATA data format.

STARTTIME=$(date +%s)
echo " "
echo "running turboSETI bash script..." 
echo " "
echo $(date)
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
    # echo $outdir
fi

# Check if the input directory exists
if [ ! -d $indir ]
  then
    echo "Directory $indir does not exist."
    exit 1
fi

for dir in ${indir[@]}
do
  # Recursively search for '*.fil' files in the directory
  find $dir -type f -name '*.fil' -print0 | while read -d $'\0' fil; do
      # Create the output directory with the same structure as the input directory
      relpath=$(realpath --relative-to=$dir $(dirname $fil))
      mkdir -p "$outdir$relpath"

      # Commented out for testing only:
      # echo $fil
      # echo $outdir$relpath

      # Execute the turboSETI command for each '*.fil' file found
      turboSETI $fil -s 10 -o $outdir$relpath -g y -l warning
      
      # Remove the .h5 files from the output directory
      rm -f $outdir$relpath/*.h5
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
