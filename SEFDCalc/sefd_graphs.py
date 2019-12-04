#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division

import sys
import numpy as np, scipy.io
import pickle
import os
import glob
# This way of importing matplotlib.pyplot allows running without an active X Server
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import json
import plumbum
import math
import get_filenames
from collections import OrderedDict
import datetime
import random

sys.path.append('/home/sonata/ATA-Utils/JSKATAScirpts')
import OnOff

"""
sefd_graphs.py
Author: Jon Richards, August 29, 2019

NOTES: The website and server are at antfeeds.setiquest.info.
       After successfully running this script, view
         http://antfeeds.setiquest.info with the new graphs

This will:

  1) Read data from groups of SNAP on/off pkl files
  2) Calculate the average SEFD for each pol 
  3) Create SEFD power graphs as PNGs
  4) The png files can be scp'd to the server.
  5) Create the HTML pages for viewing the graphs and scp's the HTML file 
     to the server.
  6) Creates a JSONP file of all the SEFD averages and PNG files for
     displaying on the website.

The operator of this script can select specify many options:

  1) The user can select which sources, ants, tunings, etc in the 
     "START OF VALUES TO CHANGE" section.
  2) To process just one observation id (one group of 3) specify
     a value for obs_id. The default is -1, which means do not use
     obs_id as a selection criteria.
  3) To process just the last "n" on/off observations, change the
     value of "last_num_groups". -1 means ALL on/off observations, which
     may be too much to display. "1" will display just the most recent
     on/off observation. A good value is "9" because 9 on/off observations
     fit well in a graph.
  4) "ssh_pngs_to_server" to True will:
       a) scp the resulting png files to the server for viewing
       b) The sefd.jsonp wile will be scp'd to the server
  5) "create_html" to True will create an HTML for viewing the graphs
     all on one page, one page for each source. If "ssh_pngs_to_server"
     is True the HTML files will be scp'd to the server.
  6) "show_graphs" will display each graph in an X window popup as
     they are created. This is useful for looking at a few graphs to
     make sure one or two are working, but not useful if you have a
     lot to process.
  7) "compare_RFI" will calculate SEFD with and without RFI mitigation techniques. Additional images will be stored
 """

# NOTE: after 1536561956 I used the auto attenuator settings - JR

SEFD_SERVER = "antfeeds.setiquest.info"
SEFD_SERVER_DIR = "www/sefd"
HTML_FILENAME = "latest_sefds_"
HTML_DIR = "www"

"""START OF VALUES TO CHANGE"""

#sources = ["moon","casa"]
sources = ["moon"]
antennas =  ['1c', '2h','2a','2b','2e','2j','4j']
#antennas =  ['1c']
#antennas = ['1a','1b','1c','1d','1f','1g','2a','2b','2c','2d','2e','2f','2h','2j','2k','2l','3e','3j','3l','4g','4j','4k','4l','5b','5e','5g','5h']
tunings = ["1400.00",
        "2500.00",
        "3500.00",
        "4500.00",
        "5500.00",                      
        "6500.00",
        "7500.00",
        "8500.00",
        "9500.00"]

obs_id = -1
last_num_groups = 1 
png_suffix = "_1"
ssh_pngs_to_server = True
show_graphs = True
create_html = True
compare_RFI = True

"""END OF VALUES TO CHANGE"""

