#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from astropy import units as u
from astropy.coordinates import Angle

from . import ata_control, logger_defaults
import threading
import time


_COORD_TYPES = ["azel", "radec"]
_CADENCE = 0.5 #seconds
class CoordDumpThread(threading.Thread):
    """
    A thread-based class used to dump coordinates (azel or radec) at high cadence to file

    ...

    Attributes
    ----------
    antList : list
        list of antennas
    outFileName : str
        name of output file
    coordType : str
        allowed values: 'azel' (default) and 'radec'
    cadence : float
        update rate in seconds (default = 0.5) 

    Methods
    -------
    run()
        starts thread
    stop()
        stops thread
    """

    def __init__(self, antList, outFileName, coordType="azel", cadence=None):
        logger = logger_defaults.getModuleLogger(__name__)

        # make thread a daemon in case main wants to exit
        # not the cleanest solution, as file would still be open
        threading.Thread.__init__(self, daemon=True)

        # Make sure we know what coordinates we're dumping to disk
        if coordType not in ["azel", "radec"]:
            raise RuntimeError("coordType provided (%s) is not included in %s"
                    %(coordType, _COORD_TYPES))

        # antList must be a list
        assert type(antList) == list, "antList argument must be a list"

        # Open output file
        self.OutFile = open(outFileName, "w")

        # set the data pulling function
        # and populate the header in the output file
        if coordType == "azel":
            self._pull_func = ata_control.get_az_el
            _ant_header = ["%s_%s" %(ant, coord) for ant in antList
                for coord in ["az", "el"]]
            _ant_header_str = " ".join(_ant_header)
            header_str = "# Time_unix " + _ant_header_str + "\n"

        elif coordType == "radec":
            self._pull_func = ata_control.get_ra_dec
            _ant_header = ["%s_%s" %(ant, coord) for ant in antList
                for coord in ["ra", "dec"]]
            _ant_header_str = " ".join(_ant_header)
            header_str = "# Time_unix " + _ant_header_str + "\n"

        # Write header
        self.OutFile.write(header_str)

        self.antList = antList

        # a thread-stopping mechanism
        self._stop = threading.Event()

        # cadence in seconds
        if not cadence:
            self.cadence = _CADENCE

    def stop(self):
        logger = logger_defaults.getModuleLogger(__name__)
        logger.info("Stopping")
        self._stop.set()

    def _is_terminated(self):
        return self._stop.isSet()

    def _to_string(self, time_now, coords):
        all_str = "%.6f" %time_now
        for ant in self.antList:
            all_str += " "
            all_str += "%.6f %.6f" %(coords[ant][0], coords[ant][1])
        all_str += "\n"
        return all_str

    def run(self):
        logger = logger_defaults.getModuleLogger(__name__)
        logger.info("Starting coord dump thread")
        while not self._is_terminated():
            time_now = time.time()
            coords = self._pull_func(self.antList)
            coords_str = self._to_string(time_now, coords)

            # write to output file
            self.OutFile.write(coords_str)
            time.sleep(self.cadence)

        logger.info("Received stop, run() is returning")
        self.OutFile.close()




def hour2hms(hour):
    h = Angle(hour*u.h).to_string(unit=u.h, sep=":")
    # add leading zero i.e. 0:24:43 to 00:24:43
    h_split = h.split(":")
    h_split[0] = h[0].zfill(2)
    h = ":".join(h_split)
    return h

def deg2dms(degree):
    ang = Angle(degree*u.degree).to_string(unit=u.degree, sep=":")
    # add leading zero
    ang_split = ang.split(":")
    ang_split[0] = ang_split[0].zfill(3) if ang[0] == "-" \
            else ang_split[0].zfill(2)
    ang = ":".join(ang_split)
    return ang

