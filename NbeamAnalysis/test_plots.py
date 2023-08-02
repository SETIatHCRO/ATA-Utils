# %%
import numpy as np
import pandas as pd
import blimpy as bl
import time
import matplotlib.pyplot as plt
%matplotlib inline
import plot_utils as ptu

# elapsed time function
def get_elapsed_time(start=0):
    end = time.time() - start
    time_label = 'seconds'    
    if end > 3600:
        end = end/3600
        time_label = 'hours'
    elif end > 60:
        end = end/60
        time_label = 'minutes'
    return end, time_label

def wf_data(fil,f1,f2):
    return bl.Waterfall(fil,f1,f2).grab_data(f1,f2)

def wf_plot(wf_objs,fils,f1,f2):
    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(20,7))
    for i in range(2):
        ptu.plot_waterfall_subplots(wf_objs[i],fils[i],index=i,ax=ax,fig=fig,f_start=f1,f_stop=f2)
    plt.show()
    return None
# %%
start=time.time()

fil0 = '/home/ntusay/scripts/NbeamAnalysis/injection_test/fil_59884_17225_248799804_trappist1_0001-beam0000.fil'
fil1 = '/home/ntusay/scripts/NbeamAnalysis/injection_test/fil_59884_17225_248799804_trappist1_0001-beam0001.fil'
f2 = 6855.999611
f1 = 6855.99936
freqs,s0=wf_data(fil0,f1,f2)
freqs,s1=wf_data(fil1,f1,f2)
for line in s0:
    plt.plot(freqs,line)
plt.yscale('log')
plt.show()
# %%
fils=[fil0,fil0[:-5]+'1.fil']
wf_objs=[bl.Waterfall(f,f1,f2) for f in fils]
wf_plot(wf_objs,fils,f1,f2)
# %%
