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

NOTE: "sudo make install" does

```
cp ./rfswitch /usr/local/bin
cp ./atten /usr/local/bin
chmod u+s /usr/local/bin/rfswitch
chmod u+s /usr/local/bin/atten
```

Which puts the programs into ./usr/local/bin and sets the SUID/SUID so when you run these programs they run as root.

When antenna port assignments change on the RF switches, or more are added, edit antassign.h with the changes.

**rfswitch**

```

Minicircuits rf switch controller control.

rfswitch <comma sep list of ant pols or ants>
 switches the RF switch to the specified ant (does both pols) or single ant pol.
 Example: "rfswitch 2a,2jx
or
rfswitch -info <ant|antPol>
 -info <ant|antpol>  will print out the RF switch hookup for an ant or antpol.
 -info all will print out all hookup info.
 -d will discover all rf switches.
Will print OK\n if successful. Otherwise an error will be reported.

```

Example: rfswitch 1fx (selects just 1fx)

Example: rfswitch 1fx,1fy (selects both pol switches)

Example: rfswitch -info all 

**atten**

```
Minicircuits attenuator control.

atten <comma sep list of db> <comma sep list of ant pols>
  attenuation, in dB 0.0 to 31.75
    -1 will print out the part number and serial number then exit.
   or
atten -discover
  discover all attenuators on the USB bus
Will print OK\n if successful. Otherwise an error will be reported.
**REMEMBER to run as root!!**

```

Example: atten 20.5 1fx (for just the one pol)

Example: atten 20.5,15.5 1fx,1fy (for both pols)




  
