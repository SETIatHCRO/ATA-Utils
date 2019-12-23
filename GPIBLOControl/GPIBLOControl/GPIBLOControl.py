#!/usr/bin/env python

import gpibcontrol
from optparse import OptionParser
import sys

def main():
    usage = """Usage %prog [options] command [commandopt]
    command selection:
        setfreq  freq - set the frequency [Hz]
        errors - list all errors
        init - resets the device do default settings and turn it on
        on - turns the power on
        off - turns the power off
        getfreq - returns the current frequency
        getoutputstate - returns True/False based on output state (On/Off)"""
    parser = OptionParser(usage=usage)
    parser.add_option("-a", "--gpibaddres", action="store", type="int", dest="address", default=30,
                      help="GPIB address od the device, default=%default", metavar="ADDR")
    parser.add_option("-s", "--host", action="store", type="string", dest="host", default='lo2.hcro.org',
                      help="hostname of the controller default=%default", metavar="HOST")
    parser.add_option("-w", "--wait", action="store", type="int", dest="wait", default=True,
                      help="wait for *OPC? to finish, default=%default", metavar="BOOL")
    parser.add_option("-v", "--verbose", action="store_true", dest="v", default=True,
                      help="print more output, default=%default")
    parser.add_option("-q", "--quiet",action="store_false", dest="v",
                      help="print less output")
    
    (options, args) = parser.parse_args()
    
    if len(args) < 1:
        print "Not enough arguments!"
        parser.print_help()
        sys.exit(1)
        
    validopts = ['setfreq','errors','init','on','off','getfreq','getoutputstate']
    
    if any(args[0] in s for s in validopts):
        if args[0] == 'setfreq' and len(args) < 2:
            print "setfreq requires second argument"
            parser.print_help()
            sys.exit(1)
    else:
        print "unrecognized command"
        parser.print_help()
        sys.exit(1)
    
    commandmodule = gpibcontrol.control()
    
    if options.v:
        print "connecting to " + options.host + " at bus " + str(options.address)
        
    commandmodule.open(options.host,options.address)
    
    #set frequency
    if args[0] == 'setfreq':
        freq = float(args[1]);
        if freq < 1e9 or freq > 20e9:
            print 'HP 83731B supports freq from 1 to 20 GHz'
            sys.exit(1)
        if options.v:
            print "setting frequency to " + str(freq/1e9) + " GHz"
        commandmodule.set_frequency(freq,options.wait)
        if options.v:
            setF = commandmodule.get_frequency()
            print "current frequency is " + str(setF/1e9) + " GHz"

    if args[0] == 'errors':
        lastError = 1
        while lastError:
            lastError,errorMsg=commandmodule.get_error()
            print "Error " + str(lastError) + ": " + errorMsg

    if args[0] == 'init':
        if options.v:
            print "initializing device"
        commandmodule.reset_device()
        commandmodule.set_defaults()
        commandmodule.output_on(options.wait)
        if options.v:
            setF = commandmodule.get_frequency()
            print "current frequency is " + str(setF/1e9) + " GHz"
            
    if args[0] == 'on':
        if options.v:
            print "turning output on"
        commandmodule.output_on(options.wait)
    
    if args[0] == 'off':
        if options.v:
            print "turning output off"
        commandmodule.output_off(options.wait)
    
    if args[0] == 'getfreq':
        setF = commandmodule.get_frequency()
        print "current frequency is " + str(setF) + " Hz"
        
    if args[0] == 'getoutputstate':
        print commandmodule.is_transmitting()
        
    if options.v:
        isT = commandmodule.is_transmitting()
        if isT:
            print "Device is transmitting"
            print "Power: " + commandmodule.send_query("POW?") 
        else:
            print "Device is NOT transmitting"
            
    commandmodule.close()
       
    sys.exit(0)
    
if __name__ == "__main__":
    main()

