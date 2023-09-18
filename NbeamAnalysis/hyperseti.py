'''
Let's give hyperseti a shot...
'''
# %%
import sys
sys.path.insert(0, "/home/ntusay/.local/lib/python3.10/site-packages/")
from hyperseti.pipeline import find_et
import plot_utils as ptu
import blimpy as bl
import numpy as np
from bisect import bisect
import scipy.interpolate as inter
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 12})
%matplotlib inline
# %%
def wfp(fils,f1,f2):
    wf_objs=[bl.Waterfall(f,f1,f2) for f in fils]
    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(20,7))
    for i in range(2):
        ptu.plot_waterfall_subplots(wf_objs[i],index=i,ax=ax,fig=fig,f_start=f1,f_stop=f2)
    plt.show()
    return None

def wf_data(fil,f1,f2):
    return bl.Waterfall(fil,f1,f2).grab_data(f1,f2)

def noise_median(s1,p=5):
    return np.median(s1[(s1>np.percentile(s1,p))&(s1<np.percentile(s1,100-p))])

def noise_std(s1,p=5):
    return np.std(s1[(s1>np.percentile(s1,p))&(s1<np.percentile(s1,100-p))])

def mySNR(signal_array,noise_array):
    peaks=[]
    for time_row in signal_array:
        peaks.append(max(time_row)**2)
    signal = np.sqrt(np.median(peaks))
    noise=np.sqrt(noise_median(noise_array**2))
    return signal/noise
# %%

fil0 = '/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/fil_59884_17225_248799804_trappist1_0001-beam0000.h5'
fil1 = '/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/fil_59884_17225_248799804_trappist1_0001-beam0001.h5'

config = {
    'preprocess': {
        'sk_flag': True,                        # Apply spectral kurtosis flagging
        'normalize': True,                      # Normalize data
        'blank_edges': {'n_chan': 1024},          # Blank edges channels
        'blank_extrema': {'threshold': 10000},  # Blank ridiculously bright signals before search
        'poly_fit': 3                           # Subtract a 3-order polynomial bandpass 
    },
    'dedoppler': {
        'kernel': 'ddsk',                       # Doppler + kurtosis doppler (ddsk)
        'max_dd': 5.0,                         # Maximum dedoppler delay, 10 Hz/s
        'apply_smearing_corr': True,            # Correct  for smearing within dedoppler kernel 
        'plan': 'stepped'                       # Dedoppler trial spacing plan (stepped = less memory)
    },
    'hitsearch': {
        'threshold': 20,                        # SNR threshold above which to consider a hit
    },
    'pipeline': {
        'n_overlap': 1024,
        'merge_boxcar_trials': True,            # Merge hits at same frequency that are found in multiple boxcars
        'blank_hits':
            {
            'n_blank': 4,                        # Do 4 rounds of iterative blanking
            'padding': 16                        # Blank signal + 16 neighboring bins
            }                     
    }
}

# config = {
#     'preprocess': {
#         'sk_flag': True,                        # Apply spectral kurtosis flagging
#         'normalize': True,                      # Normalize data
#         'blank_edges': {'n_chan': 32},          # Blank edges channels
#         'blank_extrema': {'threshold': 10000}   # Blank ridiculously bright signals before search
#     },
#     'dedoppler': {
#         'kernel': 'ddsk',                       # Doppler + kurtosis doppler (ddsk)
#         'max_dd': 10.0,                         # Maximum dedoppler delay, 10 Hz/s
#         'apply_smearing_corr': True,            # Correct  for smearing within dedoppler kernel 
#         'plan': 'stepped'                       # Dedoppler trial spacing plan (stepped = less memory)
#     },
#     'hitsearch': {
#         'threshold': 20,                        # SNR threshold above which to consider a hit
#     },
#     'pipeline': {
#         'merge_boxcar_trials': True             # Merge hits at same frequency that are found in multiple boxcars
#     }
# }
# %%
freq_span = 20 # MHz
coarse_chn_size = 0.5 # MHz
gulp = int(freq_span/coarse_chn_size) # number of coarse channels
gulp=2**20
gulp=int(0.5*1e6/8)

