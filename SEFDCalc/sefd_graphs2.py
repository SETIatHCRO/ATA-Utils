#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division

import sys
import numpy as np, scipy.io
import pickle
import os
import glob
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import json
import plumbum
import math
import get_filenames

#sefd_graphs.py
#code will read in data, calculate average SEFD, output one value for X and one value for Y
# and also the png filename. This CVS data is then appropriate for converting to JSON.
# The png files are scp'd to the server

# NOTE: after 1536561956 I used the auto attenuator settings

antennas =  ['2a','2b','2e','3l','1f','5c','4l','4g','2j','2d','4k','1d','2f','5h','3j','3e','1a','1b','1g','1h','2k','2m','3d','4j','5e','2c','4e','2l','2h','5g']

tunings = ["1000.00",
        "2000.00",
        "3000.00",
        "4000.00",
        "5000.00",                      
        "6000.00",
        "7000.00",
        "8000.00",
        "9000.00",
        "10000.00"]

sources = ["moon",
        "casa",
        "vira",
        "taua"]


#fig = plt.subplots()

antennas = get_filenames.get_ant_list();

#tunings = ["4000.00", "6000.00"]
#sources = ["casa"]
#antennas = ['4j']

MAX_GROUPS = 3

#antennas = ['5b', '2e', '2a', '4j', '1g']
#antennas = ['2e']
#tunings = ["3000.00", "4000.00"]
#antennas = ['2a']
#sources=['casa']

def writeToFile(filename, line):

    file = open(filename, "a")
    file.write(line)
    file.close()

def stddev(lst):

    if lst is None or len(lst) == 0:
        return 0.0

    #print "LIST: " + str(lst)

    mean = float(sum(lst)) / len(lst)
    #return math.sqrt(float(reduce(lambda x, y: x + y, map(lambda x: (x - mean) ** 2, lst))) / len(lst))
    return math.sqrt(sum((x - mean)**2 for x in lst) / len(lst))

def list_avg(l):

    if not l or len(l) == 0:
        return 0.0

    sum = 0.0;
    for f in l:
        sum += f;
    return sum / len(l)

def get_source_flux(source, tuning):

    if source == "moon":
        if tuning >= 6000.0:
            return 1.38 * 10**-23 * 270 / ((3 * 10**8) / (tuning * 10**6))**2 * ((((3 * 10**8 / (tuning * 10**6))/6.1/2)**2*3.14)/ (10**-26))
        else:
            return 1.38 * 10**-23 * 270 / ((3 * 10**8) / (tuning * 10**6))**2 * (6.67*10**-5)/ (10**-26)
        #return 1.38 * 10**-23 * 270 / ((3 * 10**8) / (float(tuning) * 10**6))**2 * (6.67*10**-5)/ (10**-26)
    elif source == "casa":
        return 250034 * tuning**-0.667
    elif source == "vira":
        return 39810.7 * tuning**-0.75
    elif source == "taua":
        return 6309.6 * tuning**-0.25

    return 0

def calc_sefd(source, tuning, ratio, goodcnt):

    sourceflux = get_source_flux(source, tuning)
    ratio = 1/(ratio / (float(goodcnt)))
    ratio = math.fabs(ratio);
    if 1/ratio < 0.01:
        ratio = 0.0

    return (ratio * sourceflux)

def make_graph(antenna, pol, tuning, source, power, ratio, goodcnt, markers, avg_sefd, graph_count):

    #print "POL: %s, len(power)=%d" % (pol, len(power))
    if(len(power) <= 2):
        return "NONE"

    """
    sourceflux = get_source_flux(source)

    ratio = 1/(ratio / (float(goodcnt)))
    ratio = math.fabs(ratio);
    if 1/ratio < 0.01:
        ratio = 0.0
    """
    #sefd = calc_sefd(source, ratio, goodcnt)

    # Finish up the plot
    plt.figure()
    plt.plot(power)
    ptitle = "Antenna: "+ antenna + pol + " Frequency: "+ tuning+ " MHz SEFD: " + str(int(avg_sefd)) + " Jy"
    plt.title(ptitle)
    for m in markers:
       if m[0] < 2:
           continue
       obs_sefd = "?"
       sefd_on_std = "0"
       sefd_off_std = "0"
       if pol == 'x' and int(m[2]) > 0:
          obs_sefd = int(m[2])
          sefd_on_std = "%.02f" % m[4]
          sefd_off_std = "%.02f" % m[5]
       if pol == 'y' and int(m[3]) > 0:
          obs_sefd = int(m[3])
          sefd_on_std = "%.02f" % m[6]
          sefd_off_std = "%.02f" % m[7]
       plt.axvline(x=m[0], color='grey', linestyle='--')
       plt.text(m[0]-1, 0, m[1] + "\nsefd " + str(obs_sefd) + "\n" + sefd_on_std + ", " + sefd_off_std, horizontalalignment='right')
       #plt.text(m[0]-1, -10, "sefd " + str(obs_sefd), horizontalalignment='right')
       #print "MARKER!"

    fname = antenna + pol + "_" + tuning + "_" + source + "_" + str(graph_count) + ".png"
    plt.savefig(fname)
    plt.close()				

    #Output CSV line
    #print("%s,%s,%s,%s,%f,%f,%s" % (source, antenna, pol, tuning, avg_sefd, ratio, fname));
    # SSH to server
    r = plumbum.machines.SshMachine("antfeeds.setiquest.info")
    fro = plumbum.local.path(fname)
    to =  r.path("www/sefd")
    plumbum.path.utils.copy(fro, to);

    os.remove(fname);

    return fname

