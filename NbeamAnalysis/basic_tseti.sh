#!/bin/bash

# Check if a directory name is provided as an argument
if [ $# -eq 0 ]
  then
    echo "No directory name provided. Usage: $0 <directory>"
    exit 1
fi

# Store the directory name in a variable
dir=$1

# Check if the directory exists
if [ ! -d $dir ]
  then
    echo "Directory $dir does not exist."
    exit 1
fi

# Recursively search for '*.fil' files in the directory
find $dir -type f -name '*.fil' -print0 | while read -d $'\0' fil; do
    # Create the output directory with the same structure as the input directory
    outdir=$(dirname "${fil/$dir/outdir}")
    mkdir -p $outdir
    
    # Execute the turboSETI command for each '*.fil' file found
    turboSETI $fil -s 10 -o $outdir -g y -l warning
    
    # Remove the .h5 files from the output directory
    rm -f $outdir/*.h5
done
