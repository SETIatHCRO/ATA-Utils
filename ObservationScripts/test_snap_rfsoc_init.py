from SNAPobs import snap_control

hosts = ["frb-snap5-pi", "rfsoc1-ctrl-1", "rfsoc1-ctrl-2"]

snaps = snap_control.init_snaps(hosts)
snap_control.get_system_information(snaps)

print(snaps)