# hit_browser0 = find_et(fil0, 
#                     config, 
#                     filename_out='/home/ntusay/scripts/hyperseti/test0.csv',
#                     filetype_out='csv',
#                     gulp_size=gulp)

# hit_browser1 = find_et(fil1, 
#                     config, 
#                     filename_out='/home/ntusay/scripts/hyperseti/test1.csv',
#                     filetype_out='csv',
#                     gulp_size=gulp)

# display(hit_browser.hit_table)
# %%
hit_browser0.view_hit(10, padding=50)
# %%
'''
Plot the first hit in the target beam
'''
hit_browser0.view_hit(10, padding=50, plot='dual')
# hit_browser0.view_hit(10, padding=50, plot='waterfall')
plt.tight_layout()
plt.show()
# %%
'''
Plot the first hit in the off-target beam
'''
# hit_browser1.view_hit(0, padding=250, plot='dual')
hit_browser1.view_hit(0, padding=50, plot='waterfall')
plt.tight_layout()
plt.show()

# %%
'''
Define the frequency range around the known hit
'''
frange=250*1e-6
fmid=6855.999203
f1=fmid-frange/2
f2=fmid+frange/2
# %%
'''
My waterfall plots
'''
fils=[fil0,fil1]
wfp(fils,f1,f2)
# %%
'''
Do my own SNR calculation on the data matrix
'''
freqs,s0=wf_data(fil0,f1,f2)
freqs,s1=wf_data(fil1,f1,f2)

SNR0=mySNR(s0,s0)
SNR1=mySNR(s1,s1)
print(f'SNR0: {SNR0:.3f}\t\tSNR1: {SNR1:.3f}\t\tSNR-ratio: {SNR0/SNR1:.3f}')
# %%
# %%
# %%
'''
Let's try it with some of the mars data
'''

mfil0 = '/mnt/buf0/mars/fil_60136_71961_811719848_mars_0001-beam0000.h5'
mfil1 = '/mnt/buf0/mars/fil_60136_71961_811719848_mars_0001-beam0001.h5'

# mars0 = find_et(mfil0, 
#                     config, 
#                     filename_out='/home/ntusay/scripts/hyperseti/mars0.csv',
#                     filetype_out='csv',
#                     gulp_size=2**20)

# mars1 = find_et(mfil1, 
#                     config, 
#                     filename_out='/home/ntusay/scripts/hyperseti/mars1.csv',
#                     filetype_out='csv',
#                     gulp_size=2**20)
# %%               
mars0.view_hit(0, padding=750, plot='waterfall')
plt.tight_layout()
plt.show()

mars1.view_hit(0, padding=750, plot='waterfall')
plt.tight_layout()
plt.show()
# %%
frange=1000*1e-6
fmid=8430.741547
f1=fmid-frange/2
f2=fmid+frange/2
freqs,s0=wf_data(mfil0,f1,f2)
freqs,s1=wf_data(mfil1,f1,f2)
SNR0=mySNR(s0,s0)
SNR1=mySNR(s1,s1)
print(f'SNR0: {SNR0:.3f}\t\tSNR1: {SNR1:.3f}\t\tSNR-ratio: {SNR0/SNR1:.3f}')

