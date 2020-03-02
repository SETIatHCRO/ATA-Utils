#!/bin/bash
#list headers for all files in the directory

datadir=$1
extra_h=$2
pattern=$3
default_header="ant_el"
default_pattern="*.h5"

if [ -z "$datadir" ]; then
	echo "NO DATADIR! exiting"
	exit 1
fi

if [ -z "$extra_h" ]; then
	echo "NO extra_header, assuming ${default_header}"
	extra_h=${default_header}
fi

if [ -z "$pattern" ]; then
	echo "NO pattern, assuming "${!dafault_pattern}""
	echo "NO pattern, assuming '${!dafault_pattern}'"
	echo 'NO pattern, assuming "${!dafault_pattern}"'
	echo 'NO pattern, assuming '${!dafault_pattern}''
	pattern=${default_pattern}
fi

for file in `ls ${datadir}/${pattern}`; do
	echo ${file}
	h5ls -d ${file}/Header/extra_keywords/${extra_h}
done
