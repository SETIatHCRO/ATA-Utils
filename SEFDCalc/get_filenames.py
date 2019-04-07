#!/usr/bin/python

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
import collections;
import glob;


DATA_BASE_DIR = "/home/sonata/data"

def get_data_dirs():

    dirs = [x[0] for x in os.walk(DATA_BASE_DIR)]
    data_dirs = []
    for d in dirs:
            if d.find("2") > -1 and d.find("data-backup") == -1:
                data_dirs.append(d)
    return sorted(data_dirs)

def get_all_on0_filenames(data_dirs, ant_source_freq_list=None):

    matcher = "*_on_000*.pkl"
    if(ant_source_freq_list != None):
        ant = ant_source_freq_list[0]
        source = ant_source_freq_list[1]
        freq = ant_source_freq_list[2]
        if "." not in freq:
            freq += ".00"
        matcher = "*_" + source + "_on_000_ant_" + ant + "_" + freq + "_*.pkl"
        #matcher = "*_" + source + "_on_000_ant_" + ant + "_" + freq + ".00_*.pkl"

    filenames = []
    for d in data_dirs:
        filenames.extend(glob.glob(d + "/" + matcher))
        #print filenames

    return sorted(filenames)


def get_filename_parts(filename):

    parts = filename.split("_")

    #/home/sonata/data/20181009/1539097761_rf9000.00_n16_taua_off_002_ant_1d_9000.00_obsid1151.pkl
    directory = "/".join(parts[0].split('/')[:-1])
    date = parts[0].split('/')[-2]
    secs = parts[0].split('/')[-1]
    obsid = parts[-1].split(".")[0][5:]
    num_iterations = parts[2][1:]
    source = parts[3]
    onoff = parts[4]
    iteration = parts[5]
    ant = parts[7]
    freq = parts[8].split(".")[0]
    short_filename = filename.split('/')[-1]

    FilenameParts = collections.namedtuple('FilenameParts', ['secs', 'ant', 'source', 'freq', 'onoff', 'iteration', 'obsid', 'filename', 'directory', 'date', 'num_iterations', 'short_filename'])
    return FilenameParts(secs, ant, source, freq, onoff, iteration, obsid, filename, directory, date, num_iterations, short_filename)

def create_filename(filename_parts):

    fp = filename_parts
    #filename  = fp.directory + "/" + fp.secs + "_rf" + fp.freq + ".00_n" + fp.num_iterations + "_" 
    filename  = fp.directory + "/" + "*" + "_rf" + fp.freq + ".00_n" + fp.num_iterations + "_" 
    filename += fp.source + "_" + fp.onoff + "_" + fp.iteration + "_ant_" + fp.ant + "_"
    filename += fp.freq + ".00_obsid" + fp.obsid + ".pkl"
    files = sorted(glob.glob(filename))
    if(len(files) == 0):
        print >> sys.stderr, "Glob returned None: " + filename
        return (None, False)

    for f in files:
        new_filename_parts = get_filename_parts(f)
        #print f
        if(int(new_filename_parts.secs) >= int(fp.secs)):
            #print new_filename_parts.secs + "," + fp.secs
            exists = os.path.isfile(f)
            return (f, exists)

    return (None, False)


def get_obs_ids(data_dirs):

    obs_ids = []

    #/home/sonata/data/20181009/1539097761_rf9000.00_n16_taua_off_002_ant_1d_9000.00_obsid1151.pkl
    for d in data_dirs:
            file_list = sorted([f for f in sorted(glob.glob(d +"/*.pkl"))])

            for f in file_list:
                parts = f.split("_")
                parts = parts[-1].split(".")
                obsid = int(parts[0][5:])
                if obsid not in obs_ids:
                    obs_ids.append(obsid)

    return obs_ids

def get_ant_list(data_dirs=None):

    if(data_dirs == None):
        data_dirs = get_data_dirs()

    ant_list = []

    #/home/sonata/data/20181009/1539097761_rf9000.00_n16_taua_off_002_ant_1d_9000.00_obsid1151.pkl
    for d in data_dirs:
            file_list = sorted([f for f in glob.glob(d +"/*.pkl")])

            for f in file_list:
                parts = f.split("_")
                ant = parts[7]
                if ant not in ant_list:
                    ant_list.append(ant)

    return sorted(ant_list)

def get_freqs(data_dirs=None):

    if(data_dirs == None):
        data_dirs = get_data_dirs()

    freq_list = []

    #/home/sonata/data/20181009/1539097761_rf9000.00_n16_taua_off_002_ant_1d_9000.00_obsid1151.pkl
    for d in data_dirs:
            file_list = sorted([f for f in glob.glob(d +"/*.pkl")])

            for f in file_list:
                parts = f.split("_")
                freq = parts[8].split(".")[0]
                if freq not in freq_list:
                    freq_list.append(freq)

    return freq_list

