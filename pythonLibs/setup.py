import setuptools
import version

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='ATA-Utils-pythonLibs',
    install_requires=['ephem','astropy','numpy','tftpy','pyuvdata'],
    version=version.__version__,
    description='python utility scripts for ATA (private repo)',
    license='MIT',
    packages=['ATATools','SNAPobs','OnOffCalc','OnOffCalc.flux','OnOffCalc.yFactor','OnOffCalc.misc','OnOffCalc.filterArray'],
    author='Dr. Janusz S. Kulpa',
    author_email='kulpaj.dev@gmail.com',
    keywords=['ATA'],
    long_description=long_description,
    url="https://github.com/SETIatHCRO/ATA-Utils/",
    #entry_points={'console_scripts': ['GPIBLOControl = GPIBLOControl.GPIBLOControl:main']},
)
