#!/usr/bin/env python
from SNAPobs import snap_control
import numpy as np
import sys

def eq_compute_coeffs(rfsoc, target_rms=0.5, medfil_ksize=401, 
        conv_ksize=100, acc_len=50000):
    """
    Get appropriate EQ coefficients to scale FFT output for an appropriate post-quantization
    power target. Do this by grabbing a full bit-precision spectrum, filtering out RFI and smoothing,
    and then computing the scaling required to reach a target power level.

    :param target_rms: The target voltage RMS. This should be specified relative to signed
        data normalized to the range +/-1. I.e., a target_rms of 1./2**7
        represents an RMS of one least-significant bit after quantizing to 8-bits.
        A target_rms of 1./2**3 represents one least-significant bit after quantizing
        to 4-bits.
    :type target_rms: float
    :param medfil_ksize: Size of median filter kernel to use for RFI removal. Should be odd.
    :type medfil_ksize: int
    :param conv_ksize: Convolution kernel size to use for bandpass smoothing.
    :type conv_ksize: int
    :param acc_len: If specified, use this accumulation length for the computation.
        Accumulation length should be sufficiently long to obtain good autocorrelation
        SNR. After the EQ coeffients are obtained, the accumulation length the firmware
        was using before this function was invoked is reloaded.
    :type acc_len: int

    :return: x_coeffs, y_coeffs: A tuple of coefficients. Each is a numpy array of
        floating-point values.
    :rtype: numpy.array, numpy.array
    """

    xx, yy = rfsoc.spec_read(mode='auto', flush=True, normalize=True)
    xx = rfsoc._filter_spectrum(xx, medfil_ksize=medfil_ksize, conv_ksize=conv_ksize)
    yy = rfsoc._filter_spectrum(yy, medfil_ksize=medfil_ksize, conv_ksize=conv_ksize)
    # Generate coefficients by dividing by 2 (to get the power contribution
    # of one of the real/imag parts, and sqrt-ing to get to voltage
    # The resulting coefficients will make the voltage RMS 1
    x_coeff = 1. / np.sqrt(xx / 2.)
    y_coeff = 1. / np.sqrt(yy / 2.)
    # Divide down the coefficients to get the a scale of 1 least-significant bit
    x_coeff *= float(target_rms)
    y_coeff *= float(target_rms)
    return x_coeff, y_coeff

def eq_balance(rfsoc, pol, target_rms=2.**-7 * 8, 
        cutoff=2., medfil_ksize=401, conv_ksize=50):
    """
    Tweak the EQ coefficients for a polarization to target a particular post-EQ
    RMS.

    :param pol: Polarization to equalize.
    :type pol: int

    :param target_rms: The target voltage RMS. This should be specified relative to signed
        data normalized to the range +/-1. I.e., a target_rms of 1./2**7
        represents an RMS of one least-significant bit after quantizing to 8-bits.
        A target_rms of 1./2**3 represents one least-significant bit after quantizing
        to 4-bits.
    :type target_rms: float

    :param cutoff: The scale, relative to the mean coefficient, at which coeffiecients
        are saturated. For example, if the mean coefficient is 1000, and ``cutoff`` is 2,
        coefficients will saturated at a value of 2000. This allows the bandpass
        to still be visible in the equalized data.
    :type cutoff: float


    :param medfil_ksize: Size of median filter kernel to use for RFI removal. Should be odd.
    :type medfil_ksize: int

    :param conv_ksize: Convolution kernel size to use for bandpass smoothing.
    :type conv_ksize: int

    :return: The loaded coefficients as read back. Note that these will be slightly
        different to the loaded coefficients since they will have been saturated
        and quantized to the specifications of the firmware.
    :rtype: Integer coefficients as returned by ``eq_read_coeffs``
    """
    assert pol in [0, 1], "Polarization must be 0 or 1"
    xc, yc = eq_compute_coeffs(rfsoc, target_rms=target_rms, 
            medfil_ksize=medfil_ksize, conv_ksize=conv_ksize)
    xc_mean = xc.mean()
    yc_mean = yc.mean()
    xc[xc>cutoff*xc_mean] = cutoff*xc_mean
    yc[yc>cutoff*yc_mean] = cutoff*yc_mean
    coeffs = [xc, yc]
    rfsoc.eq_load_coeffs(pol, coeffs[pol])
    return rfsoc.eq_read_coeffs(pol)

def main(rfsoc_hostnames: list):
    rfsocs = snap_control.init_snaps(rfsoc_hostnames, load_system_information=True)

    for rfsoc in rfsocs:
        print(rfsoc)
        eq_balance(rfsoc, 0)
        eq_balance(rfsoc, 1)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        main([
            "rfsoc%i-ctrl-%i" %(i,j) 
            for i in [1,2,3,4, 6,7,8,9, 11,12,13,14, 16,17,18,19] for j in [1,2,3,4,5,6,7,8]
        ])
    else:
        main(sys.argv[1:])