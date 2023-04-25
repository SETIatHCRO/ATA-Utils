# Processing ATA multibeam observation data (first made to process TRAPPIST-1 data)
NOTE: Data directory tree structure is important for processing files with the old tseti_bash.sh script: 
base_project_directory -> observations -> integrations -> nodes -> filterbank files
However, the newer basic_tseti.sh and tseti_fsrunch.sh scripts, as well as the DOTS algorithm are agnostic to the directory structure and number of beams, so long as the subdirectory tree for the filterbank/h5 files is the same as the subdirectory tree for the dat files.
These scripts will recursively scan all subfolders of the input directories for the requisite dat and fil/h5 files.

1. Use a bash script to run a dedoppler search on all beamformed filterbank files using turboSETI, with or without fscrunch for higher drift rate coverage.
    - h5 or fil files --> dat and log files
    - fscrunch allows increased sensitivity to larger drift rates

2.  DOTnbeam.py uses dot products and other functions in DOT_utils.py to score signals in the target beam
    - dats and logs --> stats histograms, DOTScore vs SNR plot, output log, and csv
    - first cross references hits with identical frequencies (within 2 Hz) to pare down the hit list
    - then correlates frequency ranges of remaining hits in target beam with other beams using a dot product
    - should work with any number of beams
    - uses pickle files to resume interrupted scripts
    - Somewhat slow because it draws blimpy waterfall data slice for each hit in all beams, and hits with large drift rates create large data slices.

3. plot_DOT_hits.py, uses plot_utils.py to plot the hits in the input csv.
    - csv --> waterfall plots
    - input arguments allow for filtering of csv
    - defaults to 1000 lowest scored hits
