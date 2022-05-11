#!/usr/bin/python3

from string import Template
import sys,os

OBS_BASEDIR="/mnt/datax-netStorage-40G/calibration"
OBS_DAT_NAME="obs.dat"

RES_BASEDIR="/home/caluser/Results"
RES_DIRS_DONE=os.listdir(RES_BASEDIR)
UTCS_DONE=[res_dir.split("_")[1] for res_dir in RES_DIRS_DONE]

cmd_template = Template(
        "RESULTDIR=$outdir /home/caluser/bin/MoonSourceReduction.tcl -source $source -dir $dir")

# Read the dat database to know the observation utcs
# Assumption: database has shape:
# UTC source_name N_on_off
db_name = os.path.join(OBS_BASEDIR, OBS_DAT_NAME)
db = open(db_name, "r")

flag=0

with open(db_name, "r") as db:
    for iline, obs_line in enumerate(db):
        # Skip the header
        if obs_line.startswith("#"):
            continue

        try:
            utc, source, n_on_off = obs_line.strip().split(" ")
        except ValueError as e:
            raise RuntimeError("Wrong entry %s in line %i" %(obs_line, 
                iline+1))

        if utc not in UTCS_DONE:
            cal_dir = os.path.join(OBS_BASEDIR, utc)
            cmd = cmd_template.substitute(source=source, 
                    dir=cal_dir, outdir=RES_BASEDIR)
            print("Running:")
            print(cmd)
            os.system(cmd)

            flag=1
            break


if flag:
    print("Done utc: %s" %utc)
else:
    print("No observation found")
