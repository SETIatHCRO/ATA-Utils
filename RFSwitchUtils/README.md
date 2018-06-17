Program to control the Mini Circuits RF switch PN: USB-1SP8T-63H
and Mini Circuits attenuator PN: RUDAT-6000-30

Jon Richards, SETI Institute. June 06, 2018

These are Linux programs derived from
https://www.minicircuits.com/softwaredownload/Prog_Examples_Troubleshooting.pdf

To prepare your system, type the following:

  1. Download libhid-0.2.16.tar.gz from somewhere, unzip it.
  2. sudo apt-get install libusb-dev
  3. cd libhid-0.2.16
  4. ./configure --enable-werror=no
  5. make
  6. sudo make install
  7. sudo ldconfig

To build the program:

  make
    and then optionally to install into /usr/local/bin:
  sudo make install

Must be run as root. Help is available by runiing rfswitch or atten without
command line arguments.

**rfswitch**

Minicircuits rf switch controller. PN: USB-1SP8T-63H

```
rfswitch <state> <rf switch number>
  state = 
    -1 to print out the serial number and part number only, then exits.
    -2 to print out the switch number that is active, then exits.
    1 .. 8, turn on a switch, turn the others off
  rf switch number (as of June 06, 2018)
    0 == left unit, SN: 1180422005
    1 == right unit, SN: 1180422007
    (they are labeled below each unit)
Will print OK\n of successful. Otherwise an error will be reported.
**REMEMBER to run as root!!**
```

**atten**

```
Minicircuits attenuator. PN: RUDAT-6000-30

atten <db> <rf switch number>
  attenuation, in db 0.0 to 31.75
    -1 will print out the part number and serial number then exit.
  attenuator number (as of June 06, 2018)
    0 == left unit, SN: 11803290005
    1 == right unit, SN: 11803290019
    (they are labeled below each unit)
Will print OK,<atten level read from unit>\n if successful. Otherwise an error will be reported.
**REMEMBER to run as root!!**
```




  