def make_html(source, antennas, pngs):

    filename = "%s%s.html" % (HTML_FILENAME, source)
    file = open(filename, "w")

    file.write('<html>\n<head>\n\t<link rel="stylesheet" type="text/css" href="css_sefd.css">\n')
    file.write('<title>%s Latest On/Off SEFDs</title>\n' % source)
    file.write('</head>\n<body>\n')

    #creating the navbar
    file.write('<div class="navbar">\n')
    
    #filling the navigation tab
    for ant in antennas:
        if ant not in pngs:
            continue

        file.write('<div class="dropdown">')
        s = '<button class="dropbtn">%s' % ant
        file.write(s)
        file.write('\t<i class="fa fa-caret-down"></i>\n</button>\n')

        #Now adding the frequencies
        file.write('<div class="dropdown-content">\n')
        fkeys = pngs[ant].keys()
        fkeys.sort()
        for freq in fkeys:
           link_name = '%s_%d' % (ant, int(float(freq)))
           s =  '<a href="#%s">%d</a>\n' % (link_name, int(float(freq)))
           file.write(s)
        file.write('</div>\n</div>\n')
    file.write('</div>\n')

    file.write("<h1>%s Latest On/Off SEFDs</h1>\n" % source)
    t = datetime.datetime.today().strftime('%Y-%m-%d&nbsp;%H:%M:%S')
    file.write("Calculated: %s UTC\n" % t)

    rand = random.randint(1,50000)

    for ant in antennas:
        if ant not in pngs:
            continue
        file.write('<p id=%s>\n' % ant)
        s = "<h2>%s</h2>\n" % ant
        file.write(s)

        fkeys = pngs[ant].keys()
        fkeys.sort()
        for freq in fkeys:
            id_str = '%s_%d' % (ant, int(float(freq)))
            s = '<p id=%s>' % id_str
            file.write(s)
            i = 0
            for img in pngs[ant][freq]:

                s = "<img src=\"http://%s/sefd/%s?x=%d\" width=\"400\">\n" % (SEFD_SERVER, img, rand)
                file.write(s)
                i += 1
                if i == 2:
                    file.write("<BR>\n")
                    i = 0

            file.write("<BR><BR>");
            file.write('</p>\n')
        file.write('</p>\n')

    file.write("</body>\n</HTML>\n")

    file.close()

    # SSH to server
    if ssh_pngs_to_server:
        r = plumbum.machines.SshMachine(SEFD_SERVER)
        fro = plumbum.local.path(filename)
        to =  r.path(HTML_DIR)
        plumbum.path.utils.copy(fro, to);
        os.remove(filename);

        url = "http://%s/%s" % (SEFD_SERVER, filename)
        return url

    return filename

def redo_spectrogram_data(data,plotStart,plotStop,idx_filtered):
    dataArray1 = np.array(data);
    dataArray = np.array(data);
    data_s = dataArray1[:,plotStart:plotStop];
    data_f_tmp = dataArray;
    rtozero = np.arange(0,data_f_tmp.shape[1]-1)
    rr = np.delete(rtozero,idx_filtered)
    data_f_tmp[:,rr] = 0
    data_f = data_f_tmp[:,plotStart:plotStop];
    
    return data_s,data_f
    

def make_single_spectrogram_graph(antenna, pol, tuning, source, number,ptype, plotStart, plotStop, idx_filtered, frange, dataArray):
    data_s,data_f = redo_spectrogram_data(dataArray,plotStart,plotStop,idx_filtered)

    dataExtent=[frange[plotStart],frange[plotStop],1,data_s.shape[0]];

    plt.figure()
    plt.imshow(data_s,aspect='auto', interpolation='none', extent=dataExtent)
    ptitle = "Antenna: " + antenna + pol + " Frequency: "+ tuning+ " MHz SEFD: rec " + str(number) + " " + ptype + " orig"
    plt.title(ptitle)
    
    fname1 = antenna + pol + "_" + tuning + "_" + source + "_rec" + str(number) + ptype + "orig" + png_suffix + ".png"
    plt.savefig(fname1)

    if show_graphs:
        plt.show()
    plt.close()

    # SSH to server
    if ssh_pngs_to_server:
        r = plumbum.machines.SshMachine(SEFD_SERVER)
        fro = plumbum.local.path(fname1)
        to =  r.path(SEFD_SERVER_DIR)
        plumbum.path.utils.copy(fro, to);
        os.remove(fname1);

    plt.figure()
    plt.imshow(data_f,aspect='auto', interpolation='none', extent=dataExtent)
    ptitle = "Antenna: " + antenna + pol + " Frequency: "+ tuning+ " MHz SEFD: rec " + str(number) + " " + ptype
    plt.title(ptitle)
    
    fname2 = antenna + pol + "_" + tuning + "_" + source + "_rec" + str(number) + ptype + png_suffix + ".png"
    plt.savefig(fname2)

    if show_graphs:
        plt.show()
    plt.close()

    # SSH to server
    if ssh_pngs_to_server:
        r = plumbum.machines.SshMachine(SEFD_SERVER)
        fro = plumbum.local.path(fname2)
        to =  r.path(SEFD_SERVER_DIR)
        plumbum.path.utils.copy(fro, to);
        os.remove(fname2);

    return fname1,fname2;