# %%
fil0='/mnt/datac-netStorage-40G/projects/p004/2022-11-01-04:44:33/fil_59884_17225_248799804_trappist1_0001/seti-node4.1/fil_59884_17225_248799804_trappist1_0001-beam0000.fil'
waterfall_data = bl.Waterfall(fil0,load_data=False)
fch1 = waterfall_data.header['fch1']
fstart = fch1 + waterfall_data.header['foff'] * waterfall_data.header['nchans']
# fstart=6845.000002
# fend=6865.000002
# fspan=fend-fstart
# gulp=int(gulp/100)
# gulp=40
MHz=0.005
MHz=0.0005
gulp=int((fch1-fstart)/MHz)
gulp=1000
fmids=[]
medPs=[]
for i in range(gulp):
    f1=fstart+i*MHz#fspan/gulp
    f2=f1+MHz#fspan/gulp
    frange,s0=wf_data(fil0,f1,f2)
    # aveP = s0.sum(axis=0)/np.shape(s0)[0]
    medPs.append(np.median(s0))
    fmids.append(np.median(frange))
plt.scatter(fmids,medPs,color='k')
plt.yscale('log')
plt.xticks(np.linspace(fstart,f2,5))
plt.show()
# %%

Pfit = inter.UnivariateSpline (fmids, medPs, s=0.1)
plt.scatter(fmids,medPs,color='k')
plt.plot(fmids,Pfit(fmids),color='orange')
plt.yscale('log')
plt.xticks(np.linspace(fstart,f2,5))
plt.show()
# %%

def fit_noise(fil,fmid,coarse_channel_size=0.5): # MHz
    waterfall_data = bl.Waterfall(fil,load_data=False)
    fch1 = waterfall_data.header['fch1']
    fstart = fch1 + waterfall_data.header['foff'] * waterfall_data.header['nchans']
    num_coarse_channels = int((fch1-fstart)/coarse_channel_size)
    slice_freq_span = 5000*1e-6 # 5 kHz
    nslices = int(coarse_channel_size/slice_freq_span)
    coarse_channels=np.linspace(fstart,fch1,num_coarse_channels+1)
    coarse_channel_start_index=bisect(coarse_channels,fmid)-1
    fstart=coarse_channels[coarse_channel_start_index]
    freq_mids=np.zeros(nslices)
    power_medians=np.zeros(nslices)
    for fslice in range(nslices):
        f1 = fstart+fslice*slice_freq_span
        f2 = f1 + slice_freq_span
        frange,s0=wf_data(fil,f1,f2)
        power_medians[fslice]=noise_median(s0)
        freq_mids[fslice]=np.median(frange)
    power_fit = inter.UnivariateSpline(freq_mids, power_medians, s=0.1)
    return freq_mids,power_fit(freq_mids)

# %%
fil0='/mnt/datac-netStorage-40G/projects/p004/2022-11-01-04:44:33/fil_59884_17225_248799804_trappist1_0001/seti-node4.1/fil_59884_17225_248799804_trappist1_0001-beam0000.fil'
freqs,power=fit_noise(fil0,fmid=6840.0)
plt.plot(freqs,power)
plt.yscale('log')
plt.xlim(6839.850000,6839.850500)
plt.grid(which='both',axis='both')

frange,s0=wf_data(fil0,6839.850000,6839.850500)
noise=np.interp(frange,freqs,power)
plt.scatter(frange,noise,color='orange')
plt.show()
# %%
def fitted_noise_median(fil,frange):
    fmid=np.median(frange)
    freqs,power=fit_noise(fil,fmid)
    return np.interp(frange,freqs,power)

# %%

def mid_90(s1,p=5):
    return s1[(s1>np.percentile(s1,p))&(s1<np.percentile(s1,100-p))]

def calc_noise(fil,freqs,s1):
    noise_profile=fitted_noise_median(fil,freqs)
    zero_centered=s1-noise_profile
    zeroed_noise=mid_90(zero_centered)
    N=len(zeroed_noise.flatten())
    # print(N)
    plt.hist(zeroed_noise,bins=int(N/1000))
    return np.sqrt(np.sum((zeroed_noise)**2)/N)

