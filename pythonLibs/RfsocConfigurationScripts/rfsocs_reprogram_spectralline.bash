#!/usr/bin/env bash
set -x #echo on

fpg_file="/opt/mnt/share/zrf_volt_64c_12t_8ant_xczu49dr_2024-06-03_1434.fpg"
cfg_file="/home/sonata/src/observing_campaign/config_files/ataconfig_beamformer_16MHz.yml"

export ATASHAREDIR=/opt/mnt

### all 4 tunings and 28 antenna...
configure_antenna_streams.py -g \
1bA,1cA,1dA,1eA,1fA,1gA,1hA,4jA,1kA,2aA,2bA,2cA,2dA,2eA,2fA,4gA,2hA,2jA,2kA,2lA,2mA,3cA,3dA,5bA,5cA,3lA,4eA,5eA \
1bB,1cB,1dB,1eB,1fB,1gB,1hB,4jB,1kB,2aB,2bB,2cB,2dB,2eB,2fB,4gB,2hB,2jB,2kB,2lB,2mB,3cB,3dB,5bB,5cB,3lB,4eB,5eB \
1bC,1cC,1dC,1eC,1fC,1gC,1hC,4jC,1kC,2aC,2bC,2cC,2dC,2eC,2fC,4gC,2hC,2jC,2kC,2lC,2mC,3cC,3dC,5bC,5cC,3lC,4eC,5eC \
1bD,1cD,1dD,1eD,1fD,1gD,1hD,4jD,1kD,2aD,2bD,2cD,2dD,2eD,2fD,4gD,2hD,2jD,2kD,2lD,2mD,3cD,3dD,5bD,5cD,3lD,4eD,5eD \
-C ataconfig_beamformer_16MHz -f ${fpg_file} $@
