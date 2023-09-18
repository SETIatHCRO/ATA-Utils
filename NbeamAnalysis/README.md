# Processing ATA multibeam observation data (first made to process TRAPPIST-1 data)
NOTE: The tseti_bash.sh and tseti_fscrunch.sh bash scripts are old and bespoke. Not recommended for general use.

The pipeline is generally agnostic to the specific directory structure and number of beams, so long as the subdirectory tree for the filterbank/h5 files is the same as the subdirectory tree for the dat files. 

Using basic_tseti.sh to create the dat files should produce identical subdirectory tree structure based on the input folder provided.

These scripts will recursively scan all subfolders of the input directories for the requisite dat and fil/h5 files.

## Processing pipeline steps:

1. Use the basic_tseti.sh bash script to run a dedoppler search on all beamformed filterbank files using turboSETI, with or without fscrunch for higher drift rate coverage.
    - input: h5 or fil files 
    - output: dat and log files
    - fscrunch allows increased sensitivity to larger drift rates
    - adjust the script as needed for your case

2. DOTnbeam.py (or the parallelized version DOTparallel.py) uses functions in DOT_utils.py to score signals in the target beam as compared to the off-target beam, and compute the amount of attenuation in the beams with a SNR-ratio.
    - input: h5s/fils, dats and logs 
    - output: stats histograms, SNR-ratio vs correlation score plot, output log, and csv
    - optional with -sf flag: Cross references hits with identical frequencies (within 2 Hz) and similar SNRs to pare down the hit list.
    - correlates power over the frequency range of each hit in the target beam with the other beams using a fancy dot product (hence the name)
    - should work with any number of beams
    - serial version uses pickle files to resume interrupted scripts
    - the nominal cutoff is an x^2 function times the attenuation value (default=4.0) just to give a rough first guess at what signals might be interesting

3. plot_DOT_hits.py, uses plot_utils.py to plot the hits in the input csv.
    - input: csv 
    - output: waterfall plots
    - input arguments allow for filtering of csv
    - defaults to 500 lowest scored hits with SNR-ratios above the attenuation value (default=4.0)

### Pipeline scripts
basic_tseti.sh
DOTnbeam.py
DOTparallel.py
    DOT_utils.py
plot_DOT_hits.py
    plot_utils.py   

#### Extra scripts
fscrunch.py is a bespoke processing script for using turboSETI with fscrunch blimpy tools in order to search through higher drift rates. fscrunch has inherent problems and the code is old and probably has bugs.

The two injection_*.py scripts were used for very limited injection recovery testing. Not ideally implemented.

hyperseti.py was initially created to test the ongoing development of hyperseti, but it became a testing dumping ground for a number of things.

test.py, test_plots.py, cutoffs.py, are all testing dumping grounds with some diagnostically useful blocks scattered throughout. 