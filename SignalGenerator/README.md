# SignalGenerator

Contains scripts to remote control signal generators via ethernet.

## SRS_SG384_Control.py
Program to control the Stanford Reseach Systems SG384 Signal Generator.
Frequency range: DC-4.05GHz

```
Usage: Usage srs_sg384_control.py options

Display or change the values of SRS SG384 Signal Generator

Options:
  -h, --help            show this help message and exit
  -p, --print           Query and print current values
  -f FREQ, --freq=FREQ  Set clock value in MHz
  -a AMP, --amp=AMP     Set amplitude
```
