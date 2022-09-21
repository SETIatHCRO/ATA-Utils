#!/opt/mnt/miniconda3/bin/python
import numpy as np
import sys
from ATATools import ata_bfweights
import argparse

WEIGHTS_1_0J = "/opt/mnt/share/ant_weights_1+0j.bin"
WEIGHTS_NEW = "./weights.bin.new"

def main():
    parser = argparse.ArgumentParser(description=
            "Convert weights.txt into binary weight file")
    parser.add_argument('weight_file', type=str, 
            help='Weights.txt file')
    parser.add_argument('--weights_1_0j', type=str,
            help='Binary weights with 1+0j [default: %s]' %WEIGHTS_1_0J,
            default=WEIGHTS_1_0J)
    parser.add_argument('--weights_new', type=str,
            help='Output binary weight name',
            default=WEIGHTS_NEW)

    args = parser.parse_args()

    antpol_gains = np.loadtxt(args.weight_file, dtype=str)
    bw = ata_bfweights.BeamWeights(args.weights_1_0j)

    for antpol, gain in antpol_gains:
        ant, pol = antpol[:2], antpol[2:]
        ant_idx = bw.ant_names.index(ant.lower())
        pol_idx = 0 if pol.lower() == "x" else 1

        bw.ant_weights[ant_idx, :, pol_idx] *= float(gain)

    bw.write_weights(args.weights_new)

if __name__ == "__main__":
    main()
