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
Minicircuits rf switch controller control.

rfswitch <ant|antPol>
 switches the RF switch to the specified ant (does bot pols) or single ant pol.
 or
rfswitch -info <ant|antPol>
 -info <ant|antpol>  will print out the RF switch hookup for an ant or antpol.
 -info all will print out all hookup info.
Will print OK\n if successful. Otherwise an error will be reported.
**REMEMBER to run as root!!**
```

Example: sudo ./rfswitch 1fx (selects just 1fx)

Example: sudo ./rfswitch 1f (selects 1fx and 1fx)

Example: sudo ./rfswitch -info 1f 

Example: sudo ./rfswitch -info all 

**atten**

```
Minicircuits attenuator control.

atten <dB> <ant|antPol>
  attenuation, in dB 0.0 to 31.75
    -1 will print out the part number and serial number then exit.
   or
atten -discover
  discover all attenuators on the USB bus
Will print OK\n if successful. Otherwise an error will be reported.
**REMEMBER to run as root!!**
```

Example: sudo ./atten 20.5 1fx (for just the one pol)

Example: sudo ./atten 20.5 1f (for both pols)




  