def make_spectrogram_graph(antenna, tuning, source, number, onArray, offArray, idx_simple, idx_filtered):
    #TODO: check if frange are the same in both!
    frange = onArray['frange']
    plotStart = idx_simple[0]
    plotStop = idx_simple[-1]

    fname1,fname2=make_single_spectrogram_graph(antenna, 'x', tuning, source, number,'ON', plotStart, plotStop, idx_filtered, frange, onArray['auto0'])
    fname3,fname4=make_single_spectrogram_graph(antenna, 'x', tuning, source, number,'OFF', plotStart, plotStop, idx_filtered, frange, offArray['auto0'])
    fname5,fname6=make_single_spectrogram_graph(antenna, 'y', tuning, source, number,'ON', plotStart, plotStop, idx_filtered, frange, onArray['auto1'])
    fname7,fname8=make_single_spectrogram_graph(antenna, 'y', tuning, source, number,'OFF', plotStart, plotStop, idx_filtered, frange, offArray['auto1'])

    return [fname1,fname2,fname3,fname4],[fname5,fname6,fname7,fname8]


def make_graph(antenna, pol, tuning, source, power, markers, avg_sefd):
    plt.figure()
    plt.plot(np.transpose(power))
    ptitle = "Antenna: "+ antenna + pol + " Frequency: "+ tuning+ " MHz SEFD: " + str(int(avg_sefd)) + " Jy"
    plt.title(ptitle)
    id_text = "id:"
    sefd_text = "sefd:"
    if len(markers) > 4:
        id_text = ""
        sefd_text = "s"
    for m in markers:
       obs_sefd = m[2]
       plt.axvline(x=m[0], color='grey', linestyle='--')
       plt.text(m[0]-1, 0, id_text + m[1] + "\n" + sefd_text + str(obs_sefd), horizontalalignment='right')

    fname = antenna + pol + "_" + tuning + "_" + source + png_suffix + ".png"
    plt.savefig(fname)

    # Display the graph
    if show_graphs:
        plt.show()
    plt.close()				

    # SSH to server
    if ssh_pngs_to_server:
        r = plumbum.machines.SshMachine(SEFD_SERVER)
        fro = plumbum.local.path(fname)
        to =  r.path(SEFD_SERVER_DIR)
        plumbum.path.utils.copy(fro, to);
        os.remove(fname);

    jsonp[source][antenna][pol].append([[tuning],[str(int(avg_sefd))],[fname]])

    return fname


"""
Go through the pkl data files and create the graphs.
"""

# The png files created are stored in a dict for creating the
# HTML file.
pngs = {};

# The list of HTML URLs are saved and printed out
# at the end for the user to reference.
html = []

jsonp = OrderedDict()
jsonp["ants"] = antennas
jsonp["sources"] = sources

