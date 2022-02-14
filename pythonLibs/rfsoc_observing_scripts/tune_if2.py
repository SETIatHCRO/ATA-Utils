#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
import atexit
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada, snap_if
import numpy as np
import sys
import time

import argparse
import logging

import os

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    antlo_list = [
            "1cB", "1eB", "1gB", "1hB",
            "1kB", "2aB", "2bB", "2cB",
            "2eB", "2hB", "2jB",
            "2lB", "2mB", "3cB", "3dB",
            "3lB", "4jB", "5bB", "4gB"]

    snap_if.tune_if_antslo(antlo_list)


if __name__ == "__main__":
    main()
