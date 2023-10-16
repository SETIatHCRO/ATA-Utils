The general strategy for reducing ATA imaging data is the following.

- Copy data to your working area from the network storage, with optional averaging.
- Combine all of the scans within your observation, and both LOs.
- Run the calibration and basic imaging script, which will probide calibrated data producs, initial images, and flux estimates for calibrators.
- Manuall clean target field.
- NOTE: These routines currently only opperate on a final measurement set consisting of a single flux calibrator, phase calibrator, and target field. 

## copy_compress_new_p002.py

This script is run in your home directory on the ATA machines to create a local averaged copy of your observing project (in this example p002) from the network storage. This script will copy the relevant data over to your home area, convert them from uvh5 to the measurement set format, perform flagging at full resolution, and then averaging them in frequeny and time.

There are a few lines that should be edited by the user. Firstly `mymstransform_script = '/home/jbright/scripts/p002_mstransform.py'` should point to a python script in your user area that will be run by casa and should contain an mstransform task. An example can be found in ATA-Utils/ImagingScripts/. Next the `project_directory = '/mnt/dataz-netStorage-40G/projects/p002'` line should be pointed to the project directory on the network storage where your uvh5 data lives. Finally `runs = glob.glob(project_directory + '/' + '2023-10-*')` allows the user to select subsets of their project data if required, e.g. in this case I only want to copy data taken in Oct. 2023. This format of this might change depending on the postprocessor you are using, but the principle remains the same. The result of running this script within a folder in your home area should be a series of directories, one for each observing session, constaining measurements sets (one for each LO) for each scan taken as part of the observation.

## Combining measurement sets

Combining the individual measurement sets within each observing directory (those with affix `_measurement_sets`) is simple using the CASA task `concat`. Simply use the `glob` module with `vis=glob.glob('*/*.ms')` to select all data for combination into a single measurement set which can be named as desired. NOTE: only the last scan on a flux calibrator should be combined into the concat measurement set, as the first was used to update the delays and phases and so exisits on an old delay/phase model. 

## fix_scans.py

This is a very simple script to fix the fact that when combining measurement sets created from uvh5 files, scan boundaries are not incremented correctly. This script iterates over the data and increments the scan counter each time a new field is visited. This is important for calibration routines which rely on breaking at scan boundaries. This script needs to be edited with the name of the measurement set which is a concatenation of all of the scans and LOs. 

## phase_reference_calibration_imaging.py

The bulk of the work is done by the `phase_reference_calibration_imaging.py` script, which performs first generation calibration and then imaging of target data. This requires some minor modification, e.g. `bpcal = '<NAME OF FLUXCAL>'`, `pcal = '<NAME OF PHASE CAL>'`, `target = '<NAME OF TARGET>'`. The user will also have to set the reference antenna (`myrefant = 'MY REFERENCE ANTENNA'`) and the name of the concatenated measurement set (`myvis = '<NAME OF MEASUREMENT SET>'`). Note that in the current iteration, the initial flagging step is not performed as the data were flagged before averaging. 

This script will produce various auxilliary products that will be of interest. Firstly a series of calibration tables with the format e.g. <`NAME OF FLUXCAL`>.B0, which contains the bandpass solutions. Secondly, calibrated measurement sets for each taget field are split out like `<TARGET NAME>_noauto_1GC.ms`. Finally, image products and flux estimates for the calibrators are stored in the `IMAGES/<TARGET NAME>` directories. Multiple clean iterations for the calibrators are performed to account for a lowering noise floor, and the `<PREFIX>_iter2.image.tt0` file is the best image. A file called `fitting_results.txt` contains an estimated flux for the calibrator and a (statistical) error. The real error will be dominated by systematics at the 5% to 10% level. The target directory just contains a dirty image.

Note that if the two LOs you have used are tuned to very disparate frequencies each LO should be calibrated independently. 

## Next steps
- Automated imaging of the target field using smart masking with the https://github.com/ratt-ru/breizorro package.
- Atomated self calibration.
- Better determination of cell sizes.
- Source catalogues using source finding.
- Exploring structure in the calibrator bandpass at the 10% level.
- Further user information, including uv-coverage, source elevations, etc. presented in a friendly way.