def get_sources(data_dirs):

    source_list = []

    #/home/sonata/data/20181009/1539097761_rf9000.00_n16_taua_off_002_ant_1d_9000.00_obsid1151.pkl
    for d in data_dirs:
            file_list = sorted([f for f in glob.glob(d +"/*.pkl")])

            for f in file_list:
                parts = f.split("_")
                source = parts[3]
                if source not in source_list:
                    source_list.append(source)

    return sorted(source_list)

def get_file_meta():

    data_dirs = get_data_dirs()

    obs_ids = get_obs_ids(data_dirs)
    ant_list = get_ant_list(data_dirs)
    freq_list = get_freqs(data_dirs)
    source_list = get_sources(data_dirs)

    #print obs_ids
    #print ant_list
    #print freq_list
    #print source_list

    MetaData = collections.namedtuple('MetaData', ['data_dirs', 'obs_ids', 'ant_list', 'freq_list', 'source_list'])
    meta_data = MetaData(data_dirs, obs_ids, ant_list, freq_list, source_list)
    return meta_data

# Get the next group of on/off files
def files_get_next_group(num, ant, source, freq):

    meta_data = get_file_meta()
    on_files = get_all_on0_filenames(meta_data.data_dirs, [ant, source, freq])

    for on_file in on_files:
        file_list = []
        pair = []
        fname_parts = get_filename_parts(on_file)
        for iteration in range(0, num):
            for on_or_off in ["on", "off"]:
                fname_parts = fname_parts._replace(onoff = on_or_off);
                fname_parts = fname_parts._replace(iteration = "%03d"%iteration);
                #print fname_parts
                file_create = create_filename(fname_parts)
                if(file_create[1] == True and file_create[0] != None):
                    pair.append(file_create[0])
                    if(on_or_off == "off"):
                        file_list.append(pair)
                        pair = []
                    #file_list.append(file_create[0])
        if(len(file_list) == 3):
            yield file_list
        else:
            print >> sys.stderr, "Only %d files for %s" % (len(file_list), on_file)

#def get_all_file_groups(num, ant, source, freq):
#
#    all_list = []
#    for file_list in files_get_next_group(num, ant, source, freq):
#            all_list.extend(file_list)
#
#    return all_list

def get_all_file_groups(num, ant, source, freq):

    all_list = []
    for file_list in files_get_next_group(num, ant, source, freq):
            #all_list.extend(file_list)
            all_list.append(file_list)

    return all_list

if __name__ == '__main__':

    #/home/sonata/data/20181017/1539773602_rf5000.00_n16_casa_on_000_ant_3e_5000.00_obsid1176.pkl
    #meta_data = get_file_meta()
    #on_files = get_all_on0_filenames(meta_data.data_dirs, ["3e", "casa", "5000"])
    #for f in on_files:
    #    print f
    #for file_list in files_get_next_group(3, "2a", "moon", "1000.00"):
    #   print " "
    #   for f in file_list:
    #        print f
    #fname_parts = get_filename_parts("/home/sonata/data/20181009/1539097761_rf9000.00_n16_taua_off_002_ant_1d_9000.00_obsid1151.pkl")
    #print fname_parts.short_filename

#    for f in get_all_file_groups(3, "2a", "casa", "1000.00"):
#        print f
#
#    print get_ant_list()
#    print get_freqs()


    meta_data = get_file_meta()
    #print len(get_all_on0_filenames(meta_data.data_dirs, ['2j', 'casa', '2000']))
    #for f in get_all_on0_filenames(meta_data.data_dirs, ['2j', 'casa', '2000']):
    #    print f
    count = 0
    for group in get_all_file_groups(3, "1f", "moon", "2000.00"):
        count += 1
        print "Group %d" % count
        for f in group:
            print f

    """
    fname_parts = get_filename_parts("/home/sonata/data/20181009/1539097761_rf9000.00_n16_taua_off_002_ant_1d_9000.00_obsid1151.pkl")
    print fname_parts
    print create_filename(fname_parts)
    fname_parts = fname_parts._replace(onoff = "on")
    print fname_parts
    print create_filename(fname_parts)
    meta_data = get_file_meta()
    print get_all_on0_filenames(meta_data.data_dirs)
    print len(get_all_on0_filenames(meta_data.data_dirs))
    #rf5000.00_n16_casa_on_000_ant_3e_5000.00_obsid1176.pkl
    print len(get_all_on0_filenames(meta_data.data_dirs, ['3e', 'casa', '5000']))
    for f in get_all_on0_filenames(meta_data.data_dirs, ['3e', 'casa', '5000']):
        print f

    print range(0, 3)

    #print meta_data.data_dirs
    #print meta_data.obs_ids
    #print meta_data.ant_list
    #print meta_data.freq_list
    #print meta_data.source_list
    """


