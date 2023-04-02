# Processing ATA multibeam observation data (first made to process TRAPPIST-1 data)
NOTE: Data directory tree structure is important for processing files with bash script: 
base_project_directory -> observations -> integrations -> nodes -> filterbank files
However, the cross correlation script is agnostic to the directory structure and number of beams.
It will recursively scan all subfolders of the input directories for the requisite dat and fil files.

1. Use tset_bash.sh with hardcoded observation directory to run fscrunch and turboSETI.
    - h5 or fil files --> dat and log files
    - fscrunch allows increased sensitivity to larger drift rates

2.  CCFnbeam.py uses cross-correlation to identify the same signals in both beams
    - dats and logs --> stats histograms, correlation vs SNR plot, output log, and csv
    - first cross references hits like the old method to pare down the hit list
    - then correlates frequency ranges of remaining hits in target beam with other beams
    - should work with any number of beams
    - uses pickle files to resume interrupted scripts
    - slower than old method because it draws blimpy waterfall data slice for each hit in all beams

3. plot_CCF_hits.py OR plot_target_hits.py, uses plot_target_utils.py to plot the hits in the input csv.
    - csv --> waterfall plots
    - input arguments allow for filtering of csv
