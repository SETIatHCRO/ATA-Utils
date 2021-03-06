import setuptools
import version

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='GPIBLOControl',
    version=version.__version__,
    description='python package controls the HP 83731B via the prologix GPIB to Ethernet adapter',
    license='MIT',
    packages=['GPIBLOControl'],
    author='Dr. Janusz S. Kulpa',
    author_email='kulpaj.dev@gmail.com',
    keywords=['HP 83731B','GPIB'],
    long_description=long_description,
    url="https://github.com/SETIatHCRO/ATA-Utils/",
    entry_points={'console_scripts': ['GPIBLOControl = GPIBLOControl.GPIBLOControl:main']},
)
