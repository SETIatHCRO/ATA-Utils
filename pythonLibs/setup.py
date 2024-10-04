import setuptools
import version
import sys

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='ATA-Utils-pythonLibs',
    version=version.__version__,
    #install_requires=['ephem','astropy','numpy','tftpy','pyuvdata<=1.4;python_version<"3"','pyuvdata;python_version>"3.5"'],
    install_requires=['ephem','astropy','numpy','tftpy', 'pandas', 'bottleneck','plotly','dash','requests', 'toml', 'pytz'],
    description='python utility scripts for ATA (private repo)',
    license='MIT',
    packages=['ATAdb', 'ATATools','ATAobs','SNAPobs','SNAPobs.snap_dada', 'SNAPobs.snap_hpguppi', 
              'OnOffCalc','OnOffCalc.flux','OnOffCalc.yFactor','OnOffCalc.misc','OnOffCalc.filterArray'],
    include_package_data=True,
    author='Dr. Wael Farah',
    author_email='wfarah@seti.org',
    keywords=['ATA'],
    long_description=long_description,
    url="https://github.com/SETIatHCRO/ATA-Utils/",
    scripts=['SNAPmon/atasnapmon.py',
        'SNAPobs/snap_hpguppi/scripts/meta_marshall.py',
        'SNAPobs/snap_hpguppi/scripts/set_postproc_keys.py',
        'SNAPobs/snap_hpguppi/scripts/set_hashpipe_keys.py',
        'SNAPobs/snap_hpguppi/scripts/populate_meta.py',
        'SNAPobs/snap_hpguppi/scripts/start_record_in_x.py',
        'ATAPointing/pointing_elxel_plot.py',
        'ATAPointing/pointing_azel_table.py',
        'ATAPointing/pointing_azel_print.py',
        'ATATools/scripts/atacheck',
        'ATATools/scripts/ataiftune',
        'ATATools/scripts/atasetifgain',
        'ATATools/scripts/atagetifgain',
        'ATATools/scripts/ataplotadc',
        'ATATools/scripts/atafindnearestcalibrator',
        'ATADelayEngine/atadelayengine']
    #entry_points={'console_scripts': ['GPIBLOControl = GPIBLOControl.GPIBLOControl:main']},
)
