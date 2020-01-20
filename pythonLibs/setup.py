import setuptools
import version

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='pythonLibs_for_ATA-Utils',
    version=version.__version__,
    description='python utility scripts for ATA (private repo)',
    license='MIT',
    packages=['OnOffCalc','ATATools'],
    author='Dr. Janusz S. Kulpa',
    author_email='kulpaj.dev@gmail.com',
    keywords=['ATA'],
    long_description=long_description,
    url="https://github.com/SETIatHCRO/ATA-Utils/",
    #entry_points={'console_scripts': ['GPIBLOControl = GPIBLOControl.GPIBLOControl:main']},
)
