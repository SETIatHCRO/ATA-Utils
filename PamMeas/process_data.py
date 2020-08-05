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
import ATASQL as atasql

duplicate_entry_errno = 1062
satval = 1.0
polyOrd = 5 #up to 5
polyTable = 5 # Must be 5
discardDiff = 0.3 #what [dB] values on front of the table should we discard (if diff is <=)

#attenuation = [0,3,6,9,12,15,18,21,24,27,30,33,36,39,42,45,48,51,54,57,60]

allowed_db = ["none","google","ata"]
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
    OY_CW = 10*numpy.log10(data[keyXCW][0,tval1]);
    
    tval2 = (data[keyXNoise][1,:] >= lowerLim) * (data[keyXNoise][1,:] <= upperLim)
    OX_N = data[keyXNoise][1,tval2]
    OY_N = 10*numpy.log10(data[keyXNoise][0,tval2]);
    
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
    OY_CW = 10*numpy.log10(data[keyYCW][0,tval1]);
    
    tval2 = (data[keyYNoise][1,:] >= lowerLim) * (data[keyYNoise][1,:] <= upperLim)
    OX_N = data[keyYNoise][1,tval2]
    OY_N = 10*numpy.log10(data[keyYNoise][0,tval2]);
    
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
    plt.title(pb_name + ' x [raw data]')
    plt.legend(['noise', 'single_tone'])
    plt.xlabel('detector value [dB]')
    plt.ylabel('measured power [dBm]')
    plt.show()
    
    plt.clf()
    plt.plot(10*numpy.log10(data[keyYNoise][0,:]),data[keyYNoise][1,:],10*numpy.log10(data[keyYCW][0,:]),data[keyYCW][1,:])
    plt.title(pb_name + ' y [raw data]')
    plt.legend(['noise', 'single_tone'])
    plt.xlabel('detector value [dB]')
    plt.ylabel('measured power [dBm]')
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
    
    #we are also eliminating the lower power points, if that seems to saturate
    id_to_clear_new = numpy.argmin(numpy.abs(numpy.diff(10*numpy.log10(ar[0,valid]))) > discardDiff)
    if id_to_clear_new:
        ftrue = numpy.argmax(valid)
        valid[ftrue+id_to_clear_new+1:] = False

    maxval = 10*numpy.log10(numpy.max(ar[0,valid]));
    minval = 10*numpy.log10(numpy.min(ar[0,valid]));
    rest=[minval,maxval]
    weights = numpy.ones(numpy.sum(valid))
    weights[10*numpy.log10(ar[0,valid])< -25] = 0.5
    weights[0] = 0.25
    weights[-1] = 0.25
    pp = numpy.polyfit(10*numpy.log10(ar[0,valid]),ar[1,valid],polyOrd, w=weights)

    if doPolyTest:
        plt.clf()
        pv = numpy.poly1d(pp);
        polybase = numpy.linspace(minval,maxval,100)
        xx = pv(polybase)
        #plt.plot(10*numpy.log10(ar[0,valid]),xx,10*numpy.log10(ar[0,valid]),ar[1,valid])
        plt.plot(polybase,xx,10*numpy.log10(ar[0,valid]),ar[1,valid])
        plt.legend(['polynomial', 'raw data'])
        plt.xlabel('detector value [dB]')
        plt.ylabel('measured power [dBm]')
        plt.show()


    assert polyTable == 5, "Database polynomial size mismatch. polyTable must be 5"
    assert polyTable >= polyOrd, "polyOrd must be not greater than 5"
    if polyTable > polyOrd:
        pptmp = pp;
        pp=numpy.zeros(polyTable+1)
        pp[(polyTable-polyOrd):] = pptmp

    return pp,rest        

