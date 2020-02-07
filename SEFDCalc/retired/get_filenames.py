#!/usr/bin/python

"""
Name: get_filenames.py
Author: Jon Richards, August 28, 2019

Contains helpers to retrieve the SNAP on/off pkl data files.
Returns the file groups based on source, frequency, antenna, etc.
The function get_all_file_groups() is the one you will want to
use. See the main test at the end of this file for an example.

"""

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
files_meta_data = None

def get_data_dirs():

    """ Get a sorted list of all the data directories. """

    dirs = [x[0] for x in os.walk(DATA_BASE_DIR)]
    data_dirs = []
    for d in dirs:
            if d.find("2") > -1 and d.find("data-backup") == -1:
                parts = d.split("/")
                if int(parts[4]) >= 20190814:
                    data_dirs.append(d)
    return sorted(data_dirs)

def get_all_on0_filenames(data_dirs, ant_source_freq_list=None):

    """ Retrieve the filenames of all the on0 pkl data files. """

    # Filename example:
    # 1539097761_rf9000.00_n16_taua_off_002_ant_1d_9000.00_obsid1151.pkl
    matcher = "*_on_000*.pkl"
    if(ant_source_freq_list != None):
        ant = ant_source_freq_list[0]
        source = ant_source_freq_list[1]
        freq = ant_source_freq_list[2]
        obsid = ant_source_freq_list[3]
        if "." not in freq:
            freq += ".00"
        if obsid is not -1:
            matcher = "*_" + source + "_on_000_ant_" + ant + "_" + freq + "_obsid" + str(obsid) + ".pkl"
        else:
            matcher = "*_" + source + "_on_000_ant_" + ant + "_" + freq + "_*.pkl"
        #matcher = "*_" + source + "_on_000_ant_" + ant + "_" + freq + ".00_*.pkl"

    filenames = []
    for d in data_dirs:
        filenames.extend(glob.glob(d + "/" + matcher))
        #print filenames

    return sorted(filenames)


def get_filename_parts(filename):

    """Given a pkl filename return a named tuple of all the parts."""

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

    """From a list of filename parts, assemble and return the full path filename."""

    fp = filename_parts
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


def get_obs_ids(data_dirs=None):

    """ Go through all the file directories and return the list of antennas."""

    if data_dirs is None:
        data_dirs = get_data_dirs()

    obs_ids = []

    # Filename example:
    #/home/sonata/data/20181009/1539097761_rf9000.00_n16_taua_off_002_ant_1d_9000.00_obsid1151.pkl
    for d in data_dirs:
            file_list = sorted([f for f in sorted(glob.glob(d +"/*.pkl"))])

            for f in file_list:
                #print(f)
                parts = f.split("_")
                if int(parts[2][1:]) != 16:
                    continue
                #print(f, len(parts), parts[2][1:])
                parts = parts[-1].split(".")
                obsid = int(parts[0][5:])
                if obsid not in obs_ids:
                    obs_ids.append(obsid)

    return obs_ids

def get_ant_list(data_dirs=None):

    """ Go through all the file directories and return the list of antennas."""

    if data_dirs is None:
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

    """ Go through all the file directories and return the list of frequencies."""

    if data_dirs is None:
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

    """ Go through all the file directories and return the list of sources."""

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

    """ Get the meta data for all data files in the data directory.
    Returns a named tuple containing the list of directories, obs ids,
    antennas, freqencies, and sources.
    """


    global files_meta_data
    if files_meta_data is not  None:
        return files_meta_data

    data_dirs = get_data_dirs()

    obs_ids = get_obs_ids(data_dirs)
    ant_list = get_ant_list(data_dirs)
    freq_list = get_freqs(data_dirs)
    source_list = get_sources(data_dirs)

    MetaData = collections.namedtuple('MetaData', ['data_dirs', 'obs_ids', 'ant_list', 'freq_list', 'source_list'])
    files_meta_data = MetaData(data_dirs, obs_ids, ant_list, freq_list, source_list)
    return files_meta_data

def files_get_next_group(num, ant, source, freq, obsid):

    """
    Generator that returns data file names that match the
    desired antena, source, frequency and optionally an
    obsid.
    The files are returned in a list of lists. Each list
    is grouped by obsid. 
    """

    global files_meta_data
    if files_meta_data is None:
        files_meta_data = get_file_meta()

    on_files = get_all_on0_filenames(files_meta_data.data_dirs, [ant, source, freq, obsid])

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
        if(len(file_list) == num):
            yield file_list
        #else:
        #    print >> sys.stderr, "Only %d files for %s" % (len(file_list), on_file)

def get_all_file_groups(number_in_group, ant, source, freq, obsid, lastn):

    """
    Retrieve data file names that match the desired antenna, source, 
    frequency and optionally an obsid.

    number_in_group is the number of pkl files to be returned in each group
    obsid can be -1, whcih will return ALL groups that match.
    lastn returns only the name "n" matches. -1 returns all.

    The files are returned in a list of lists. Each list
    is grouped by obsid. 
    """

    all_list = []
    for file_list in files_get_next_group(number_in_group, ant, source, freq, int(obsid)):
            all_list.append(file_list)

    if lastn > 0:
        return all_list[-lastn:]
    return all_list

if __name__ == '__main__':

    count = 0
    for group in get_all_file_groups(3, "1c", "moon", "1400.00", -1, -1):
        count += 1
        print "Group %d" % count
        for f in group:
            print f
