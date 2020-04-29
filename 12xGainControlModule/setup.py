import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="attenuatorMain",
    version="0.0.1",
    author="Helen Peng",
    author_email="helenpeng@berkeley.edu",
    description="Program for controlling attenuator system designed by Alexander Pollak at SETI institute",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SETIatHCRO/ATA-Utils/tree/master/12xGainControlModule",
    py_modules=['attenuatorMain'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