def genDatabaseQuery(pb,data,polys,rest,isok,database_name, update_flag):
    
    #check if db exist?
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
        dict3['m' + str(a)] = data[keyYCW][1,a];
        dict3['d' + str(a)] = data[keyYCW][0,a];
    for a in numpy.arange(6):
        dict3['p' + str(a)] = polys[keyYCW][-a-1];
    dict3['vallow'] = rest[keyYCW][0]
    dict3['valhigh'] = rest[keyYCW][1]
        
    dict4 = {'pbstr' : pb, 'pol': 'y', 'type': 'n', 'ok': isok[1]}
    for a in numpy.arange(21):
        dict4['m' + str(a)] = data[keyYNoise][1,a];
        dict4['d' + str(a)] = data[keyYNoise][0,a];
    for a in numpy.arange(6):
        dict4['p' + str(a)] = polys[keyYNoise][-a-1];
    dict4['vallow'] = rest[keyYNoise][0]
    dict4['valhigh'] = rest[keyYNoise][1]
    
    if database_name != "none":
        if database_name == "google":
            db = atasql.connectDefaultRW();
            cx = db.cursor()
        elif database_name == "ata":
            db = atasql.connectATARW();
            cx = db.cursor()
        else:
            raise RuntimeError("unknown db")
    
        if update_flag:
            query = ("UPDATE pbmeas set iscoherent=%(ok)s,"
                " meas0=%(m0)s, meas1=%(m1)s, meas2=%(m2)s, meas3=%(m3)s,"
                " meas4=%(m4)s, meas5=%(m5)s, meas6=%(m6)s, meas7=%(m7)s,"
                " meas8=%(m8)s, meas9=%(m9)s, meas10=%(m10)s, meas11=%(m11)s,"
                " meas12=%(m12)s, meas13=%(m13)s, meas14=%(m14)s, meas15=%(m15)s,"
                " meas16=%(m16)s, meas17=%(m17)s, meas18=%(m18)s, meas19=%(m19)s,"
                " meas20=%(m20)s, "
                " det0=%(d0)s, det1=%(d1)s, det2=%(d2)s, det3=%(d3)s, det4=%(d4)s, "
                " det5=%(d5)s, det6=%(d6)s, det7=%(d7)s, det8=%(d8)s, det9=%(d9)s, "
                " det10=%(d10)s, det11=%(d11)s, det12=%(d12)s, det13=%(d13)s, det14=%(d14)s, "
                " det15=%(d15)s, det16=%(d16)s, det17=%(d17)s, det18=%(d18)s, det19=%(d19)s, "
                " det20=%(d20)s, " 
                " lowdet=%(vallow)s, highdet= %(valhigh)s, "
                " p0=%(p0)s, p1=%(p1)s, p2=%(p2)s, p3=%(p3)s, p4=%(p4)s, p5=%(p5)s "
                " where pax_box_sn=%(pbstr)s and pol=%(pol)s and type=%(type)s ;")
        else:
            query = ("INSERT INTO pbmeas ( " 
                "pax_box_sn, pol, type, iscoherent,"
                " meas0, meas1, meas2, meas3, meas4, meas5, meas6, meas7, "
                " meas8, meas9, meas10, meas11, meas12, meas13, meas14, "
                " meas15, meas16, meas17, meas18, meas19, meas20, "
                " det0, det1, det2, det3, det4, det5, det6, det7, "
                " det8, det9, det10, det11, det12, det13, det14, "
                " det15, det16, det17, det18, det19, det20, "
                " lowdet, highdet, p0, p1, p2, p3, p4, p5"
                ") VALUES ( %(pbstr)s, %(pol)s, %(type)s, %(ok)s, "
                " %(m0)s, %(m1)s, %(m2)s, %(m3)s, %(m4)s, %(m5)s, %(m6)s, %(m7)s,"
                " %(m8)s, %(m9)s, %(m10)s, %(m11)s, %(m12)s, %(m13)s, %(m14)s, "
                " %(m15)s, %(m16)s, %(m17)s, %(m18)s, %(m19)s, %(m20)s, "
                " %(d0)s, %(d1)s, %(d2)s, %(d3)s, %(d4)s, %(d5)s, %(d6)s, %(d7)s,"
                " %(d8)s, %(d9)s, %(d10)s, %(d11)s, %(d12)s, %(d13)s, %(d14)s, "
                " %(d15)s, %(d16)s, %(d17)s, %(d18)s, %(d19)s, %(d20)s, "
                " %(vallow)s, %(valhigh)s, "
                " %(p0)s, %(p1)s, %(p2)s, %(p3)s, %(p4)s, %(p5)s ); "
                )

        try:
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
            print(cx._executed)
            print(query)
            if e.errno == duplicate_entry_errno:
                print("try running with -u flag")
    else:
        #none db, so only printing
        outstr="{0[pbstr]}{0[pol]}({0[type]}): {0[p0]} {0[p1]} {0[p2]} {0[p3]} {0[p4]} {0[p5]} max/min: {0[valhigh]}/{0[vallow]}"
        #import pdb
        #pdb.set_trace()
        print(outstr.format(dict1))
        print(outstr.format(dict2))
        print(outstr.format(dict3))
        print(outstr.format(dict4))

if __name__ == '__main__':
    
    usage = ("Usage %prog [options] PB_NUMBER \n"
             "\n"
             "The software requires that files PB_NUMBER{xy}-{ab}.txt\n"
             "are present in measurement directory. '-a.txt' is for CW, whereas\n"
             "'-b.txt' for noise measurements")
    parser = OptionParser(usage=usage)    
    parser.add_option("-u", "--update",
            action="store_true", dest="update",
            help="update database if row exist. By default without this flag the program will crash if data exist in DB")
    parser.add_option("-d","--dir", action="store", type="str",
            dest="dir", default="meas",
            help="directory containing data")
    parser.add_option("-v", "--verbose",
            action="store_true", dest="verbose", default=False,
            help="more information and enables plots")
    parser.add_option("--db",
            action="store", dest="db_string", default="ata",
            help="specify which db to populate [" + "|".join(allowed_db) + "]. Selecting none prints values to stdout")

    (options, args) = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        sys.exit(1)

    if options.db_string not in allowed_db:
        print("unrecognized DB. use [" + "|".join(allowed_db) + "]")
        sys.exit(1)

    pb_name = args[0];
    
    fnames = genFileNamesTxt(pb_name,options.dir)
    keys = fnames.keys()
    
    data = dict()
    for k in keys:
        data[k] = getDataTxt(fnames[k])

    keys = data.keys()
    
    if options.verbose:
        plotData(data)

    isok = checkData(data)

    polys = dict()
    rest = dict()
    for k in keys:
        if options.verbose:
            print(k)
        polys[k],rest[k] = makePolynomial(data[k],options.verbose)
        
    genDatabaseQuery(pb_name,data,polys,rest,isok,options.db_string,options.update)
