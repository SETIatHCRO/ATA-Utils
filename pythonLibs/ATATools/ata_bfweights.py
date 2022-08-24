#!/usr/bin/python3

"""
Python utility classes/functions to use to read and write
ATA beamformer weights files
"""

import numpy as np

ANTENNA_NAME_LENGTH = 2 # ATA-style antennas; e.g. 1a,1f,3c,4g
ANT_DELIM = "\0"
FILE_DTYPE = np.complex128

class BeamWeights(object):
    """
    A BeamWeights object contains the weights for a set of antennas with
    a specific number of frequency channels and polarizations to be used 
    as an input to he beamformer.

    The weights are by default complex128, therefore phase and amplitude 
    weights can be loaded unto the beamformer.

    A description of the binary file format, see this:
    https://github.com/MydonSolutions/ata_antenna_weights_binary

    Parameters
    ----------
    fname : str
        The filename to read the weights from

    Attributes
    ----------
    ant_weights : np.ndarray
        The complex weights matrix, with shape = (nants, nchans, npols)
    ant_list : array-like
        The antenna names
    
    """
    def __init__(self, fname):
        self.fname = fname

        self._fio = open(self.fname, "rb")
        self._read_header()
        self._read_weights()
        
        # Make sure there is nothing left in file
        t = self._fio.read(1)
        if t:
            raise RuntimeError("File still contains bytes?")
        self._fio.close()

    def _read_header(self):
        self.nants  = int.from_bytes(self._fio.read(4), byteorder='little')
        self.nchans = int.from_bytes(self._fio.read(4), byteorder='little')
        self.npols  = int.from_bytes(self._fio.read(4), byteorder='little')
        self._get_ant_names()

    def _get_ant_names(self):
        ant_bin = self._fio.read((ANTENNA_NAME_LENGTH + 1)*self.nants)
        ant_bin = ant_bin.decode('ascii')
        self.ant_names = []
        stride = ANTENNA_NAME_LENGTH + len(ANT_DELIM)

        for i in range(self.nants):
            ant = ant_bin[i*stride:(i+1)*stride]
            assert ant[ANTENNA_NAME_LENGTH:] == ANT_DELIM,\
                    "Something's wrong with file format"
            self.ant_names.append(ant[:ANTENNA_NAME_LENGTH])

    def _read_weights(self):
        """
        Weights are have the shape (nants, nchans, npols)
        """
        self.ant_weights = np.fromfile(self._fio, dtype=FILE_DTYPE,
                count=self.nants*self.nchans*self.npols)
        self.ant_weights =\
                self.ant_weights.reshape(self.nants, self.nchans, self.npols)

    def write_weights(self, fname):
        write_weights(fname, self.ant_names, 
                self.ant_weights) 


def write_weights(fname, ant_list, ant_weights):
    """
    Write out ATA antenna weight file

    Parameters
    ----------
    fname : str
        Name of file
    ant_list : list
        List of antenna names
    ant_weights : np.array
        Antenna weights. Assumes shape = (nants, nchans, npols)

    """
    nants, nchans, npols = ant_weights.shape
    _check_consistency(ant_list, ant_weights,
            nants, nchans, npols)
    fio = open(fname, "wb")

    fio.write(nants.to_bytes(4, byteorder='little', signed=False))
    fio.write(nchans.to_bytes(4, byteorder='little', signed=False))
    fio.write(npols.to_bytes(4, byteorder='little', signed=False))
    fio.write((ANT_DELIM.join(ant_list)+ANT_DELIM).encode('ascii'))
    fio.write(ant_weights.tobytes())


def _check_consistency(ant_list, ant_weights,
        nants, nchans, npols):
    """
    Check, as much as possible, whether the input is able to be 
    written to a antenna weight file
    """
    assert len(ant_list) == nants,\
            "Len(ant_list) and nants are different"
    assert np.shape(ant_weights) == (nants, nchans, npols),\
            "Make sure ant_weights have dim=(nants, nchans, npol)"
    assert ant_weights.dtype == FILE_DTYPE,\
            "Make sure dtype of ant_weights is: %s" %FILE_DTYPE
    for i in ant_list:
        assert len(i) == ANTENNA_NAME_LENGTH,\
            "Make sure all antenna names have %i length" %ANTENNA_NAME_LENGTH
