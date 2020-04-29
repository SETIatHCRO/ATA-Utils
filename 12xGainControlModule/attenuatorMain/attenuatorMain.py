# -*- coding: utf-8 -*-s
import RPi.GPIO as IO         # calling for header file which helps us use GPIO’s of PI
import time                    # calling for time to provide delays in program
import sys
import logging
import logging.config
from optparse import OptionParser
import argparse
logger = logging.getLogger()
IO.setwarnings(False)           # do not show any warnings
IO.setmode (IO.BCM)            # programming the GPIO by BCM pin numbers. (like PIN29 as‘GPIO5’)
IO.setup(4, IO.OUT)            #initialize selected GPIO as output
IO.setup(5,IO.OUT)
IO.setup(6,IO.OUT)
IO.setup(20,IO.OUT)
IO.setup(21,IO.OUT)
IO.setup(22,IO.OUT)
IO.setup(23,IO.OUT)
IO.setup(24,IO.OUT)

def attenuate(attenuation):
    logger.debug("#Calulate bit pattern from attenuation")
    input = attenuation
    digits = [0,0,0,0,0,0]
    steps = [16,8,4,2,1,0.5]
    for i in range(6):           #calculate the bit value of each step and store in digits
        quotient = int(attenuation/steps[i])
        digits[i] = 0 if quotient == 0 else 1
        attenuation = attenuation-steps[i]*quotient
    logger.debug("#Send data at every rising clock")
    for x in range(6):          #assign every bit to output
        IO.output(4,digits[x])            # pull up/down the data pin for every bit.
        time.sleep(0.1)            # wait for 100ms
        IO.output(5,1)            # pull CLOCK pin high
        time.sleep(0.1)
        IO.output(5,0)            # pull down the SHIFT pin
    latchEnable()
    
def latchEnable():
    logger.debug("#Outputing all the values")
    IO.output(4,0)       # clear the DATA pin
    IO.output(6,1)       # pull the SHIFT pin high to put the 8 bit data out parallel
    time.sleep(0.1)
    IO.output(6,0)       # pull down the SHIFT pin
    
def select_att(attenuator):
    logger.debug("#Selecting attenuator")
    binary = (format(attenuator-1, '05b')[::-1])
    b1 = int(binary[0])
    b2 = int(binary[1])
    b3 = int(binary[2])
    b4 = int(binary[3])
    b5 = int(binary[4])
    IO.output(20, b1)                #A1
    IO.output(21, b2)                #A2
    IO.output(22, b3)                #A3
    IO.output(23, b4)                #A4
    IO.output(24, b5)                #A5
    logger.debug("A1-A5 should be" + str(b1) + str(b2) + str(b3) + str(b4) + str(b5))

def main():
    parser = argparse.ArgumentParser(description='Select an attenuator to attenuate inputs at different levels')
    parser.add_argument('-a', '--attenuation', type=float, metavar='', required=True, help='Attenuation level from 0-31.5dB, in steps of 0.5')
    parser.add_argument('-n', '--number', type=int, metavar='', required=True, help='Input the selected attenuator number from 1 to 24, select 0 to program all attenuators')
    parser.add_argument('-v','--verbose', action='store_true', help='Prints the actions done by the program')
    args = parser.parse_args()

    #Create and configure logger
    log_format = "%(levelname)s %(asctime)s - %(message)s"
    logging.basicConfig(filename = "Attenuator.log", level = logging.DEBUG, format = log_format, filemode = 'w')
    
    if not len(sys.argv) > 1:
        logger.warning("no input provided")
        parser.print_help()
        sys.exit(1)
    
    if args.attenuation>31.5 or args.attenuation<0 or (args.attenuation/0.5)%1 != 0:
            logger.error("attenuation must be numbers between [0,31.5] that are divisible by 0.5")
            print("Illegal input for attenuation, -h for help")
            exit()
    if not (args.number>=0 and args.number<=24):
            logger.error("Attenuator# must be from 1 to 24")
            print("Invalid attenuator selection, -h for help")
            exit()
    if args.number == 0:                                #program all attenuators
        attenuate(args.attenuation)
        for i in range(24):
            select_att(i+1)
            latchEnable()
    else:
        select_att(args.number)
        attenuate(args.attenuation)
        
    if args.verbose:
        if args.number == 0:
            print("Successfully selected all attenuators")
        else:
            print("Successfuly selected attenuator#" + str(args.number))
        print("Successfully attenuated to " + str(args.attenuation) + "dB")
    exit()
    
if __name__== "__main__":
    main()
