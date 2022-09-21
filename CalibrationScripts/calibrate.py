#!/home/sonata/src/casa-6.4.0-16/bin/python3
from casatools import table
import numpy as np

import pandas as pd
from yaml import load, Loader
import toml
import os,sys

import argparse

TELINFO_PATH = "./telinfo_ata.toml"

START_CHAN = 352
NCHAN_BP   = 192*7 #1344
NCHAN_PFB  = 2048

ANT_UPDATE = ["1c", "1k", "1h", "1e", "1g", "2a", "2b", "2c",
        "2h", "2e", "2j", "2l", "2m", "3c", "3d", "3l", "4g",
        "5b", "4j", "2k", "4e", "5e"]


def get_antnumb(telinfo, antname):
    for entry in telinfo['antennas']:
        if entry['name'] == antname:
            return entry['number']


def main():
    parser = argparse.ArgumentParser(description='Calibrate delay and phase')
    parser.add_argument('--delay_table', dest='delay_table', type=str,
        help = 'delay table')
    parser.add_argument('--bf_delays', dest='bf_delays', type=str,
        help = 'delay file that was used in the beamformer')
    parser.add_argument('--delay_output', dest='output_delays', type=str,
        help = 'output delay file [defaults to "bf_delays"+".new"]')

    parser.add_argument('--phase_table', dest='phase_table', type=str,
        help = 'phase table')
    parser.add_argument('--bandpass_table', dest='bandpass_table', type=str,
        help = 'bandpass table')
    parser.add_argument('--bf_phases', dest='bf_phases', type=str,
        help = 'phases file that was used in the beamformer')
    parser.add_argument('--phase_output', dest='output_phases', type=str,
        help = 'output phase file [defaults to "bf_phases"+".new"]')

    parser.add_argument('-t', dest='telinfo_path', type=str,
        help = 'path to telinfo [default: %s]' %TELINFO_PATH)

    parser.add_argument('--cfreq', dest='cfreq', type=float,
        help = 'Center frequency of the observation [GHz]')

    args = parser.parse_args()
    delay_table    = args.delay_table
    bf_delays      = args.bf_delays
    delay_output   = args.output_delays

    phase_table    = args.phase_table
    bandpass_table = args.bandpass_table 
    bf_phases      = args.bf_phases
    phase_output   = args.output_phases

    cfreq          = args.cfreq

    # load telinfo path
    telinfo_path = args.telinfo_path if args.telinfo_path else TELINFO_PATH

    if telinfo_path.endswith(".yml"):
        telinfo = load(open(telinfo_path, "r").read(), Loader=Loader)
    elif telinfo_path.endswith(".toml"):
        telinfo = toml.load(telinfo_path)

    if delay_table and phase_table:
        if not args.cfreq:
            raise RuntimeError("Please input sky frequency")

    # =========================
    # Perform delay calibration
    # =========================
    if delay_table:
        print("")
        print("="*79)
        print("Performing delay calibration")
        print("="*79)
        # read delays that were used by the beamformer
        delays_initial = pd.read_csv(bf_delays, sep=" ", index_col=None)

        # read casa's delays
        calK = table()
        calK.open(delay_table)
        delays = np.squeeze(calK.getcol("FPARAM"))
        antnames = calK.getcol("ANTENNA1")

        # residual delays measured by casa
        delays_casa = np.column_stack((antnames, *delays))

        delays_applied = delays_initial.copy()

        for antname in ANT_UPDATE:
            antnumb = get_antnumb(telinfo, antname)
            residuals = np.squeeze(delays_casa[delays_casa[:,0] 
                == antnumb])[1:] # X and Y residuals

            ant_indx = delays_applied[delays_applied['#ant'] == antname].index

            # WF: Feb 18, 2022, replaced += with -=
            # because we inverse conjugated correlator
            delays_applied.loc[ant_indx, 'x'] -= residuals[0]
            delays_applied.loc[ant_indx, 'y'] -= residuals[1]

        # now write the file
        out_delays = delay_output if delay_output else\
                os.path.basename(bf_delays)+".new"
        print("Writing out delay file: "+out_delays)
        delays_applied.to_csv(out_delays, sep=" ", float_format="%.3f", 
                index=False)
        print("Done")


    # =========================
    # Perform phase calibration
    # =========================
    if phase_table:
        print("")
        print("="*79)
        print("Performing phase calibration")
        print("="*79)
        phases_initial = pd.read_csv(bf_phases, sep=" ", index_col=False)
        # read casa's phases
        calG = table()
        calG.open(phase_table)
        phase = np.squeeze(calG.getcol("CPARAM"))
        antnames = calG.getcol("ANTENNA1")

        ang_p = np.angle(phase.T)

        # bandpass
        calBP = table()
        calBP.open(bandpass_table)

        bandp = np.squeeze(calBP.getcol("CPARAM"))
        antnames = calBP.getcol("ANTENNA1")

        ang_b = np.angle(bandp)

        phase_a = ang_p.T[:,np.newaxis,:]

        angbp = phase_a + ang_b

        npol, nchan, nant = angbp.shape

        # If we are applying both delay and phase calibration simultaneously:
        # We have to take out the residual phase offset introduced by the 
        # residual delays that were calculated above and that were not yet 
        # "seen" by the delay engine while the observation was happening
        if delay_table:
            # assuming cfreq is in the middle of the band seen by CASA
            delay_phase_offset = 2*np.pi*(cfreq*1e9)*(delays*1e-9)
            angbp -= delay_phase_offset[:, np.newaxis, :]


        res_bp_final = np.zeros_like(angbp).reshape(nchan, nant*npol)

        for iant in range(nant):
            for ipol in range(npol):
                res_bp_final[:, ipol + iant*npol] = angbp[ipol, :, iant]

        antnames_pol = [str(antname)+pol for antname in antnames
                for pol in ["x","y"]]

        # these are the phases that casa measured
        phases_casa = pd.DataFrame(res_bp_final, columns = antnames_pol)

        phases_applied = phases_initial.copy()

        for antname in ANT_UPDATE:
            antnumb = get_antnumb(telinfo, antname)

            phases_x = phases_casa['%ix' %antnumb]
            phases_y = phases_casa['%iy' %antnumb]

            # WF 24 feb 2022
            # replaced += with -=
            if antname+"x" not in phases_initial.columns:
                phases_applied[antname+"x"] = np.zeros(NCHAN_PFB)
            phases_applied[antname+"x"][START_CHAN:START_CHAN+NCHAN_BP].values[:] -=\
                phases_x.values[:]

            if antname+"y" not in phases_initial.columns:
                phases_applied[antname+"y"] = np.zeros(NCHAN_PFB)
            phases_applied[antname+"y"][START_CHAN:START_CHAN+NCHAN_BP].values[:] -=\
                phases_y.values[:]

        # making sure the phases values are between -pi and +pi
        phases_applied[:] = np.angle(np.exp(1j*phases_applied))

        # now write the file
        out_phases = phase_output if phase_output else\
                os.path.basename(bf_phases)+".new"
        print("Writing out phase file: "+out_phases)
        phases_applied.to_csv(out_phases, sep=" ", float_format="%.3f", 
                index=False)
        print("Done")




if __name__ == "__main__":
    main()
