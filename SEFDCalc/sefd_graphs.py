#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division

import os
# This way of importing matplotlib.pyplot allows running without an active X Server
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import json
import math
from collections import OrderedDict
import datetime
import random
import plumbum
import numpy
import OnOffCalc.misc

"""
sefd_graphs.py
Author: Jon Richards, August 29, 2019

NOTES: The website and server are at antfeeds.setiquest.info.
       After successfully running this script, view
         http://antfeeds.setiquest.info with the new graphs

Feb 2020: JKulpa
    The file was significantly changed - now it operates as a lib file

This will:

  3) Create SEFD power graphs as PNGs
  4) The png files can be scp'd to the server.
  5) Create the HTML pages for viewing the graphs and scp's the HTML file 
     to the server.
  6) Creates a JSONP file of all the SEFD averages and PNG files for
     displaying on the website.

The operator of this script can select specify many options:

  6) "show_graphs" will display each graph in an X window popup as
     they are created. This is useful for looking at a few graphs to
     make sure one or two are working, but not useful if you have a
     lot to process.
 """

# NOTE: after 1536561956 I used the auto attenuator settings - JR

SEFD_SERVER = "antfeeds.setiquest.info"
SEFD_SERVER_DIR = "www/sefd"
HTML_FILENAME = "latest_sefds_"
HTML_DIR = "www"

"""START OF VALUES TO CHANGE"""

show_graphs = False

"""END OF VALUES TO CHANGE"""

def makeJson(sefddict):
    jsonp = OrderedDict()
    antennas = sefddict.keys()
    jsonp["ants"] = antennas
    #TODO:this part is hardcoded. This is because previous scripts made distinction on
    #the source. in new code, we don't care that much what the source was and all sources
    #goes into one processing scheme. But that would need changing java on the website
    jsonp["sources"] = ["moon"]
    source = "moon"

    jsonp[source] = OrderedDict()
    for ant in sefddict:
        jsonp[source][ant] = OrderedDict()
        jsonp[source][ant]['x'] = []
        jsonp[source][ant]['y'] = []
        for freq in sefddict[ant]:
            cdict = sefddict[ant][freq]
            #getting one number 
            avg_sefd = numpy.average(cdict['sefd_x'], weights=numpy.divide(1,cdict['sefd_x_var']))
            fname = os.path.basename(cdict['powerplots']['x'])
            jsonp[source][ant]['x'].append([['{0:.2f}'.format(freq)],[str(int(avg_sefd))],[fname]])
            avg_sefd = numpy.average(cdict['sefd_y'], weights=numpy.divide(1,cdict['sefd_y_var']))
            fname = os.path.basename(cdict['powerplots']['y'])
            jsonp[source][ant]['y'].append([['{0:.2f}'.format(freq)],[str(int(avg_sefd))],[fname]])

        #sorting by frequency
        jsonp[source][ant]['x'].sort(key=lambda sd: float(sd[0][0]))
        jsonp[source][ant]['y'].sort(key=lambda sd: float(sd[0][0]))

    file = open("sefd.jsonp", "w")
    j = "sefd(" + json.dumps(jsonp) + ")"
    file.write(j)
    file.close()

    r = plumbum.machines.SshMachine(SEFD_SERVER)
    fro = plumbum.local.path("sefd.jsonp")
    to =  r.path(SEFD_SERVER_DIR)
    plumbum.path.utils.copy(fro, to);
    os.remove("sefd.jsonp");

