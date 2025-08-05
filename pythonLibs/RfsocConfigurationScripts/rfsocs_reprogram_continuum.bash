#!/usr/bin/env bash
set -x #echo on

LOA=`python -c "import sys; from SNAPobs import snap_config; print(','.join(['%s%s' %(s,sys.argv[1]) for s in snap_config.get_rfsoc_active_antlist()]))" A`
LOB=`python -c "import sys; from SNAPobs import snap_config; print(','.join(['%s%s' %(s,sys.argv[1]) for s in snap_config.get_rfsoc_active_antlist()]))" B`
LOC=`python -c "import sys; from SNAPobs import snap_config; print(','.join(['%s%s' %(s,sys.argv[1]) for s in snap_config.get_rfsoc_active_antlist()]))" C`
LOD=`python -c "import sys; from SNAPobs import snap_config; print(','.join(['%s%s' %(s,sys.argv[1]) for s in snap_config.get_rfsoc_active_antlist()]))" D`

configure_antenna_streams.py -g \
${LOA} \
${LOB} \
${LOC} \
${LOD} \
-C ataconfig_beamformer_8bit_4tunings $@
