import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="attenuatorMain",
    version="1.0.1",
    author="Alexander Pollak",
    author_email="apollak@seti.org",
    description="Program for controlling original Attemplifiers for 8x dual channel IF-Gain-Control-Module ",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SETIatHCRO/ATA-Utils/tree/master/AttemplifierControl",
    py_modules=['attenuatorMain'],
    entry_points={'console_scripts': ['Attemplifier = .attenuatorMain.attenuatorMain:main', 'TestRun =.attenuatorMain.Attemplifier_test:main']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
