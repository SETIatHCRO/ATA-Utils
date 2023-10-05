The general strategy for reducing ATA imaging data is the following.

- Copy data to your working area from the network storage, with optional averaging.
- Combine all of the scans within your observation, and both LOs.
- Run the calibration and basic imaging script, which will probide calibrated data producs, initial images, and flux estimates for calibrators.
- Manuall clean target field.

## copy_compress_new_p002.py

This script is run in your home directory on the PI machines to create a local averaged copy of your observing project (in this example p002) from the network storage. This script will copy the relevant data over to your home area, convert them from uvh5 to the measurement set format, perform flagging at full resolution, and then averaging them in frequeny and time.

There are a few lines that should be edited by the user. Firstly `mymstransform_script = '/home/jbright/scripts/p002_mstransform.py'` should point to a python script in your user area that will be run by casa and should contain an mstransform task. An example can be found in ATA-Utils/ImagingScripts/. Next the `project_directory = '/mnt/dataz-netStorage-40G/projects/p002'` line should be pointed to the project directory on the network storage where your uvh5 data lives. Finally `runs = glob.glob(project_directory + '/' + '2023-10-*')` allows the user to select subsets of their project data if required, e.g. in this case I only want to copy data taken in Oct. 2023. This format of this might change depending on the postprocessor you are using, but the principle remains the same. The result of running this script within a folder in your home area should be a series of directories, one for each observing session, constaining measurements sets (one for each LO) for each scan taken as part of the observation.

## Combining measurement sets

Combining the individual measurement sets within each observing directory (those with affix `_measurement_sets`) is simple using the CASA task `concat`. Simply use the `glob` module with `vis=glob.glob('*/*.ms')` to select all data for combination into a single measurement set which can be named as desired. NOTE: only the last scan on a flux calibrator should be combined into the concat measurement set, as the first was used to update the delays and phases and so exisits on an old delay/phase model. 

## fix_scans.py

This is a very simple script to fix the fact that when combining measurement sets created from uvh5 files, scan boundaries are not incremented correctly. This script iterates over the data and increments the scan counter each time a new field is visited. This is important for calibration routines which rely on breaking at scan boundaries. This script needs to be edited with the name of the measurement set which is a concatenation of all of the scans and LOs. 

## 

## Next steps