def makeHtml( sefddict ):
    filename = "%s%s.html" % (HTML_FILENAME, 'moon')

    file = open(filename, "w")

    file.write('<html>\n<head>\n\t<link rel="stylesheet" type="text/css" href="css_sefd.css">\n')
    file.write('<title>Latest On/Off SEFDs</title>\n')
    file.write('</head>\n<body>\n')

    #filling the navigation tab
    file.write('<div class="navbar">\n')
    antkeys = sefddict.keys()
    antkeys.sort()
    for ant in antkeys:

        file.write('<div class="dropdown">')
        s = '<button class="dropbtn">{0:s}'.format(ant)
        file.write(s)
        file.write('\t<i class="fa fa-caret-down"></i>\n</button>\n')

        #Now adding the frequencies
        file.write('<div class="dropdown-content">\n')
        fkeys = sefddict[ant].keys()
        fkeys.sort()
        for freq in fkeys:
            link_name = '{0:s}_{1:d}'.format(ant, int(float(freq)))
            s =  '<a href="#{0:s}">{1:d}</a>\n'.format(link_name, int(float(freq)))
            file.write(s)
        file.write('</div>\n</div>\n')
    file.write('</div>\n')

    file.write("<h1>Latest On/Off SEFDs</h1>\n")
    t = datetime.datetime.today().strftime('%Y-%m-%d&nbsp;%H:%M:%S')
    file.write("Calculated: {} UTC\n".format(t))

    rand = random.randint(1,50000)

    for ant in antkeys:
        file.write('<p id={0:s}>\n'.format(ant))
        s = "<h2>{0:s}</h2>\n".format(ant)
        file.write(s)

        fkeys = sefddict[ant].keys()
        fkeys.sort()
        for freq in fkeys:
            cdict = sefddict[ant][freq]
            link_name = '{0:s}_{1:d}'.format(ant, int(float(freq)))
            s = '<p id={0:s}>'.format(link_name)
            file.write(s)

            s = "<h3>power vs time ({0:.2f} MHz)</h3>\n".format(freq)
            file.write(s)
            #printing power plots
            iname1 = os.path.basename(cdict['powerplots']['x'])
            s = "<img src=\"http://%s/sefd/%s?x=%d\" width=\"400\">\n" % (SEFD_SERVER, iname1, rand)
            file.write(s)
            iname2 = os.path.basename(cdict['powerplots']['y'])
            s = "<img src=\"http://%s/sefd/%s?x=%d\" width=\"400\">\n" % (SEFD_SERVER, iname2, rand)
            file.write(s)
            file.write("<BR>\n")
    
            #checking if there are any spectrograms
            if cdict['specplots']:
                s = "<h3>spectrograms (waterfalls)</h3>\n"
                file.write(s)
                cplotlist = cdict['specplots']['x']
                i = 0
                for img in cplotlist:
                    imgbase = os.path.basename(img)
                    s = "<img src=\"http://%s/sefd/%s?x=%d\" width=\"400\">\n" % (SEFD_SERVER, imgbase, rand)
                    file.write(s)
                    i += 1
                    if i == 2:
                        file.write("<BR>\n")
                        i = 0
                file.write("<BR>\n")

                cplotlist = cdict['specplots']['y']
                i = 0
                for img in cplotlist:
                    imgbase = os.path.basename(img)
                    s = "<img src=\"http://%s/sefd/%s?x=%d\" width=\"400\">\n" % (SEFD_SERVER, imgbase, rand)
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

    r = plumbum.machines.SshMachine(SEFD_SERVER)
    fro = plumbum.local.path(filename)
    to =  r.path(HTML_DIR)
    plumbum.path.utils.copy(fro, to);
    os.remove(filename);

    url = "http://%s/%s" % (SEFD_SERVER, filename)
    return url

def genImages(onData,offData,sefddict,comparedict=None,upload=True,genspectrograms=True,directory='.'):
    directoryfull = os.path.abspath(directory)
    
    #'x' and 'y'
    powerplots = {}
    spectrogramplots = {}
    
    cant = sefddict['ant']
    cfreq = sefddict['freq']
    csrc = sefddict['source']

    if comparedict:
        powerplots['x'] = makePowerGraph([sefddict['power_x'],comparedict['power_x']],cant,'x',cfreq,csrc,directoryfull,upload)
        powerplots['y'] = makePowerGraph([sefddict['power_y'],comparedict['power_y']],cant,'y',cfreq,csrc,directoryfull,upload)
    else:
        powerplots['x'] = makePowerGraph(sefddict['power_x'],cant,'x',cfreq,csrc,directoryfull,upload)
        powerplots['y'] = makePowerGraph(sefddict['power_y'],cant,'y',cfreq,csrc,directoryfull,upload)

    if genspectrograms:
        spectrogramplots = makeSpectrograms(onData,offData,sefddict,comparedict,upload,directoryfull,flatspectra=True)

    return powerplots,spectrogramplots

