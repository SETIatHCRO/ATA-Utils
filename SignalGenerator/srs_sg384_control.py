#!/usr/bin/python

"""
srs_sg384_control.py
This program will query the SRS SG384 Signal Generator for the 
output frequency and amplitude.
"""

import telnetlib
from optparse import OptionParser
import sys

_host = "10.10.1.197"
_port = 5025

defaultF = 1800
defaultA = 16


def main():
    parser = OptionParser(usage= 'Usage %prog options',
        description='Display or change the values of SRS SG384 Signal Generator')

    parser.add_option('-p', '--print', dest='do_print', action="store_true", default=False,
            help ="Query and print current values")
    parser.add_option('-f','--freq', dest='freq', type=float, default=None,
            help ='Set clock value in MHz')
    parser.add_option('-a','--amp', dest='amp', type=float, default=None,
            help ='Set amplitude')

    (options,args) = parser.parse_args()

    

    if len(sys.argv) <= 1:
        print("no options provided")
        parser.print_help()
        sys.exit(1)

    do_p = options.do_print;
    freq = options.freq
    amp = options.amp
    if (do_p and (freq or amp)):
        print('if -p option is provided, -a and -f option should not be given')
        sys.exit(1)

    if (do_p):
        settings = get_clock_settings()
        print("{}:{} {} MHz  amp {}".format(_host,_port,settings['freq']/1e6,settings['ampr']))
    else:
        if (freq):
            set_freq(freq)
        if (amp):
            set_amp(amp)
        print("done")

def set_freq(freq):
    telnet = telnetlib.Telnet()
    telnet.open(_host, _port)

    telnet.write("FREQ {} MHz\n".format(freq))

def set_amp(amp):
    telnet = telnetlib.Telnet()
    telnet.open(_host, _port)

    telnet.write("AMPR {} Dbm\n".format(amp))

def get_clock_settings():


    telnet = telnetlib.Telnet()
    telnet.open(_host, _port)

    telnet.write("FREQ?\n")
    freq = telnet.read_until("\n", 5)
    telnet.write("AMPR?\n")
    ampr = telnet.read_until("\n", 5)

    answer = { "type" : "clock", "freq" : float(freq), "ampr" : float(ampr) }

    return answer

def set_clock_freq(freq_mhz):

    print ('To set the clock freq, "telnet %s %d" then "FREQ %f MHz"' % (_host, _port, float(freq_mhz)))

def set_ampr(ampr_db):

    print ('To set rhe amplitude of the RF output, "telnet %s %d" then "AMPR %f"' % (_host, _port, float(ampr_db)))


if __name__== "__main__":
    main()

