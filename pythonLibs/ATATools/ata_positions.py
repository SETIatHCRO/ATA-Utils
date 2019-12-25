#!/usr/bin/python

##
# ATAPOsitions class
# Calculated the Az/Elof various objects in the sky, including ra/dec.
# Note that the calculated positions are not exact, but within a degree.
# Author: Jon Richards, SETI Institute
# July 16, 2018
##

import sys
import numpy as np, scipy.io
import plumbum
import math
import os
import datetime as dt
import ata_constants as ata_const
import ephem
import math
from astropy import units as u
from astropy.coordinates import Angle

MIN_MOON_SUN_DIST = 45.0
MIN_ELEV = 23.0

class ATAPositions:

    def __init__(self):

        self.observer = ephem.Observer()
        self.observer.lat = ata_const.ATA_LAT * math.pi/180.0
        self.observer.lon = ata_const.ATA_LON * math.pi/180.0
        self.observer.elev = ata_const.ATA_ELEV

    @staticmethod
    def getFirstInListThatIsUp(sources, d=None):

        if(d == None):
            d=dt.datetime.now()

        pos = ATAPositions();

        for s in sources:
            info = pos.getAzEl(d, s)
            sun_angle = ATAPositions.angular_distance('sun', s, d)
            if(s == 'moon'):
                moon_angle = 90.0
            else:
                moon_angle = ATAPositions.angular_distance('moon', s, d)
            is_up = pos.isUp(s, d)
            if(is_up == True and sun_angle >= MIN_MOON_SUN_DIST and moon_angle >= MIN_MOON_SUN_DIST):
              info = pos.getAzEl(d, s)
              return { 'status' : 'up', 'source' : s, 'az' : info['az'], 'el' : info['el'] }

        # If we got this far, none are up. So get the next one to rise
        future_minutes = 1;
        now_date = d

        while(future_minutes < 1440): #If more than 1 day, something is wrong

            d = now_date + dt.timedelta(minutes=future_minutes)

            for s in sources:
                info = pos.getAzEl(dt.datetime.now(), s)
                sun_angle = ATAPositions.angular_distance('sun', s, d)
                if(s == 'moon'):
                    moon_angle = 90.0
                else:
                    moon_angle = ATAPositions.angular_distance('moon', s, d)
                is_up = pos.isUp(s, d)
                if(is_up == True and sun_angle >= MIN_MOON_SUN_DIST and moon_angle >= MIN_MOON_SUN_DIST):
                    print s
                    info = pos.getAzEl(d, s)
                    return { 'status' : 'next_up', 'source' : s, 'az' : info['az'], \
                            'el' : info['el'], "minutes" : future_minutes }
            future_minutes+=1;


        return None

    def getSunAzEl(self, d=None):
        if(d == None):
            self.observer.date = dt.datetime.now()
        else:
            self.observer.date = d
        sun = ephem.Sun()
        sun.compute(self.observer)
        return { 'az' : sun.az * 180.0/math.pi, 'el' : sun.alt * 180.0/math.pi }

    
    # Get the Az, El returned in decrees
    # ra/dec options, ra in hours decimal, dec in degrees decimal
    def getAzEl(self, d, name, ra=-99.0, dec=-99):

        if(name == None and ra == -99 and dec == -99):
            return None

        self.observer.date = d
        obj = None
        if(name != None):

            if(name.lower() == "sun"):
                obj = ephem.Sun()
            elif(name.lower() == "moon"):
                obj = ephem.Moon()
            elif(name.lower() == "casa"):
                obj =  ephem.FixedBody()
                obj._ra = 23.391 * math.pi/180.0 * 15.0
                obj._dec = 58.808 * math.pi/180.0
            elif(name.lower() == "cyga"):
                obj =  ephem.FixedBody()
                obj._ra = 19.991 * math.pi/180.0 * 15.0
                obj._dec = 40.734 * math.pi/180.0
            elif(name.lower() == "taua"):
                obj =  ephem.FixedBody()
                obj._ra = 5.575 * math.pi/180.0 * 15.0
                obj._dec = 22.016 * math.pi/180.0
            elif(name.lower() == "vira"):
                obj =  ephem.FixedBody()
                obj._ra = 12.514 * math.pi/180.0 * 15.0
                obj._dec = 12.391 * math.pi/180.0
            elif(name.lower() == "goes-16"):
                obj =  ephem.FixedBody()
                ra,dec = self.observer.radec_of(121.998 * math.pi/180.0, 23.598 * math.pi/180.0)
                obj._ra =  ra
                obj._dec = dec
            elif(name.lower() == "radec"):
                obj =  ephem.FixedBody();
                obj._ra = ra * math.pi/180.0 * 15.0
                obj._dec = dec * math.pi/180.0
                name = "%f,%f" % (ra, dec)
        else:
            obj =  ephem.FixedBody();
            obj._ra = ra * math.pi/180.0 * 15.0
            obj._dec = dec * math.pi/180.0
            name = "%f,%f" % (ra, dec)

        obj.compute(self.observer)
        return { 'name' : name,
                 'az' : obj.az * 180.0/math.pi, 'el' : obj.alt * 180.0/math.pi,
                 'ra' : obj.ra/ephem.degree / 15.0, 'dec' :  obj.dec/ephem.degree }


        return None

    def isUp(self, name, d=None, ra=-99.0, dec=-99):
        
        if(name == 'goes-16'):
            return True

        if(d == None):
            d = dt.datetime.now()

        loc = self.getAzEl(d, name, ra, dec)
        #print "isUp: %f" % loc['el']
        if(loc['el'] > MIN_ELEV):
            return True
        return False

    @staticmethod
    def angular_distance(source1, source2, d=None):

        if(d == None):
            d=dt.datetime.now()

        pos = ATAPositions();

        s1_az_el = pos.getAzEl(d, source1)
        s2_az_el = pos.getAzEl(d, source2)

        az1 = s1_az_el['az']
        el1 = s1_az_el['el']
        az2 = s2_az_el['az']
        el2 = s2_az_el['el']

        if(abs(az1 - az2) < 1 and abs(el1 - el2) < 1):
            #print "%s: %.1f %.1f" % (source1, az1, el1)
            #print "%s: %.1f %.1f" % (source2, az2, el2)
            return 0.0

        pi = math.pi
        az1 = math.radians(az1)
        el1 = math.radians(el1)
        az2 = math.radians(az2)
        el2 = math.radians(el2)

        return 180.0/pi * math.acos( (math.sin(el1) * math.sin(el2) + math.cos(el1) * math.cos(el2) * math.cos(az1-az2)))



