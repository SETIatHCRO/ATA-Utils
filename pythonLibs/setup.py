import setuptools
import version
import sys

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='ATA-Utils-pythonLibs',
    version=version.__version__,
    #install_requires=['ephem','astropy','numpy','tftpy','pyuvdata<=1.4;python_version<"3"','pyuvdata;python_version>"3.5"'],
    install_requires=['ephem','astropy','numpy','tftpy'],
    description='python utility scripts for ATA (private repo)',
    license='MIT',
    packages=['ATATools','ATAobs','SNAPobs','OnOffCalc','OnOffCalc.flux','OnOffCalc.yFactor','OnOffCalc.misc','OnOffCalc.filterArray'],
    author='Dr. Janusz S. Kulpa',
    author_email='kulpaj.dev@gmail.com',
    keywords=['ATA'],
    long_description=long_description,
    url="https://github.com/SETIatHCRO/ATA-Utils/",
    #entry_points={'console_scripts': ['GPIBLOControl = GPIBLOControl.GPIBLOControl:main']},
)
