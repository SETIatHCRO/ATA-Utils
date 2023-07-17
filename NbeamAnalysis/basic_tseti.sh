#!/bin/bash

# Takes 2 inputs, .fil file directory and an output directory.
# Creates subfolders with .dat files in the output directory.

# Check if both input and output directory names are provided as arguments
if [ $# -ne 2 ]
  then
    echo "Usage: $0 <input directory> <base output directory>"
    exit 1
fi

# Store the input and base output directory names in variables
indir=$1
outdir=$2

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

# Recursively search for '*.fil' files in the directory
find $indir -type f -name '*.fil' -print0 | while read -d $'\0' fil; do
    # Create the output directory with the same structure as the input directory
    relpath=$(realpath --relative-to=$indir $(dirname $fil))
    mkdir -p "$outdir$relpath"
    # echo $outdir$relpath

    # Execute the turboSETI command for each '*.fil' file found
    turboSETI $fil -s 10 -o $outdir$relpath -g y -l warning
    
    # Remove the .h5 files from the output directory
    rm -f $outdir$relpath/*.h5
done