for source in sources:

    jsonp[source] = OrderedDict()
    pngs ={} 

    for antenna in antennas:

        jsonp[source][antenna] = OrderedDict()
        jsonp[source][antenna]['x'] = []
        jsonp[source][antenna]['y'] = []

        pngs[antenna] = {}

        for tuning in tunings:	
            pngs[antenna][tuning] = []
            xPolSpectrogramNames=[]
            yPolSpectrogramNames=[]

            print("Processing %s, %s, %s" % (antenna, source, tuning))

            # Get groups of three on/off pkl files
            groups = get_filenames.get_all_file_groups(3, antenna, source, tuning, obs_id, last_num_groups)

            print "NUMBER GROUPS of 3 = " + str(len(groups))

            # Markers are the data used to decorate the graph with
            # extra information such as average SEFD, obsid, etc.
            markers_x = []
            markers_y = []

            # Init the power x/y data array. make the first value be
            # 0.0 so all the graphs have basically the same scale
            # when plotted.
            power_x = np.zeros(1)
            power_y = np.zeros(1)
            
            power_x_s = np.zeros(1)
            power_y_s = np.zeros(1)

            sefd_mean_x = []
            sefd_mean_y = []

            for g in groups:

                # Get the groups of 3 on/off file names
                file_on0 = g[0][0]
                file_off0 = g[0][1]
                file_on1 = g[1][0]
                file_off1 = g[1][1]
                file_on2 = g[2][0]
                file_off2 = g[2][1]

                # Get the data from the files
                on_0_dict = pickle.load( open( file_on0, "rb" )  )
                off_0_dict = pickle.load( open( file_off0, "rb" ) )
                on_1_dict = pickle.load( open( file_on1, "rb" )  )
                off_1_dict = pickle.load( open( file_off1, "rb" ) )
                on_2_dict = pickle.load( open( file_on2, "rb" )  )
                off_2_dict = pickle.load( open( file_off2, "rb" ) )

                # Calculate the SEFD
                OnOff.filterArray.setMADall()
                SEFD_X,SEFD_var_X,SEFD_Y,SEFD_var_Y,timeStamps,powerX,powerY,idx_plot,idy_plot = OnOff.calcSEFDThreeDict(on_0_dict, off_0_dict, on_1_dict, off_1_dict, on_2_dict, off_2_dict)
                if compare_RFI:
                    OnOff.filterArray.setSimple()
                    SEFD_X_s,SEFD_var_X_s,SEFD_Y_s,SEFD_var_Y_s,timeStamps_s,powerX_s,powerY_s,idx_plot_s,idy_plot_s = OnOff.calcSEFDThreeDict(on_0_dict, off_0_dict, on_1_dict, off_1_dict, on_2_dict, off_2_dict)

                    fname1,fname2 = make_spectrogram_graph(antenna, tuning, source,0, on_0_dict, off_0_dict, idx_plot_s[0], idx_plot[0])
                    for x in fname1:
                        xPolSpectrogramNames.append(x)
                    for x in fname2:
                        yPolSpectrogramNames.append(x)
                    fname1,fname2 = make_spectrogram_graph(antenna, tuning, source,1, on_1_dict, off_1_dict, idx_plot_s[1], idx_plot[1])
                    for x in fname1:
                        xPolSpectrogramNames.append(x)
                    for x in fname2:
                        yPolSpectrogramNames.append(x)
                    fname1,fname2 = make_spectrogram_graph(antenna, tuning, source,2, on_2_dict, off_2_dict, idx_plot_s[2], idx_plot[2])
                    for x in fname1:
                        xPolSpectrogramNames.append(x)
                    for x in fname2:
                        yPolSpectrogramNames.append(x)
                
                # Get the observation id for this group
                filename_parts = get_filenames.get_filename_parts(file_on0)
                obsid = filename_parts.obsid

                # Calc the mean of the SEFD values. If the mean is
                # less than 500, there is obviously a problem. So
                # set to 0. 500 was arbitrarily selected as a
                # threshold value, you may wish to change this.
                # Also added > 200000, that is way too large
                obs_sefd_mean_x = np.mean(SEFD_X)
                obs_sefd_mean_y = np.mean(SEFD_Y)
                if obs_sefd_mean_x < 500 or obs_sefd_mean_x > 200000:
                    obs_sefd_mean_x = 0
                if obs_sefd_mean_y < 500 or obs_sefd_mean_y > 200000:
                    obs_sefd_mean_y = 0

                # For graphing, append the power data
                #power_x.extend(powerX)
                #power_y.extend(powerY)
                power_x = np.hstack((power_x,powerX))
                power_y = np.hstack((power_y,powerY))
                if compare_RFI:
                    power_x_s = np.hstack((power_x_s,powerX_s))
                    power_y_s = np.hstack((power_y_s,powerY_s))

                # If the SEFD is > 0, thus no error calulating the 
                # SEFD, add it to the sefd_mean_x/y array.
                # Add the data necessary for the graphing markers.
                if obs_sefd_mean_x > 0:
                    sefd_mean_x.append(obs_sefd_mean_x)
                    markers_x.append([len(power_x), obsid, int(obs_sefd_mean_x)])
                else:
                    markers_x.append([len(power_x), obsid, 0])

                if obs_sefd_mean_y > 0:
                    sefd_mean_y.append(obs_sefd_mean_y)
                    markers_y.append([len(power_y), obsid, int(obs_sefd_mean_y)])
                else:
                    markers_y.append([len(power_y), obsid, 0])
            
            # If there are no SEFD mean values, probably due to 
            # bad data or RFI, create an array [0.0] so the
            # mean calculates to 0 for making hte graph.
            if len(sefd_mean_x) == 0:
                sefd_mean_x.append(0.0)
            if len(sefd_mean_y) == 0:
                sefd_mean_y.append(0.0)
            
            # Make the x and y pol graphs.
            #fname_x = make_graph(antenna, 'x', tuning, 
            #        source, [int(x) for x in power_x], 
            #        markers_x, int(np.mean(sefd_mean_x)))
            #fname_y = make_graph(antenna, 'y', tuning, 
            #        source, [int(x) for x in power_y], 
            #        markers_y, int(np.mean(sefd_mean_y)))
            if compare_RFI:
                fname_x = make_graph(antenna, 'x', tuning, 
                    source, [power_x,power_x_s], 
                    markers_x, int(np.mean(sefd_mean_x)))
                fname_y = make_graph(antenna, 'y', tuning, 
                    source, [power_y,power_y_s], 
                    markers_y, int(np.mean(sefd_mean_y)))

            else:
                fname_x = make_graph(antenna, 'x', tuning, 
                    source, power_x, 
                    markers_x, int(np.mean(sefd_mean_x)))
                fname_y = make_graph(antenna, 'y', tuning, 
                    source, power_y, 
                    markers_y, int(np.mean(sefd_mean_y)))

            # For making the HTML file add the filenames
            # to a dict.
            pngs[antenna][tuning].append(fname_x)
            pngs[antenna][tuning].append(fname_y)
            for x in xPolSpectrogramNames:
                pngs[antenna][tuning].append(x)
            for x in yPolSpectrogramNames:
                pngs[antenna][tuning].append(x)


    if create_html:
        url = make_html(source, antennas, pngs)
        html.append(url)

# A the end, print out the URLs for the user to view, if create_html is True
if create_html:
    for url in html:
        print("View at %s" % url)

# Push the sefd.jsonp file to the server
if ssh_pngs_to_server:

    file = open("sefd.jsonp", "w")
    j = "sefd(" + json.dumps(jsonp) + ")"
    file.write(j)
    file.close()

    r = plumbum.machines.SshMachine(SEFD_SERVER)
    fro = plumbum.local.path("sefd.jsonp")
    to =  r.path(SEFD_SERVER_DIR)
    plumbum.path.utils.copy(fro, to);
    os.remove("sefd.jsonp");

# Whew! the end!
