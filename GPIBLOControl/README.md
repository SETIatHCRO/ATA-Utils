# GPIB-LO-Control
Python program to control the local oscilator using the GPIB to Ethernet adapter
Tested with HP 83731B

the repository consist of library (control.py) and a shell program (GPIBLOControl.py)

The library allows to send and receive any arbitrary SCPI command, but also 
have some predefined functions. The default power level is +13 dBm and it is not
possible to control it in the program (it is defined in the library). The program
is installed in the snap-controlling server

The shell program has predefined command options

## Usage

 Usage: Usage GPIBLOControl.py [options] command [commandopt]

    command selection:

        setfreq  freq - set the frequency [Hz]

        errors - list all errors

        init - resets the device do default settings

        on - turns the power on

        off - turns the power off

        getfreq - returns the current frequency [Hz]

        getoutputstate - returns True/False based on output state (On/Off)


 Options:

  -h, --help            show this help message and exit

  -a ADDR, --gpibaddres=ADDR
                        GPIB address od the device, default=30

  -s HOST, --host=HOST  hostname of the controller default=lo2.hcro.org

  -w BOOL, --wait=BOOL  wait for *OPC? to finish, default=True

  -v, --verbose         print more output, default=True

  -q, --quiet           print less output

## Examples:

setting LO to default settings and turning it on:

    GPIBLOControl.py -q init

setting LO frequency to 2 GHz (note that HP 83731B works in frequency range 1-20 GHz)

    GPIBLOControl.py -q setfreq 2e9

checking all errors in the query and state of the device

    GPIBLOControl.py -v errors
