import setuptools
import version

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='autotune',
    install_requires=['ATASQL>=0.0.2'],
    version=version.__version__,
    description='python package for auto tune',
    license='MIT',
    packages=['ataautotune'],
    author='Dr. Janusz S. Kulpa',
    author_email='kulpaj.dev@gmail.com',
    keywords=['SQL','PAX'],
    long_description=long_description,
    url="https://github.com/SETIatHCRO/ATA-Utils/",
    entry_points={'console_scripts': ['ataautotune = ataautotune.ataautotune:main']},
)
