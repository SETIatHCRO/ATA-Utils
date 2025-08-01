import setuptools
import glob
import version
import sys

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='ATA-Utils-pythonLibs',
    version=version.__version__,
    #install_requires=['ephem','astropy','numpy','tftpy','pyuvdata<=1.4;python_version<"3"','pyuvdata;python_version>"3.5"'],
    install_requires=['ephem','astropy','numpy','tftpy', 'pandas', 'bottleneck','plotly','dash',
        'requests', 'toml', 'pytz', 'pytk', 'tkcalendar', 'parse', 'redis', 'matplotlib',
        'slack-sdk', 'ansible', 'pyuvdata', 'python-casacore',
        'hashpipe_keyvalues @ git+https://github.com/MydonSolutions/HashpipeKeyValues_py.git',
        'odsutils @ git+https://github.com/david-deboer/odsutils.git'],
    description='python utility scripts for ATA (private repo)',
    license='MIT',
    packages=['ATAdb', 'ATATools','ATAobs', 'ATAgui', 'SNAPobs','SNAPobs.snap_dada', 'SNAPobs.snap_hpguppi', 
              'OnOffCalc','OnOffCalc.flux','OnOffCalc.yFactor','OnOffCalc.misc','OnOffCalc.filterArray'],
    include_package_data=True,
    author='Wael Farah, Ross Donnachie',
    author_email='wfarah@seti.org, radonnachie@gmail.com',
    keywords=['ATA'],
    long_description=long_description,
    url="https://github.com/SETIatHCRO/ATA-Utils/",
    scripts=['SNAPmon/atasnapmon.py',
        'SNAPobs/snap_hpguppi/scripts/meta_marshall.py',
        'SNAPobs/snap_hpguppi/scripts/set_postproc_keys.py',
        'SNAPobs/snap_hpguppi/scripts/set_hashpipe_keys.py',
        'SNAPobs/snap_hpguppi/scripts/populate_meta.py',
        'SNAPobs/snap_hpguppi/scripts/sync_streams.py',
        'SNAPobs/snap_hpguppi/scripts/configure_antenna_streams.py',
        'SNAPobs/snap_hpguppi/scripts/start_record_in_x.py',
        'RfsocConfigurationScripts/rfsocs_deprogram.py',
        'RfsocConfigurationScripts/rfsocs_fix_clock.bash',
        'RfsocConfigurationScripts/rfsocs_reprogram_continuum.bash',
        'RfsocConfigurationScripts/rfsocs_reprogram_spectralline.bash',
        'RfsocConfigurationScripts/rfsocs_set_equilizers.bash',
        'ATAPointing/pointing_elxel_plot.py',
        'ATAPointing/pointing_azel_table.py',
        'ATAPointing/pointing_azel_print.py',
        'ATAgui/scripts/ataobsgui',
        'ATADelayEngine/atadelayengine'] + glob.glob('ATATools/scripts/ata*')
    #entry_points={'console_scripts': ['GPIBLOControl = GPIBLOControl.GPIBLOControl:main']},
)
