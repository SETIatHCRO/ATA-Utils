#!/opt/mnt/miniconda3/bin/python
"""
Script to get frequency in GHz from a uvh5 file
Will print frequency to stdout
"""

from pyuvdata import UVData
import sys

import argparse


def main():
    parser = argparse.ArgumentParser(description=
            'Print some UVH5 header info.\nNote that the output elements '\
            'will appear one after the other according to the description '\
            'list')

    parser.add_argument(dest='uvfile', type=str,
            help="Name of input UVH5 file")

    parser.add_argument('-f', dest='freq', action='store_true',
            help='Print center frequency in GHz')
    parser.add_argument('-s', dest='source', action='store_true',
            help='Print object name')

    args = parser.parse_args()

    uv = UVData()
    uv.read_uvh5(args.uvfile, read_data=False)

    output = []

    if args.freq:
        output += ["%.9f" %(uv.freq_array.mean() * 1e-9)]
    if args.source:
        output += [uv.object_name]

    print(" ".join(output))

if __name__ == "__main__":
    main()
