import numpy as np
from .ata_rest import ATARest, ATARestException


ARC_SEC = 1.0 / 3600.0
DEG2RAD = np.pi / 180.0
RAD2DEG = 180.0 / np.pi
SEC2RAD = np.pi / 180.0 / 3600.0
PIBY2 = np.pi / 2.0

MAX_EL_FOR_CORRECTION = 1.5533430342749532 #radians, 89.0 degrees


class modelCoeff(object):
    pass


class PointingModel():
    """
    An exact translation from the java code that exists in:
    obs@control:/hcro/atasys/ata/src/ata/trajectory/PointingModel.java
    """
    def __init__(self, ant):
        self.antName = ant
        self.mCoef = self._load_pm_coeffs_from_db(ant)

    def _load_pm_coeffs_from_db(self, ant):
        mCoef = modelCoeff()
        pm = ATARest.get('/antenna/{:s}/pm'.format(ant))
        mCoef.IA = pm['IA']
        mCoef.AN = pm['AN']
        mCoef.AW = pm['AW']
        mCoef.CA = pm['CA']
        mCoef.NPAE = pm['NPAE']
        mCoef.ACES = pm['ACES']
        mCoef.ACEC = pm['ACEC']
        mCoef.HASA2 = pm['HASA2']
        mCoef.HACA2 =pm['HACA2']
        mCoef.IE = pm['IE']
        mCoef.ECES = pm['ECES']
        mCoef.ECEC = pm['ECEC']
        return mCoef

    def _get_model_coefficients_test(self, ant):
        # These are 3c's parameters
        # for testing purposes only
        mCoef = modelCoeff()
        mCoef.IA = -396
        mCoef.AN = -112
        mCoef.AW = 66
        mCoef.CA = 298
        mCoef.NPAE = 0
        mCoef.ACES = 0
        mCoef.ACEC = 0
        mCoef.HASA2 = 0
        mCoef.HACA2 = 0
        mCoef.IE = -1831
        mCoef.ECES = 0
        mCoef.ECEC = 0
        return mCoef

    def get_model_coefficients(self, ant):
        # should be replaced with REST call
        return self._get_model_coefficients_test(ant)

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