# %%
def hist_frame(fil,f1=8431.239299,f2=8431.243799):
    frange,power=wf_data(fil,f1,f2)
    noise=calc_noise(fil,frange,power)
    signal_els=mid_90(power[power>noise])
    signal=np.percentile(signal_els,95)
    signal=np.sqrt(np.sum((signal_els-np.median(signal_els))**2)/len(signal_els))
    signal=np.median(signal_els)
    print(f"noise: {noise:.3e}\tsignal: {signal:.3e}\tSNR: {signal/noise:.4f}")
    plt.hist(signal_els,bins=int(len(signal_els.flatten())/1000),color='orange')
    ylims=plt.gca().get_ylim()
    plt.vlines(noise,0,ylims[1],linestyles='--',colors='purple',label='noise')
    plt.vlines(signal,0,ylims[1],linestyles=':',colors='k',label='signal')
    plt.xlim(-2*noise,2*signal)
    plt.legend()
    plt.show()
    return None

def simple_hist(fil,f1=8431.239299,f2=8431.243799):
    frange,power=wf_data(fil,f1,f2)
    noise_els=mid_90(power)
    N=len(noise_els.flatten())
    noise=np.sqrt(np.sum((noise_els-noise_median(power))**2)/N)
    plt.hist(noise_els-noise_median(power))#,bins=int(N/1000))
    above_noise=power[power>noise]
    signal_els=above_noise[above_noise>np.percentile(above_noise,5)]
    signal=np.percentile(signal_els,95)
    signal_els=[]
    for line in power:
        [signal_els.append(el) for el in line[line>(noise_median(power)+noise_std(power))]]
    print(f"Noise median: {noise_median(power):.3e}\tPower spike elements: {len(signal_els)}")
    signal=np.median(sorted(signal_els)[-32:])
    print(f"noise: {noise:.3e}\tsignal: {signal:.3e}\tSNR: {signal/noise:.4f}")
    plt.hist(signal_els,color='orange')#,bins=int(len(signal_els.flatten())/10))
    ylims=plt.gca().get_ylim()
    plt.vlines(noise,0,ylims[1],linestyles='--',colors='purple',label='noise')
    plt.vlines(signal,0,ylims[1],linestyles=':',colors='k',label='signal')
    plt.xlim(-2*noise,2*signal)
    plt.legend()
    plt.xscale('log')
    plt.xlim(0.5*noise,2*signal)
    plt.show()
    return signal/noise

def simple_hist2(fil,f1=8431.239299,f2=8431.243799):
    frange,power=wf_data(fil,f1,f2)
    median_noise=noise_median(power)
    noise_els=mid_90(power)
    zeroed_noise=noise_els-noise_median(power)
    plt.hist(zeroed_noise)
    std_noise=np.sqrt(np.median((noise_els-median_noise)**2))
    signal_els=power[(power>10*std_noise)&(power>np.percentile(power,95))]
    signal=np.median(sorted(signal_els)[-np.shape(power)[0]:])-median_noise
    SNR=signal/std_noise
    print(f"Noise els: {len(noise_els)}\tSignal els: {len(signal_els)}")
    print(f"noise median: {median_noise:.3e}")
    print(f"std_noise: {std_noise:.3e}\tsignal: {signal:.3e}\tSNR: {SNR:.3f}")
    # min_value = min(signal_els)
    # max_value = max(signal_els)
    # num_bins = 20 
    # bin_edges = np.logspace(np.log10(min_value), np.log10(max_value), num=num_bins)

    plt.hist(signal_els,color='orange')#,bins=bin_edges)#int(len(signal_els.flatten())/10))
    ylims=plt.gca().get_ylim()
    plt.vlines(std_noise,0,ylims[1],linestyles='--',colors='purple',label='noise')
    plt.vlines(10*std_noise,0,ylims[1],linestyles='-.',colors='green',label='10 sigma')
    plt.vlines(signal,0,ylims[1],linestyles=':',colors='k',label='signal')
    plt.xlim(-2*std_noise,2*signal)
    plt.legend()
    plt.xscale('log')
    plt.yscale('log')
    plt.xlim(0.5*std_noise,2*signal)
    plt.show()
    return SNR
