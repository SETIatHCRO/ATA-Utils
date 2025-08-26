#!/usr/bin/env bash
set -x #echo on

ANTLIST=`python -c "import sys; from SNAPobs import snap_config; print(','.join([s for s in snap_config.get_rfsoc_active_antlist()]))"`
IFS=',' read -r -a ANTARR <<< "$ANTLIST"

printf -v LOA "%sA," "${ANTARR[@]}"
LOA="${LOA%,}"
printf -v LOB "%sB," "${ANTARR[@]}"
LOB="${LOB%,}"
printf -v LOC "%sC," "${ANTARR[@]}"
LOC="${LOC%,}"
printf -v LOD "%sD," "${ANTARR[@]}"
LOD="${LOD%,}"

configure_antenna_streams.py -g \
${LOA} \
${LOB} \
${LOC} \
${LOD} \
-C ataconfig_beamformer_8bit_4tunings $@
