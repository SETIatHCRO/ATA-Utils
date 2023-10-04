import os
import shutil
import glob as glob
import astropy
import scipy
import pyuvdata
import pyuvdata
from pyuvdata import UVData

mymstransform_script = '/home/jbright/scripts/p002_mstransform.py'
casapath = '/home/sonata/src/casa-6.4.0-16/bin/casa'

project_directory = '/mnt/dataz-netStorage-40G/projects/p002'
local_directory = os.getcwd()
runs = glob.glob(project_directory + '/' + '2023-10-*')

for run in runs:
	# check for new files to average
	if os.path.isdir('./' + run.split('/')[-1]):
		continue

	print('Found new data: ' + run)
	print('Copying, flagging, and averaging')

	# copy run to home area
	shutil.copytree(run, local_directory+ '/' + run.split('/')[-1])

	# convert files to measuere set
	os.chdir(run.split('/')[-1])
	for folder in glob.glob('uvh5*'):
		os.chdir(folder)

		LoB_files = glob.glob('LoB*/*.uvh5')
		uvd = UVData()
		uvd.read(LoB_files, fix_old_proj=False)
		print("Writing LoB ms file")
		uvd.write_ms(folder + "_b.ms")
		os.system('rm -r LoB*')

		LoC_files = glob.glob('LoC*/*.uvh5')
		uvd = UVData()
		uvd.read(LoC_files, fix_old_proj=False)
		print("Writing LoC ms file")
		uvd.write_ms(folder + "_c.ms")
		os.system('rm -r LoC*')

		os.mkdir('../' + folder + '_measure_sets')
		os.system('mv *.ms ../' + folder + '_measure_sets')
		os.system('mv *.txt ../' + folder + '_measure_sets')
		os.system('mv *.toml ../' + folder + '_measure_sets')
		os.chdir('../')
		os.system('rm -r ' + folder)
		os.chdir(folder + '_measure_sets')
		for ms in glob.glob('*.ms'):
			os.system('aoflagger ' + ms)
			os.system(casapath + ' --nologfile --nogui -c ' + mymstransform_script + ' ' + ms + ' ' + ms.split('.ms')[0] + '_averaged.ms')
			os.system('rm -rf ' + ms)
		os.chdir('../')
	os.chdir('../')

	# delete un-needed files

	# flag at full resolution

	# average in frequency

	#remove full resolution measure set