# %%
fil0_mars='/mnt/buf0/mars/fil_60136_71961_811719848_mars_0001-beam0000.h5'
fil1_mars='/mnt/buf0/mars/fil_60136_71961_811719848_mars_0001-beam0001.h5'

SNR0=simple_hist2(fil0_mars)
SNR1=simple_hist2(fil1_mars)
print(f"SNR_ratio: {SNR0/SNR1:.3f}")
# %%
f1=8445.484345
f2=8445.491563
SNR0=simple_hist2(fil0_mars,f1,f2)
SNR1=simple_hist2(fil1_mars,f1,f2)
print(f"SNR_ratio: {SNR0/SNR1:.3f}")
# %%
fil0_mars='/mnt/buf0/mars/fil_60157_67188_922170715_mars_0001-beam0000.h5'
fil0_mars='/mnt/buf0/mars/fil_60157_67188_922170715_mars_0001-beam0001.h5'

f1=8430.301818
f2=8430.305416
SNR0=simple_hist2(fil0_mars,f1,f2)
SNR1=simple_hist2(fil1_mars,f1,f2)
print(f"SNR_ratio: {SNR0/SNR1:.3f}")
# %%
hist_frame(fil0_mars)
# %%
fil0='/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/fil_59884_17225_248799804_trappist1_0001-beam0000.h5'
fil1='/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/fil_59884_17225_248799804_trappist1_0001-beam0001.h5'
fmid=6855.999203
f1=fmid-500*1e-6
f2=fmid+500*1e-6
SNR0=simple_hist2(fil0,f1,f2)
SNR1=simple_hist2(fil1,f1,f2)
print(f"SNR_ratio: {SNR0/SNR1:.3f}")
# %%
fil1_mars='/mnt/buf0/mars/fil_60136_71961_811719848_mars_0001-beam0001.h5'
frange1_mars,s1_mars=wf_data(fil1_mars,8431.239299,8431.243799)
noise1=calc_noise(fil1_mars,frange1_mars,s1_mars)
signal1_els=s1_mars[s1_mars>noise1]
signal1=np.percentile(signal1_els,95)
signal1=np.median(signal1_els)
print(f"noise: {noise1:.3e}\tsignal: {signal1:.3e}\tSNR: {signal1/noise1:.4f}")
plt.hist(signal1_els[signal1_els<=2*signal1],bins=int(len(signal1_els.flatten())/1000),color='orange')
plt.vlines(noise1,0,3000,linestyles=':',colors='k')
plt.vlines(signal1,0,3000,linestyles=':',colors='k')
# plt.xscale('log')
plt.xlim(-2*noise1,2*signal1)
plt.show()
# %%
# %%
def get_SNR(data_array,snr_threshold=10):
    noise_RMS = get_noise_RMS(data_array)
    normalized_data = (data_array/noise_RMS).flatten()
    signal_elements = normalized_data[normalized_data>=snr_threshold]
    signal_RMS = np.sqrt(np.median(signal_elements**2))
    return signal_RMS

def get_noise_RMS(data_array,snr_threshold=10):
    array=data_array.flatten()
    check=10
    while check>0:
        median_noise=np.median(array)
        just_noise=array[array/median_noise<snr_threshold]
        print(check,median_noise,len(array))
        if len(just_noise)==len(array):
            check=0
        else:
            array=array[array/median_noise<snr_threshold]
            check-=1
    return np.sqrt(np.median(just_noise**2))
    

# %%
frange=250*1e-6
fmid=6855.999203
f1=fmid-frange/2
f2=fmid+frange/2
freqs,s0=wf_data(fil0,f1,f2)
freqs,s1=wf_data(fil1,f1,f2)
# get_SNR(s0),get_SNR(s1),get_SNR(s0)/get_SNR(s1)
mySNR(s0,s0),mySNR(s1,s1),mySNR(s0,s0)/mySNR(s1,s1)
# %%
# %%
