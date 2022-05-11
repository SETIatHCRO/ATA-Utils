from ATATools import ata_control
import atexit

az_offset = 20.
el_offset = 0.

ant_list = ["1a", "1f", "1c", "2a", "2b", "2h",
        "3c", "4g", "1k", "5c", "1h", "4j"]

ata_control.reserve_antennas(ant_list)
atexit.register(ata_control.release_antennas,ant_list, False)

source = "casa"
ata_control.create_ephems2(source, az_offset, el_offset)

ata_control.point_ants2(source, "on", ant_list)

ata_control.point_ants2(source, "off", ant_list) #this failes