def flatSpectraVector(onData,offData,drange):
    """
    returns dictionary with 'x' and 'y' being numpy vector(array) to correct passband spectra
    """

    method = 'globmin'

    xdata = offData[0].data_array[:,0,drange,0].real.copy()
    ydata = offData[0].data_array[:,0,drange,1].real.copy()

    for ii in range(len(offData)-1):
        xdata = numpy.concatenate((xdata,offData[ii+1].data_array[:,0,drange,0].real.copy()),axis=0)
        ydata = numpy.concatenate((ydata,offData[ii+1].data_array[:,0,drange,1].real.copy()),axis=0)


    if method == 'poly':

        polyorder = 32

        #xaxes for polynomial. probably best conditioning if -1:1
        xxt = numpy.linspace(-1,1,xdata.shape[1])
        xyt = numpy.linspace(-1,1,ydata.shape[1])

        #y data for polynomial. 
        yxt_tmp = numpy.mean(xdata,axis=0)
        xmaxval = max(yxt_tmp)
        yxt = yxt_tmp/xmaxval
        yyt_tmp = numpy.mean(ydata,axis=0)
        ymaxval = max(yyt_tmp)
        yyt = yyt_tmp/ymaxval
    
        #weights
        #wx = 1.0/(numpy.std(xdata,axis=0)/xmaxval)
        #wy = 1.0/(numpy.std(xdata,axis=0)/xmaxval)

        polyx = numpy.poly1d(numpy.polyfit(xxt,yxt,polyorder))
        polyy = numpy.poly1d(numpy.polyfit(xyt,yyt,polyorder))
        #polyx = numpy.poly1d(numpy.polyfit(xxt,yxt,polyorder,w=wx))
        #polyy = numpy.poly1d(numpy.polyfit(xyt,yyt,polyorder,w=wy))

        pvalsx = polyx(xxt)*xmaxval
        pvalsy = polyy(xyt)*ymaxval

    elif method == 'mean':
        pvalsx = numpy.mean(xdata,axis=0)
        pvalsy = numpy.mean(ydata,axis=0)

    elif method == 'min':
        pvalsx = numpy.min(xdata,axis=0)
        pvalsy = numpy.min(ydata,axis=0)

    elif method == 'globmin':

        xminoff = numpy.min(xdata,axis=0)
        yminoff = numpy.min(ydata,axis=0)

        xdata = onData[0].data_array[:,0,drange,0].real.copy()
        ydata = onData[0].data_array[:,0,drange,1].real.copy()

        for ii in range(len(offData)-1):
            xdata = numpy.concatenate((xdata,onData[ii+1].data_array[:,0,drange,0].real.copy()),axis=0)
            ydata = numpy.concatenate((ydata,onData[ii+1].data_array[:,0,drange,1].real.copy()),axis=0)

        xminon = numpy.min(xdata,axis=0)
        yminon = numpy.min(ydata,axis=0)

        pvalsx = numpy.min((xminoff,xminon),axis=0)
        pvalsy = numpy.min((yminoff,yminon),axis=0)

    else:
        raise NotImplementedError("unknown flat band method")

    return {'x':pvalsx,'y':pvalsy}

def makeSpectrograms(onData,offData,sefddict,comparedict,upload,directoryfull,flatspectra=False, dbscale=True):
    nReps = len(onData)
    assert (nReps == len(offData)), "data list mismatch"
    drange = OnOffCalc.misc.getDatarange(onData[0].data_array[:,0,:,0].shape[1])
    retdict = {'x':[],'y':[]}

    if flatspectra:
        specvector = flatSpectraVector(onData,offData,drange)
    else:
        specvector = None

    for ii in range(nReps):
        if comparedict:
            retx,rety = makeXYSpectrograms(onData[ii],drange,"ON",ii,sefddict,useflags=False,upload=upload,directory=directoryfull,spectracorrectionvector=specvector, dbscale=dbscale)
            retdict['x'].append(retx)
            retdict['y'].append(rety)

        retx,rety = makeXYSpectrograms(onData[ii],drange,"ON",ii,sefddict,useflags=True,upload=upload,directory=directoryfull,spectracorrectionvector=specvector, dbscale=dbscale)
        retdict['x'].append(retx)
        retdict['y'].append(rety)

        if comparedict:
            retx,rety = makeXYSpectrograms(offData[ii],drange,"OFF",ii,sefddict,useflags=False,upload=upload,directory=directoryfull,spectracorrectionvector=specvector, dbscale=dbscale)
            retdict['x'].append(retx)
            retdict['y'].append(rety)

        retx,rety = makeXYSpectrograms(offData[ii],drange,"OFF",ii,sefddict,useflags=True,upload=upload,directory=directoryfull,spectracorrectionvector=specvector, dbscale=dbscale)
        retdict['x'].append(retx)
        retdict['y'].append(rety)

    return retdict

