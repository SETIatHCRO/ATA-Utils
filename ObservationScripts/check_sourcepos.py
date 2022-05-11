from ATATools import ata_control, logger_defaults
from ATATools import ata_sources
import numpy as np
import sys
import time
import argparse
import logging
import csv
import os
from recons10_utils import get_source_names
from recons10_utils import is_observed
from recons10_utils import mark_as_observed

def main():

    freqs = sys.argv[1]
    freqs_c = sys.argv[2]

    freqs = int(freqs)
    freqs_c = int(freqs_c)

    time.sleep(30)
    
    print("Aquiring source list")
    
    csv_name = 'sources_observed.csv'

    source_names = get_source_names(csv_name)

    lista=[]
    listb=[]
    src_lft=[]
    ra_lst=[]
    dec_lst=[]

    #loop through source list
    for i, source in enumerate(source_names):
        
        #make sure source is not observed
        if is_observed(csv_name, source, freqs) == 0 and\
                is_observed(csv_name, source, freqs_c) == 0:
            src_lft.append(source)
            ra_lst.append(ata_sources.check_source(source)['ra'])
            dec_lst.append(ata_sources.check_source(source)['dec'])
            print(source, ata_sources.check_source(source)['ra'], ata_sources.check_source(source)['dec'])
            
            #place elevation limits
            if 85 > ata_sources.check_source(source)['el'] > 19:
                lista.append(source)
                listb.append(ata_sources.check_source(source)['el']) 
            else:
                #print(str(source) + " is not high (or low) enough to observe, trying again once all others are targeted")
                continue
        else:
            #print(str(source) + " has been observed at " + str(freqs) + "MHz and " + str(freqs_c) + "MHz, moving to the next source") 
            continue

    print("Sources that can be observed now:")
    print(lista, listb)
    print("")
    print("Sources left to be observed at " + str(freqs))
    print("")
    print(src_lft)
    print(len(src_lft))
    
    listc = np.array([src_lft, ra_lst, dec_lst]).T

    #np.savetxt("sources_left_"+str(freqs)+".txt", listc, header = 'Source RA Dec', fmt='%s')
if __name__ == "__main__":
    main()
