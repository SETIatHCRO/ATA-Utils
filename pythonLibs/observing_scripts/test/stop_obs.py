#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from SNAPobs import snap_control

snap_list = ['frb-snap1-pi']

fengs = snap_control.init_snaps(snap_list)
snap_control.stop_snaps(fengs)
