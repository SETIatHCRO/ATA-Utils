#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
data Processing for pax boxes

@author: jkulpa
"""

import numpy
import os
import pdb
import matplotlib.pyplot as plt
from optparse import OptionParser
import sys
from mysql.connector import Error  
import ATA-Utils-priv.ATASQL as atasql

satval = 0.88
polyOrd = 5 #up to 5
polyTable = 5 # Must be 5
discardDiff = 0.3 #what [dB] values on front of the table should we discard (if diff is <=)

#attenuation = [0,3,6,9,12,15,18,21,24,27,30,33,36,39,42,45,48,51,54,57,60]

keyXCW = 'x1'
keyXNoise = 'x2'
keyYCW = 'y1'
keyYNoise = 'y2'

def genFileNamesTxt(pb_name, directory):
    filenames = dict()
    name = os.path.join(directory,pb_name + 'x-a.txt')
    filenames[keyXCW] = name
    name = os.path.join(directory,pb_name + 'x-b.txt')
    filenames[keyXNoise] = name
    name = os.path.join(directory,pb_name + 'y-a.txt')
    filenames[keyYCW] = name
    name = os.path.join(directory,pb_name + 'y-b.txt')
    filenames[keyYNoise] = name
    return filenames

def genFileNamesBin(pb_name, directory):
    filenames = dict()
    name = os.path.join(directory,pb_name + 'x-a.bin')
    filenames[keyXCW] = name
    name = os.path.join(directory,pb_name + 'x-b.bin')
    filenames[keyXNoise] = name
    name = os.path.join(directory,pb_name + 'y-a.bin')
    filenames[keyYCW] = name
    name = os.path.join(directory,pb_name + 'y-b.bin')
    filenames[keyYNoise] = name
    return filenames

def saturateData(string):
    try:
        x = float(string);
    except (ValueError, TypeError):
        x = satval
    return x

def checkData(data):
    #we are assuming that the data between -25 and -3 dBm is linear
    
    P1_LIM = 0.1 #[db/db], the line curve
    P0_LIM = 1 #[db], how much difference between lines
    
    upperLim = -3
    lowerLim= -20
    
    isokx = 1
    isoky = 1

    #doing X pol
    tval1 = (data[keyXCW][1,:] >= lowerLim) * (data[keyXCW][1,:] <= upperLim)
    OX_CW = data[keyXCW][1,tval1]
    OY_CW = 20*numpy.log10(data[keyXCW][0,tval1]);
    
    tval2 = (data[keyXNoise][1,:] >= lowerLim) * (data[keyXNoise][1,:] <= upperLim)
    OX_N = data[keyXNoise][1,tval2]
    OY_N = 20*numpy.log10(data[keyXNoise][0,tval2]);
    
    p1x = numpy.polyfit(OX_CW,OY_CW,1)
    p2x = numpy.polyfit(OX_N,OY_N,1)
    
    if(numpy.abs( p1x[0] - p2x[0] ) > P1_LIM):
        isokx=0
        print("WARN: the CW and NOISE pol X data are significantly different! (P1)")
    if(numpy.abs( p1x[1] - p2x[1] ) > P0_LIM):
        isokx=0
        print("WARN: the CW and NOISE pol X data are significantly different! (P0)")
    
    #doing Y pol
    tval1 = (data[keyYCW][1,:] >= lowerLim) * (data[keyYCW][1,:] <= upperLim)
    OX_CW = data[keyYCW][1,tval1]
    OY_CW = 20*numpy.log10(data[keyYCW][0,tval1]);
    
    tval2 = (data[keyYNoise][1,:] >= lowerLim) * (data[keyYNoise][1,:] <= upperLim)
    OX_N = data[keyYNoise][1,tval2]
    OY_N = 20*numpy.log10(data[keyYNoise][0,tval2]);
    
    p1y = numpy.polyfit(OX_CW,OY_CW,1)
    p2y = numpy.polyfit(OX_N,OY_N,1)
    
    if(numpy.abs( p1y[0] - p2y[0] ) > P1_LIM):
        isoky=0
        print("WARN: the CW and NOISE pol Y data are significantly different! (P1)")
    if(numpy.abs( p1y[1] - p2y[1] ) > P0_LIM):
        isoky=0
        print("WARN: the CW and NOISE pol Y data are significantly different! (P0)")
    
    #pdb.set_trace()
    return [isokx,isoky];

def plotData(data):
    plt.plot(10*numpy.log10(data[keyXNoise][0,:]),data[keyXNoise ][1,:],10*numpy.log10(data[keyXCW][0,:]),data[keyXCW][1,:])
    plt.title(pb_name + ' x')
    plt.show()
    
    plt.clf()
    plt.plot(10*numpy.log10(data[keyYNoise][0,:]),data[keyYNoise][1,:],10*numpy.log10(data[keyYCW][0,:]),data[keyYCW][1,:])
    plt.title(pb_name + ' y')
    plt.show()

def getDataTxt(filename):
    data = numpy.loadtxt(filename,converters = {0: saturateData})
    assert(len(data) == 42), "bad number of inputs in data, 42 expected"
    retdat = numpy.empty((2,21))
    retdat[0,:] = data[0:21]
    retdat[1,:] = data[21:43]
    return retdat


def makePolynomial(ar,doPolyTest=0):
    valid = (ar[0,:] < satval)
    
    #HERE we are assuming that the data is as in the ALEX's files, i.e. bigger power on top
    id_to_clear = numpy.argmax(numpy.abs(numpy.diff(10*numpy.log10(ar[0,valid]))) > discardDiff)
    if id_to_clear:
        #we need to remove some more data, i.e. modify the valid vector
        ftrue = numpy.argmax(valid)
        #pdb.set_trace()
        valid[ftrue:ftrue+id_to_clear] = False
    
    maxval = 10*numpy.log10(numpy.max(ar[0,valid]));
    minval = 10*numpy.log10(numpy.min(ar[0,valid]));
    rest=[minval,maxval]
    pp = numpy.polyfit(20*numpy.log10(ar[0,valid]),ar[1,valid],polyOrd)
    
    if doPolyTest:
        plt.clf()
        pv = numpy.poly1d(pp);
        xx = pv(20*numpy.log10(ar[0,valid]))
        plt.plot(20*numpy.log10(ar[0,valid]),xx,20*numpy.log10(ar[0,valid]),ar[1,valid])
        plt.show()


    assert polyTable == 5, "Database polynomial size mismatch. polyTable must be 5"
    assert polyTable >= polyOrd, "polyOrd must be not greater than 5"
    if polyTable > polyOrd:
        pptmp = pp;
        pp=numpy.zeros(polyTable+1)
        pp[(polyTable-polyOrd):] = pptmp

    return pp,rest        

def genDatabaseQuery(pb,data,polys,rest,isok):
    
    #check if db exist?
    try:
        dict1 = {'pbstr' : pb, 'pol': 'x', 'type': 'cw', 'ok': isok[0]}
        for a in numpy.arange(21):
            dict1['m' + str(a)] = data[keyXCW][1,a];
            dict1['d' + str(a)] = data[keyXCW][0,a];
        for a in numpy.arange(6):
            dict1['p' + str(a)] = polys[keyXCW][-a-1];
        dict1['vallow'] = rest[keyXCW][0]
        dict1['valhigh'] = rest[keyXCW][1]
            
        dict2 = {'pbstr' : pb, 'pol': 'x', 'type': 'n', 'ok': isok[0]}
        for a in numpy.arange(21):
            dict2['m' + str(a)] = data[keyXNoise][1,a];
            dict2['d' + str(a)] = data[keyXNoise][0,a];
        for a in numpy.arange(6):
            dict2['p' + str(a)] = polys[keyXNoise][-a-1];
        dict2['vallow'] = rest[keyXNoise][0]
        dict2['valhigh'] = rest[keyXNoise][1]
        
        dict3 = {'pbstr' : pb, 'pol': 'y', 'type': 'cw', 'ok': isok[1]}
        for a in numpy.arange(21):
            dict3['m' + str(a)] = data[keyXCW][1,a];
            dict3['d' + str(a)] = data[keyXCW][0,a];
        for a in numpy.arange(6):
            dict3['p' + str(a)] = polys[keyXCW][-a-1];
        dict3['vallow'] = rest[keyXCW][0]
        dict3['valhigh'] = rest[keyXCW][1]
            
        dict4 = {'pbstr' : pb, 'pol': 'y', 'type': 'n', 'ok': isok[1]}
        for a in numpy.arange(21):
            dict4['m' + str(a)] = data[keyYNoise][1,a];
            dict4['d' + str(a)] = data[keyYNoise][0,a];
        for a in numpy.arange(6):
            dict4['p' + str(a)] = polys[keyYNoise][-a-1];
        dict4['vallow'] = rest[keyYNoise][0]
        dict4['valhigh'] = rest[keyYNoise][1]
        
        pdb.set_trace()
        
        db = atasql.connectDefaultRW();
        cx = db.cursor()
        
        query = ("INSERT INTO pbmeas ( " 
                "pax_box_sn, pol, type, iscoherent,"
                " meas0, meas1, meas2, meas3, meas4, meas5, meas6, meas7, "
                " meas8, meas9, meas10, meas11, meas12, meas13, meas14, "
                " meas15, meas16, meas17, meas18, meas19, meas20, "
                " det0, det1, det2, det3, det4, det5, det6, det7, "
                " det8, det9, det10, det11, det12, det13, det14, "
                " det15, det16, det17, det18, det19, det20, "
                " lowdet, highdet, p0, p1, p2, p3, p4, p5"
                ") VALUES %(pbstr)s, %(pol)s, %(type)s, %(ok)d, "
                " %(m0)f, %(m1)f, %(m2)f, %(m3)f, %(m4)f, %(m5)f, %(m6)f, %(m7)f,"
                " %(m8)f, %(m9)f, %(m10)f, %(m11)f, %(m12)f, %(m13)f, %(m14)f, "
                " %(m15)f, %(m16)f, %(m17)f, %(m18)f, %(m19)f, %(m20)f, "
                " %(d0)f, %(d1)f, %(d2)f, %(d3)f, %(d4)f, %(d5)f, %(d6)f, %(d7)f,"
                " %(d8)f, %(d9)f, %(d10)f, %(d11)f, %(d12)f, %(d13)f, %(d14)f, "
                " %(d15)f, %(d16)f, %(d17)f, %(d18)f, %(d19)f, %(d20)f, "
                " %(vallow)f, %(valhigh)f, "
                " %(p0)f, %(p1)f, %(p2)f, %(p3)f, %(p4)f, %(p5)f, "
                )
        cx.execute(query,dict1)
        db.commit()
        cx.execute(query,dict2)
        db.commit()
        cx.execute(query,dict3)
        db.commit()
        cx.execute(query,dict4)
        db.commit()
        cx.close()
        db.close()
    except Error as e:
        print("Error reading data from MySQL table", e)

    

if __name__ == '__main__':
    
    usage = "Usage %prog [options] PB_NUMBER"
    parser = OptionParser(usage=usage)    
    parser.add_option("-f", "--file",
            action="store_true", dest="file", default=True,
            help="fetch data from file")
    parser.add_option("-s", "--sql",
            action="store_false", dest="file",
            help="Fetch data from SQL and update polynomial NOT IMPLEMENTED")
    parser.add_option("-t", "--text",
            action="store_true", dest="text", default=True,
            help="process text file [default]. File names PB_NUMBER{xy}-{ab}.txt. Only with -f")
    parser.add_option("-b", "--binary",
            action="store_false", dest="text",
            help="Only with -f. NOT IMPLEMENTED")
    parser.add_option("-d","--dir", action="store", type="str",
            dest="dir", default="meas",
            help="directory containing data")
    parser.add_option("-v", "--verbose",
            action="store_true", dest="verbose", default=False,
            help="more information and enables plots")

    (options, args) = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        sys.exit(1)

    if not options.text:
        print("binary not supported yet")
        sys.exit(1)
        
    if not options.file:
        print("fetching from sql not supported yet")
        sys.exit(1)


    pb_name = args[0];
    
    if options.file:
        if options.text:
            fnames = genFileNamesTxt(pb_name,options.dir)
            keys = fnames.keys()
    
            data = dict()
            for k in keys:
                data[k] = getDataTxt(fnames[k])
        else:
            fnames = genFileNamesBin(pb_name,options.dir)
            keys = fnames.keys()
    
            data = dict()
            #for k in keys:
            #   data[k] = getDataBin(fnames[k])

    keys = data.keys()
    
    if options.verbose:
        plotData(data)

    isok = checkData(data)

    polys = dict()
    rest = dict()
    for k in keys:
        polys[k],rest[k] = makePolynomial(data[k],options.verbose)
        
    genDatabaseQuery(pb_name,data,polys,rest,isok)