def makeXYSpectrograms(uvdata,drange,onoffstr,seqnum,sefddict,useflags,upload,directory,spectracorrectionvector, dbscale=True):

    #copying is not time efficient, but we will be modifying values here and we don't want to affect the underlaying arrays
    xdata = uvdata.data_array[:,0,drange,0].real.copy()
    ydata = uvdata.data_array[:,0,drange,1].real.copy()

    freqrange = uvdata.freq_array[0,drange]/1e6 #in MHz
    ant = sefddict['ant']
    freq = sefddict['freq']
    src = sefddict['source']

    dataExtent=[freqrange[0],freqrange[-1],1,xdata.shape[0]];

    #correcting for the pass-band ripples
    #TODO: check if division is better, so expected value is 1
    #the multiplicative approach seems better, but values near 0 will be an issue
    if spectracorrectionvector:
        if dbscale:
            xdata = numpy.divide(xdata,spectracorrectionvector['x'])
            ydata = numpy.divide(ydata,spectracorrectionvector['y'])
        else:
            xdata = xdata - spectracorrectionvector['x']
            ydata = ydata - spectracorrectionvector['y']

        scstr = 'spectral_correction'
    else:
        scstr = ''

    if dbscale:
        scalestr = 'dB'
    else:
        scalestr = 'lin'
    
    #after correcting (or not) the ripples, dealing with the flags
    if useflags:
        method = sefddict['method']
        xflags = uvdata.flag_array[:,0,drange,0]
        yflags = uvdata.flag_array[:,0,drange,1]
        xdata[xflags] = 0
        ydata[yflags] = 0
    else:
        method = 'simple'

    freqstr = '{0:.2f}'.format(freq)
    indexstr = '{0:d}'.format(seqnum)
    fnamex = "spectr_" + ant + "x_" + freqstr + "_" + onoffstr + indexstr + "_" + method + "_" + src + ".png"
    xtitle = "Ant " + ant + 'x freq ' + freqstr + " "  + onoffstr + indexstr + " (" + method + scstr + " " + scalestr + ") " + src
    fnamey = "spectr_" + ant + "y_" + freqstr + "_" + onoffstr + indexstr + "_" + method + "_" + src + ".png"
    ytitle = "Ant " + ant + 'y freq ' + freqstr + " "  + onoffstr + indexstr + " (" + method + scstr + " " + scalestr + ") " + src
    
    xnamefull = os.path.join(directory,fnamex)
    ynamefull = os.path.join(directory,fnamey)

    plt.figure()
    if dbscale:
        plt.imshow(10*numpy.log10(xdata),aspect='auto', interpolation='none', extent=dataExtent,vmin=0)
    else:
        plt.imshow(xdata,aspect='auto', interpolation='none', extent=dataExtent,vmin=0)
    #plt.imshow(xdata,aspect='auto', interpolation='none', extent=dataExtent)
    plt.title(xtitle)
    plt.xlabel('freq [MHz]')
    plt.ylabel('snapshot no.')
    plt.colorbar()

    plt.savefig(xnamefull)

    if show_graphs:
        plt.show()
    plt.close()

    plt.figure()
    if dbscale:
        plt.imshow(10*numpy.log10(ydata),aspect='auto', interpolation='none', extent=dataExtent,vmin=0)
    else:
        plt.imshow(ydata,aspect='auto', interpolation='none', extent=dataExtent,vmin=0)
    #plt.imshow(ydata,aspect='auto', interpolation='none', extent=dataExtent)
    plt.title(ytitle)
    plt.xlabel('freq [MHz]')
    plt.ylabel('snapshot no.')
    plt.colorbar()

    plt.savefig(ynamefull)

    if show_graphs:
        plt.show()
    plt.close()

    if upload:
        r = plumbum.machines.SshMachine(SEFD_SERVER)
        fro = plumbum.local.path(xnamefull)
        to =  r.path(SEFD_SERVER_DIR)
        plumbum.path.utils.copy(fro, to);
        fro = plumbum.local.path(ynamefull)
        plumbum.path.utils.copy(fro, to);

    return xnamefull,ynamefull

def makePowerGraph(power,ant,pol,freq,src,directoryfull,upload):
    plt.figure()
    plt.plot(numpy.transpose(power))
    ptitle = "Antenna: "+ ant + pol + " Frequency: "+ '{0:.2f}'.format(freq) + " MHz source: " + src
    plt.title(ptitle)
    fname = 'power_' + ant + pol + "_" + '{0:.2f}'.format(freq) + "_" + src + ".png"
    fullname = os.path.join(directoryfull,fname)
    plt.savefig(fullname)

    if show_graphs:
        plt.show()
    plt.close()

    if upload:
        r = plumbum.machines.SshMachine(SEFD_SERVER)
        fro = plumbum.local.path(fullname)
        to =  r.path(SEFD_SERVER_DIR)
        plumbum.path.utils.copy(fro, to);

    return fullname

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

    return fname

