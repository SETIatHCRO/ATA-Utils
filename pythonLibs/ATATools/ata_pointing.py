import numpy as np
from .ata_rest import ATARest, ATARestException


ARC_SEC = 1.0 / 3600.0
DEG2RAD = np.pi / 180.0
RAD2DEG = 180.0 / np.pi
SEC2RAD = np.pi / 180.0 / 3600.0
PIBY2 = np.pi / 2.0

MAX_EL_FOR_CORRECTION = 1.5533430342749532 #radians, 89.0 degrees


class modelCoeff:
    pass


class PointingModel():
    """
    An exact translation from the java code that exists in:
    obs@control:/hcro/atasys/ata/src/ata/trajectory/PointingModel.java
    """
    _TPOINT_COEFFS = [
        'IA', 'AN', 'AW', 'CA', 'NPAE', 'ACES', 'ACEC', 'HASA2', 'HACA2',
        'IE', 'ECES', 'ECEC'
    ]

    def __init__(self, ant):
        self.antName = ant
        self.mCoef = modelCoeff()

        pointing_model = ATARest.get('/antenna/{:s}/pm'.format(ant))
        for key, value in pointing_model.items():
            if key in self._TPOINT_COEFFS:
                setattr(self.mCoef, key, value)
            else:
                setattr(self, key, value)

    def avoidImpossibleEl(self, el_rad):
        """
        Keeps you away from the region around zenith that can't be reached
        if you have a collimation error (CA).
       
        Note: We're not using NPAE because it makes the model unstable.
        It is not recommended, but if you insist on using it, then you
        must modify avoidImpossibleEl() to operate on the sum of CA and NPAE
        where it now operates on CA only.
        @param el_rad input elevation in radians
        @return coerced elevation in radians
        """
        # the pointing model makes no sense very close to zenith
        # (you could never get there anyway cause these are nonperp terms)
        avoidance_zone = np.abs(self.mCoef.CA) * SEC2RAD + 0.0001;
        if ( el_rad <  0.0          ):
            return 0.0
        if ( el_rad > (PIBY2 - avoidance_zone)):
          return (PIBY2 - avoidance_zone);
        return el_rad;



    def applyTPOINTCorrections(self, Az, El, IR):
        # break out the individual tracks
        #Track az_track = new Track(track_in.getAz());
        #Track el_track = new Track(track_in.getEl());
        #Track ir_track = new Track(track_in.getIR());

        # convert to the "coordinate system" of the encoders
        # calculations are done in radians
        az = Az * DEG2RAD;
        el = self.avoidImpossibleEl(El * DEG2RAD);

        # pointing terms MUST be applied serially, not in parallel
        az, el = self.applyECEC  (az, el);
        az, el = self.applyECES  (az, el);
        az, el = self.applyIE    (az, el);

        az, el = self.applyHACA2 (az, el);
        az, el = self.applyHASA2 (az, el);
        az, el = self.applyACEC  (az, el);
        az, el = self.applyACES  (az, el);
        az, el = self.applyNPAE  (az, el);
        az, el = self.applyCA    (az, el);
        az, el = self.applyAW    (az, el);
        az, el = self.applyAN    (az, el);
        az, el = self.applyIA    (az, el);

        # convert back to degrees
        az = az * RAD2DEG;
        el = el * RAD2DEG;

        return az, el, IR

    def applyECEC(self, az, el):
        el = self.coerceEl(el - SEC2RAD * self.mCoef.ECEC * np.cos(el))
        return az, el

    def applyECES(self, az, el):
        el = self.coerceEl(el - SEC2RAD * self.mCoef.ECES * np.sin(el))
        return az, el

    def applyIE(self, az, el):
        el = self.coerceEl(el - SEC2RAD * self.mCoef.IE)
        return az, el

    def applyHACA2(self,  az, el):
        az = az + SEC2RAD * self.mCoef.HACA2 * np.cos(2.0 * az)
        return az, el

    def applyHASA2(self, az, el):
        az = az - SEC2RAD * self.mCoef.HASA2 * np.sin(2.0 * az)
        return az, el

    def applyACEC(self, az, el):
        az = az - SEC2RAD * self.mCoef.ACEC * np.cos(az)
        return az, el

    def applyACES(self, az, el):
        az = az + SEC2RAD * self.mCoef.ACES * np.sin(az)
        return az, el

    def applyNPAE(self, az, el):
        # Prohibit tan(el) from reaching a value too large.
        if (el > MAX_EL_FOR_CORRECTION):
            az = az + SEC2RAD * self.mCoef.NPAE * np.tan(MAX_EL_FOR_CORRECTION)
            return az, el
        az = az + SEC2RAD * self.mCoef.NPAE * np.tan(el)
        return az, el

    def applyCA(self, az, el):
        # Prohibit 1/cos(el) from reaching a value too large.
        if (el > MAX_EL_FOR_CORRECTION):
            az = az + SEC2RAD * self.mCoef.CA / np.cos(MAX_EL_FOR_CORRECTION)
            return az, el
        az = az + SEC2RAD * self.mCoef.CA / np.cos(el)
        return az, el

    def applyAW(self, az, el):
        # Prohibit tan(el) from reaching a value too large.
        if (el > MAX_EL_FOR_CORRECTION):
            az = az + SEC2RAD * self.mCoef.AW * np.cos(az) * np.tan(MAX_EL_FOR_CORRECTION)
            el = self.coerceEl(el - SEC2RAD * self.mCoef.AW * np.sin(az))
            return az, el
        az = az + SEC2RAD * self.mCoef.AW * np.cos(az) * np.tan(el)
        el = self.coerceEl(el - SEC2RAD * self.mCoef.AW * np.sin(az))
        return az, el

    def applyAN(self, az, el):
        # Prohibit tan(el) from reaching a value too large.
        if (el > MAX_EL_FOR_CORRECTION):
            az = az + SEC2RAD *self. mCoef.AN * np.sin(az) * np.tan(MAX_EL_FOR_CORRECTION)
            el = self.coerceEl(el + SEC2RAD * self.mCoef.AN * np.cos(az))
            return az, el
        az = az + SEC2RAD * self.mCoef.AN * np.sin(az) * np.tan(el)
        el = self.coerceEl(el + SEC2RAD * self.mCoef.AN * np.cos(az))
        return az, el

    def applyIA(self, az, el):
        az = az + SEC2RAD * self.mCoef.IA
        return az, el

    def coerceEl(self, el_rad):
        # tan(el) and sec(el) blow up too close to zenith
        # avoid those values
        roundoff_zone = 0.0001;
        if ( el_rad <  0.0 ):
            return 0.0
        if ( el_rad > (PIBY2 - roundoff_zone)):
          return (PIBY2 - roundoff_zone)
        return el_rad


    def to_tpoint_str(self):
        # return a pretty print string of pointing model
        retStr =  "!  AzOffset = %.3f\n" %self.AzOffset
        retStr += "!  ElOffset = %.3f\n" %self.ElOffset
        retStr += "!  IA = %.3f\n" %self.mCoef.IA
        retStr += "!  AN = %.3f\n" %self.mCoef.AN
        retStr += "!  AW = %.3f\n" %self.mCoef.AW
        retStr += "!  CA = %.3f\n" %self.mCoef.CA
        retStr += "!  NPAE = %.3f\n" %self.mCoef.NPAE
        retStr += "!  ACES = %.3f\n" %self.mCoef.ACES
        retStr += "!  ACEC = %.3f\n" %self.mCoef.ACEC
        retStr += "!  HASA2 = %.3f\n" %self.mCoef.HASA2
        retStr += "!  HACA2 = %.3f\n" %self.mCoef.HACA2
        retStr += "!  IE = %.3f\n" %self.mCoef.IE
        retStr += "!  ECES = %.3f\n" %self.mCoef.ECES
        retStr += "!  ECEC = %.3f\n" %self.mCoef.ECEC
        retStr += "!\n"
        return retStr


