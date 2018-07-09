from __future__ import division

import sys
import numpy as np, scipy.io
import pickle
import os
import glob
import matplotlib.pyplot as plt

mylist = sorted([f for f in glob.glob("psr*.raw")])	
mylist = sorted([f for f in glob.glob("psrb0950+08_2e_rf3000_obsid18_1529883544.raw")])		
mylist = sorted([f for f in glob.glob("psrb0329+54_4j_rf3000_obsid28_1529944749.raw")])


	

print mylist

for file in mylist:
	pieces = file.split("_")
	freq = float (pieces[2].split("rf")[1]) + 200

	mjd = float(pieces[len(pieces)-1].split(".",1)[0])/86400.0 + 2440587.5 - 2400000.5
	 
	command = "filterbank_mkheader -o tmphdr -nifs 1 -fch1 " + str(freq) + " -source B0329+54 -filename foo.test -telescope ATA -src_raj 033259.368 -src_dej +543443.57 -tsamp 4660.33777 -foff 0.2197265625 -nbits 32 -nchans 2048 -tstart " + str(mjd)
	#command = "filterbank_mkheader -o tmphdr -nifs 1 -fch1 " + str(freq) + " -source B0950+08 -filename foo.test -telescope ATA -src_raj 095309.3 -src_dej +075536.0 -tsamp 4660.33777 -foff 0.2197265625 -nbits 32 -nchans 2048 -tstart " + str(mjd)
	#command = "filterbank_mkheader -o tmphdr -nifs 1 -fch1 " + str(freq) + " -source B2021+51 -filename foo.test -telescope ATA -src_raj 202249.8730 -src_dej +515450.233 -tsamp 4660.33777 -foff 0.2197265625 -nbits 32 -nchans 2048 -tstart " + str(mjd)
	#command = "filterbank_mkheader -o tmphdr -nifs 1 -fch1 " + str(freq) + " -source B1933+16 -filename foo.test -telescope ATA -src_raj 193547.8259 -src_dej +161639.9863 -tsamp 4660.33777 -foff 0.2197265625 -nbits 32 -nchans 2048 -tstart " + str(mjd)

	print command	
	
	
	os.system(command)

	command = "cat tmphdr " + file + " > " + file + ".2.fil"

	os.system(command)
