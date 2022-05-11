from ATATools import ata_control
import atexit

ant_list = ["1a", "1f", "1c", "2a", "2b", "2h",
            "3c", "4g", "1k", "5c", "1h", "4j"]

ata_control.reserve_antennas(ant_list)
atexit.register(ata_control.release_antennas,ant_list, True)

#print("Setting az_el to 60,60")
#ata_control.set_az_el(ant_list, 60, 60)

#print ("Tracking casa")
#source = "casa"
#ata_control.make_and_track_ephems(source, ant_list)

print ("Tracking coordinates: RA = 21.478, DEC = 41.545")
ata_control.make_and_track_ra_dec(21.478, 41.545, ant_list)

print("Done")
