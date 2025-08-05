#!/usr/bin/env bash

#python=/home/sonata/miniconda3/envs/rfsoc8bit/bin/python
#basedir=/home/sonata/src/ata_snap

#python=/opt/mnt/miniconda3/envs/testrfsoc2/bin/python
lmkconf=/opt/mnt/share/Jack_CLK1REF_10M_LMK_PL_OUT_50M_adc_on.txt
lmxconf=/opt/mnt/share/Jack_LMX_50_IN_256_OUT.txt
siconf=/opt/mnt/share/Si5341-RevD-ATA001-156_25M-041521-Registers.txt

rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc1.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc2.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc3.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc4.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc5.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc6.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc7.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc8.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc9.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc10.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc11.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc12.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc13.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc14.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc15.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc16.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc17.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc18.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc19.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc20.hcro.org &
rfsoc_program_clocks.py --lmkconf ${lmkconf} --lmxconf ${lmxconf} --siconf ${siconf} rfsoc21.hcro.org &
wait
