#!/usr/bin/env bash
set -x #echo on

ANTLIST=`python -c "import os; os.environ['ATA_SNAPOBS_HPGUPPPI_DEFAULTS_RESOLVE_HPT'] = 'False'; from SNAPobs import snap_config; print(','.join([s for s in snap_config.get_rfsoc_active_antlist()]))"`
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
-C ataconfig_fengine_destinations_continuum $@
