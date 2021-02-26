# -*- coding: utf-8 -*-s
import RPi.GPIO as IO         # calling for header file which helps us use GPIO’s of PI
import time                    # calling for time to provide delays in program
import sys,os
import logging
import logging.config
import argparse
import pickle
from filelock import FileLock

LOCK_FILE = "/var/lock/attenuator.lock"
LOCK = FileLock(LOCK_FILE)

HISTORY_FILE = "./history.p"
if not os.path.exists(HISTORY_FILE):
    pickle.dump({}, open(HISTORY_FILE, "wb"))

logger = logging.getLogger()
IO.setwarnings(False)           # do not show any warnings
IO.setmode (IO.BCM)            # programming the GPIO by BCM pin numbers. (like PIN29 as‘GPIO5’)
IO.setup(4,IO.OUT)          #Data Pin
IO.setup(5,IO.OUT)          #CLK
IO.setup(6,IO.OUT)          #LE
IO.setup(20,IO.OUT)         #1-Bit register to select Attemplifier LE
IO.setup(21,IO.OUT)         #2-Bit register to select Attemplifier LE
IO.setup(22,IO.OUT)         #1-Bit register to select Attemplifier LE
IO.setup(23,IO.OUT)         #1-Bit register to select Attemplifier LE

def attenuate(attenuation):
    logger.debug("#Calulate bit pattern from attenuation")
    digits = [0,0,0,0,0,0]
    steps = [16,8,4,2,1,0.5]
    for i in range(6):           #calculate the bit value of each step and store in digits
        quotient = int(attenuation/steps[i])
        digits[i] = 0 if quotient == 0 else 1
        attenuation = attenuation-steps[i]*quotient
    logger.debug("#Send data at every rising clock")
    for x in range(5, -1, -1):          #Modified to reverse bit order when sending range(6)
        IO.output(4,digits[x])            # pull up/down the data pin for every bit.
        time.sleep(0.1)            # wait for 10ms
        IO.output(5,1)            # pull CLOCK pin high
        time.sleep(0.0005)
        IO.output(5,0)            # pull CLOCK pin low
        time.sleep(0.0005)

def latchEnable():
    logger.debug("#Outputing all the values")
    IO.output(4,0)       # clear the DATA pin
    time.sleep(0.0005)
    IO.output(6,0)       # pull the SHIFT pin high to put the 8 bit data out parallel
    time.sleep(0.0005)
    IO.output(6,1)       # pull down the SHIFT pin
    time.sleep(0.0005)
    IO.output(6,0)       # pull down the SHIFT pin



def select_att(attenuator):
    logger.debug("#Selecting attenuator")
    binary = (format(attenuator-1, '04b')[::-1])
    b1 = int(binary[0])
    b2 = int(binary[1])
    b3 = int(binary[2])
    b4 = int(binary[3])
    IO.output(20, b1)                #A1
    IO.output(21, b2)                #A2
    IO.output(22, b3)                #A3
    IO.output(23, b4)                #A4
    logger.debug("A1-A4 should be" + str(b1) + str(b2) + str(b3) + str(b4) )

def main():
    #Create and configure logger
    log_format = "%(levelname)s %(asctime)s - %(message)s"
    logging.basicConfig(filename = "Attenuator.log", level = logging.DEBUG, format = log_format, filemode = 'w')
    #Parsing arguments
    parser = argparse.ArgumentParser(description='Select an attenuator to attenuate inputs at different levels')
    parser.add_argument('-a', '--attenuation', type=float, metavar='', nargs='+', help='Attenuation level from 0-31.5dB, in steps of 0.5; can select multiple values(in sequence matched by the selected attenuator#) by typing multiple inputs separated by single spaces')
    parser.add_argument('-n', '--number', type=int, metavar='', nargs='+', help='Input the selected attenuator number from 1 to 16, select 0 to program all attenuators. Can select multiple by typing selected numbers separated by single spaces')
    parser.add_argument('-v','--verbose', action='store_true', help='Prints the actions done by the program')
    parser.add_argument('-g', '--getvalue', action='store_true', help='Returns the last programmed value for all attenuators. Else specify attenuator number(s) with -n command.')
    parser.add_argument('-i', '--initialize', action='store_true', help='Initializes all the attenuators to last programmed values')
    #validate arguments
    args = parser.parse_args()
    if args.attenuation and args.number:
        alist = args.attenuation
        nlist = args.number
        if len(alist) != len(nlist):
            logger.error("number of attenuators does not match number of attenuation inputs")
            print("Number of attenuators selected must match number of attenuation level selected")
            exit(-1)
    #initialize
    with LOCK:
        hist_dict = pickle.load(open(HISTORY_FILE, "rb"))
        if args.initialize:
            for n, a in hist_dict.items():
                n = int(n)
                a = float(a)
                if n != 0:
                    select_att(n)
                    attenuate(a)
                    latchEnable()
            if args.verbose:
                print("Successfully initialized all attenuators")
            exit()

    #getvalue
    with LOCK:
        dict = pickle.load(open(HISTORY_FILE, "rb"))
        if args.getvalue:
            if not args.number:
                number_list = dict.keys()
            else:
                number_list = args.number
            for eachNumb in number_list:
                if not eachNumb in dict:
                    print(eachNumb, -1)
                else:
                    print(eachNumb, dict[eachNumb])
            exit()

    #attenuate
    with LOCK:
        #case for programming all attenuators
        if len(nlist) == 1 and nlist[0]== 0 and alist[0]<31.5 and alist[0]>0 and (alist[0]/0.5)%1 == 0:
            attenuate(args.attenuation[0])
            for i in range(16):
                select_att(i+1)
                latchEnable()
                hist_dict = pickle.load(open(HISTORY_FILE, "rb"))
                hist_dict[i] = args.attenuation[0]
                pickle.dump(hist_dict, open(HISTORY_FILE, "wb"))
            exit()
        #validate all arguments
        for i in range(len(alist)):
            if alist[i]>31.5 or alist[i]<0 or (alist[i]/0.5)%1 != 0:
                logger.error("attenuation must be numbers between [0,31.5] that are divisible by 0.5")
                print("Illegal input for attenuation, -h for help")
                exit()
            if not (nlist[i]>=0 and nlist[i]<=16):
                logger.error("Attenuator# must be from 1 to 16")
                print("Invalid attenuator selection, -h for help")
                exit()
            #attenuate
            select_att(nlist[i])
            attenuate(alist[i])
            latchEnable()
            #saving h h to pickle file
            hist_dict = pickle.load(open(HISTORY_FILE, "rb"))
            hist_dict[nlist[i]] = alist[i]
            pickle.dump(hist_dict, open(HISTORY_FILE, "wb"))

        #verbose mode
        if args.verbose:
            if args.number == 0:
                print("Successfully selected all attenuators")
            else:
                print("Successfuly selected attenuator#" + str(nlist))
            print("Successfully attenuated to " + str(alist) + "dB")

        exit()

if __name__== "__main__":
    main()