if __name__== "__main__":

    def run_tests():
        print "ATA Position tests"
        pos = ATAPositions()
        sun = pos.getAzEl(dt.datetime.now(), "Sun")
        print sun
        moon = pos.getAzEl(dt.datetime.now(), "moon")
        print moon
        casa = pos.getAzEl(dt.datetime.now(), "casa")
        print casa
        taua = pos.getAzEl(dt.datetime.now(), "taua")
        print taua
        vira = pos.getAzEl(dt.datetime.now(), "vira")
        print vira
        radec = pos.getAzEl(dt.datetime.now(), None, 12.514, 12.391)
        print radec
        goes_16 = pos.getAzEl(dt.datetime.now(), "goes-16")
        print goes_16
        print ATAPositions.angular_distance('moon', 'goes-16')
        print ATAPositions.angular_distance('sun', 'goes-16')

        obj = sun
        up = pos.isUp(obj['name'])
        print "%s el=%f, up=%s" % (obj['name'], obj['el'], up)

        obj = moon
        up = pos.isUp(obj['name'])
        print "%s el=%f, up=%s" % (obj['name'], obj['el'], up)

        obj = casa
        up = pos.isUp(obj['name'])
        print "%s el=%f, up=%s" % (obj['name'], obj['el'], up)

        obj = taua
        up = pos.isUp(obj['name'])
        print "%s el=%f, up=%s" % (obj['name'], obj['el'], up)
 
        obj = vira
        print "%s el=%f, up=%s" % (obj['name'], obj['el'], up)
 
        obj = radec
        up = pos.isUp(None, None, radec['ra'], radec['dec'])
        print "%s el=%f, up=%s" % (obj['name'], obj['el'], up)

        first_up = ATAPositions.getFirstInListThatIsUp(['moon', 'casa', 'taua', 'vira', 'goes-16']);
        if(first_up == None):
            print "No sources are up and far enough from the sun/moon!"
        elif(first_up['status'] == 'next_up'):
            print "No sources up, next is %s in %d minutes" % (first_up['source'], first_up['minutes'])
        else:
            print"First in list that is up: %s: az=%.4f, el=%.4f" % (first_up['source'], first_up['az'], first_up['el'])

    run_tests()