xxx = 1

for antenna in antennas:
    for source in sources:
        for tuning in tunings:	

                
                groups = get_filenames.get_all_file_groups(3, antenna, source, tuning)

                #print "NUM GROUPS=" + str(len(groups))
                num_groups = str(len(groups))

                power0 = np.zeros(1);
                power1 = np.zeros(1);
                ratio0 = 0.0
                ratio1 = 0.0
                goodcnt0 = 0;
                goodcnt1 = 0;
                iteration = -1

                fnames_x = []
                fnames_y = []

                sefd_list_x = []
                sefd_list_y = []

                sefd_group_x = []
                sefd_group_y = []

                markers = [];
                group_count = 0
                graph_count = 0;

                #groups3 = groups[-3:]
                for g in groups:

                    group_count += 1
                    goodcnt0 = 0;
                    goodcnt1 = 0;
                    #print "Group %d, pair count=%d" % (group_count, len(g))

                    thisObsid = "-1"
                    ratio_one_obs_0 = 0.0
                    ratio_one_obs_1 = 0.0
                    avg_sefd = 0.0

                    sedf_x_on_std = 0.0;
                    sedf_x_off_std = 0.0;
                    sedf_y_on_std = 0.0;
                    sedf_y_off_std = 0.0;

                    sefd_x_text = ""
                    sefd_y_text = ""

                    for pair in g:

                        try:
                            on_filename = pair[0]
                            off_filename = pair[1]

                            #print pair

                            # Skip 1536297385 to 1536451200
                            filename_parts = get_filenames.get_filename_parts(on_filename)
                            file_timestamp = int(filename_parts.secs)
                            #if(filename_parts.obsid == "974" or filename_parts.obsid == "973") :
                            #    break
                            dataon = pickle.load(open(on_filename,'r'))
                            dataoff = pickle.load(open(off_filename,'r'))

                            iteration = int(filename_parts.iteration)


                            #Keep track of the obsId for drawing the markers
                            thisObsid = filename_parts.obsid
                            
                            #if(int(thisObsid) < 1910) :
                            #if(int(thisObsid) < 2339) :
                            #    group_count -= 1;
                            #    break;

                            #print >> sys.stderr, "%s" % filename_parts.short_filename
                        except:
                            print >> sys.stderr, "EXCEPTION"
                            break


                        if dataon['adc0_stats']['dev'] >= 2.:
                            frange = dataon['frange'][768:1700]
                            specon = np.mean(dataon['auto0'], axis=0)[768:1700]
                            specoff = np.mean(dataoff['auto0'], axis=0)[768:1700]

                            #if(iteration == 2):
                            #    markers.append([len(power0)-1, filename_parts.obsid])

                            power0 = np.append(power0, np.mean(np.array(dataon['auto0'])[:,768:1700], axis=1))
                            power0 = np.append(power0, np.mean(np.array(dataoff['auto0'])[:,768:1700], axis=1))
                            onpower = np.mean(np.array(dataon['auto0'])[:,768:1700])
                            offpower = np.mean(np.array(dataoff['auto0'])[:,768:1700])
                            ratio0 += (onpower / offpower - 1.0)
                            ratio_one_obs_0 += (onpower / offpower - 1.0)
                            sedf_x_on_std = np.std(np.mean(np.array(dataon['auto0'])[:,768:1700], axis=1))
                            sedf_x_off_std = np.std(np.mean(np.array(dataoff['auto0'])[:,768:1700], axis=1))
                            #print sedf_x_on_std,sedf_x_off_std
                            goodcnt0 += 1

                            if(len(sefd_y_text) > 0):
                                sefd_y_text += ","
                            sefd_x_text += "%0.2f" % onpower
                            sefd_x_text +="," 
                            sefd_x_text += "%0.2f" % offpower

                        if dataon['adc1_stats']['dev'] >= 2.:
                            frange = dataon['frange'][768:1700]
                            specon = np.mean(dataon['auto1'], axis=0)[768:1700]
                            specoff = np.mean(dataoff['auto1'], axis=0)[768:1700]

                            power1 = np.append(power1, np.mean(np.array(dataon['auto1'])[:,768:1700], axis=1))
                            power1 = np.append(power1, np.mean(np.array(dataoff['auto1'])[:,768:1700], axis=1))


                            onpower = np.mean(np.array(dataon['auto1'])[:,768:1700])
                            offpower = np.mean(np.array(dataoff['auto1'])[:,768:1700])
                            ratio1 += (onpower / offpower - 1.0)
                            ratio_one_obs_1 += (onpower / offpower - 1.0)
                            #print("Ratio y = %f\n" % ratio_one_obs_1)
                            sedf_y_on_std = np.std(np.mean(np.array(dataon['auto1'])[:,768:1700], axis=1))
                            sedf_y_off_std = np.std(np.mean(np.array(dataoff['auto1'])[:,768:1700], axis=1))
                            goodcnt1 += 1

                            if(len(sefd_y_text) > 0):
                                sefd_y_text += ","
                            sefd_y_text += "%0.2f" % onpower
                            sefd_y_text +="," 
                            sefd_y_text += "%0.2f" % offpower

                    """
                    if(int(iteration)==2):
                        sefdx = calc_sefd(source, ratio0, goodcnt0)
                        sefdy = calc_sefd(source, ratio1, goodcnt1)
                        print("SEFDX=%f, SERDY=%f" % (sefdx, sefdy))
                        power0 = np.zeros(1);
                        power1 = np.zeros(1);
                        ratio0 = 0.0
                        ratio1 = 0.0
                        goodcnt0 = 0;
                        goodcnt1 = 0;
                    """
        
                    print "+%s,%s,%s,x,%s,%s" % (thisObsid, antenna, str(tuning), source, sefd_x_text.replace(",,", ","))
                    print "+%s,%s,%s,y,%s,%s" % (thisObsid, antenna, str(tuning), source, sefd_y_text.replace(",,", ","))
                    sefd_x = 0
                    sefd_y = 0
                    if ratio_one_obs_0 > 0.01:
                      sefd_x = calc_sefd(source, float(tuning), ratio_one_obs_0, 3)
                      sefd_list_x.append(sefd_x)
                      #if graph_count == 1:
                        #print "Added %s" % str(sefd_x)
                      sefd_group_x.append(sefd_x)
                    if ratio_one_obs_1 > 0.01:
                      sefd_y = calc_sefd(source, float(tuning), ratio_one_obs_1, 3)
                      sefd_list_y.append(sefd_y)
                      sefd_group_y.append(sefd_y)
                    #print "len=%d, thisObsId=%d, sefd_x=%f, sefd_y=%f, goodcnt0=%d, goodcnt1=%d" % (len(power0)-1, int(thisObsid), sefd_x, sefd_y, goodcnt0, goodcnt1)
                    markers.append([len(power0)-1, thisObsid, sefd_x, sefd_y, sedf_x_on_std, sedf_x_off_std, sedf_y_on_std, sedf_y_off_std ])

                    #if(group_count == len(groups) and int(iteration) == 2):
                    if(group_count == MAX_GROUPS and int(iteration) == 2):
                        graph_count += 1
                        ##print sefd_group_x
                        #print list_avg(sefd_group_x)
                        #print("AVGs=%f,%f\n" % (list_avg(sefd_group_x), list_avg(sefd_group_y)))
                        #if graph_count == 2:
                        #    print sefd_group_x
                        #fname = make_graph(antenna, 'x', tuning, source, power0, ratio0, goodcnt0, markers, list_avg(sefd_group_x), graph_count)
                        #fnames_x.append(fname)
                        #fname = make_graph(antenna, 'y', tuning, source, power1, ratio1, goodcnt1, markers, list_avg(sefd_group_y), graph_count)
                        #fnames_y.append(fname)

                        group_count = 0
                        sefd_group_x = []
                        sefd_group_y = []

                        markers = [];
                        power0 = np.zeros(1);
                        power1 = np.zeros(1);
                        ratio0 = 0.0
                        ratio1 = 0.0
                        goodcnt0 = 0;
                        goodcnt1 = 0;
                        #if xxx == 5:
                        #    exit(0)
                        xxx += 1

                s = antenna + "," + "x" + "," + str(tuning) + "," + source + "," + num_groups + "," + str(list_avg(sefd_list_x)) 
                s += "," + str(np.std(sefd_list_x))
                #s += "," +  sefd_x_text
                #print str(sefd_list_x)
                for f in fnames_x:
                    s += "," + f
                print s
                s = antenna + "," + "y" + "," + str(tuning) + "," + source + "," + num_groups + "," + str(list_avg(sefd_list_y))
                s += "," + str(np.std(sefd_list_y))
                #s += "," +  sefd_y_text
                #print str(sefd_list_y)
                for f in fnames_y:
                    s += "," + f
                print s
                sefd_list_x = []
                sefd_list_y = []
                fnames_x = []
                fnames_y = []
