from ATATools import ata_control
import atexit

source = "casa"
#print(eph)
ant_list = ["2e"]

ata_control.reserve_antennas(ant_list)
atexit.register(ata_control.release_antennas, ant_list, False)

#eph_id = ata_control.generate_ephemeris(source=source)
eph_id = ata_control.generate_ephemeris(azel=[80.,80.])
eph = ata_control.retrieve_ephemeris(eph_id)
print(eph_id)

ata_control.track_ephemeris(eph_id, ant_list, wait=True)
_ = input("waiting...")
#ata_control.set_antennas_azel_offset(ant_list, 0, 1)
