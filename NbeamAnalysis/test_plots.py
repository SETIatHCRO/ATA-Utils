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

def wf_plot(fils,f1,f2):
    wf_objs=[bl.Waterfall(f,f1,f2) for f in fils]
    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(20,7))
    for i in range(2):
        ptu.plot_waterfall_subplots(wf_objs[i],index=i,ax=ax,fig=fig,f_start=f1,f_stop=f2)
    plt.show()
    return None

def mean_noise(s1,p=5):
    return np.mean(s1[(s1>np.percentile(s1,p))&(s1<np.percentile(s1,100-p))])

def median_noise(s1,p=5):
    return np.median(s1[(s1>np.percentile(s1,p))&(s1<np.percentile(s1,100-p))])

def shift_array_with_drift(array, drift_rate, time_interval=16, freq_interval=1):
    # Calculate the number of elements to shift for each row
    num_elements_to_shift = int(drift_rate * time_interval / abs(freq_interval))
    # Make sure the shift is within the array's bounds
    num_columns = array.shape[1]
    num_rows = array.shape[0]
    # Create a new shifted array
    array1=array[::-1]
    shifted_array = np.zeros_like(array1)
    shifted_array[0] = array1[0]
    # Shift each row
    for r, row in enumerate(array1):
        row_shift = r * num_elements_to_shift
        # Calculate the index to start copying from
        shifted_array[r] = np.append(array1[r][row_shift:],array1[r][:row_shift])
    return shifted_array[::-1]
# %%
start=time.time()

fil0 = '/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/fil_59884_17225_248799804_trappist1_0001-beam0000.h5'
fil1 = '/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/fil_59884_17225_248799804_trappist1_0001-beam0001.h5'
fil0='/mnt/buf0/mars/fil_60157_68032_922222229_mars_0001-beam0000.h5'
fil1='/mnt/buf0/mars/fil_60157_68032_922222229_mars_0001-beam0001.h5'

drift_rate=0.070518*1e-6
fmid = 6855.499203+0.000039
f1=fmid-0.00005
f2=fmid+0.00005

drift_rate=0.131731
fmid = 8402.577652
f1=fmid-0.000250
f2=fmid+0.000250

freqs0,s0=wf_data(fil0,f1,f2)
freqs1,s1=wf_data(fil0,fmid-0.05,fmid+0.05)
fil_meta = bl.Waterfall(fil0,load_data=False)
tsamp = fil_meta.header['tsamp']
frez = fil_meta.header['foff']
s0=shift_array_with_drift(s0, drift_rate, tsamp,frez)
peaks=[]
for line in s0:
    peaks.append(max(line)**2)
    plt.plot(freqs0,line)
signal=np.sqrt(np.mean(peaks))
plt.scatter(fmid,signal,color='k',zorder=100)
plt.hlines(median_noise(s0),freqs0[0],freqs0[-1],linestyle='--',color='k',lw=3)
plt.hlines(median_noise(s1),freqs0[0],freqs0[-1],linestyle='--',color='red',lw=3)
plt.hlines(median_noise(np.delete(s0,np.s_[30:70],1)),freqs0[0],freqs0[-1],linestyle='--',color='green',lw=3)
plt.yscale('log')
plt.show()
print(signal/median_noise(s1))
# %%

# %%
f1 = 6855.479054
f2 = 6855.519353
fmid = 6855.499203
f1=fmid-0.0005
f2=fmid+0.0005
fils=[fil0,fil1]
wf_objs=[bl.Waterfall(f,f1,f2) for f in fils]
wf_plot(wf_objs,fils,f1,f2)
# %%
fmid = 8402.577652
f1=fmid-0.000250
f2=fmid+0.000250
fils=[fil0,fil1]
wf_objs=[bl.Waterfall(f,f1,f2) for f in fils]
freqs0,s0=wf_objs[0].grab_data(f1,f2)
freqs1,s1=wf_objs[1].grab_data(f1,f2)
def plot_data(s0,s1):
    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(20,7))
    extent0 = ptu.calc_extent(plot_f=freqs0, plot_t=np.linspace(0,600,16))
    extent1 = ptu.calc_extent(plot_f=freqs1, plot_t=np.linspace(0,600,16))
    ax[0].imshow(ptu.normalize(s0),aspect='auto',origin='lower',rasterized=True,interpolation='nearest',extent=extent0,cmap='viridis')
    ax[1].imshow(ptu.normalize(s1),aspect='auto',origin='lower',rasterized=True,interpolation='nearest',extent=extent1,cmap='viridis')
    fig.tight_layout(rect=[0, 0, 1, 1.05])
    plt.show()
    return None
plot_data(s0,s1)
# %%
s0=wf_objs[0].grab_data(f1,f2)[1]
s1=wf_objs[1].grab_data(f1,f2)[1]
DR=0.070518*1e-6
DR=0.131731*1e-6
fil_meta = bl.Waterfall(fil0,load_data=False)
tsamp = fil_meta.header['tsamp']
frez = fil_meta.header['foff']
s0=shift_array_with_drift(s0,DR,tsamp,frez)
s1=shift_array_with_drift(s1,DR,tsamp,frez)
plot_data(s0,s1)
# %%
datdir='/home/ntusay/scripts/mars/'
fildir='/mnt/buf0/mars/'
import DOT_utils as DOT
import blimpy as bl
import glob
beam='0000'
dat_files,errors=DOT.get_dats(datdir,beam)
for d,dat in enumerate(dat_files):
    dat1=dat.replace('beam0000','beam0001')
    fil0=sorted(glob.glob(fildir+dat.split('/')[-1][:-4]+'.h5'))[0]
    fil1=fil0.replace('beam0000','beam0001')
    fils=[fil0,fil1]
    df0 = DOT.load_dat_df(dat,fils)
    df0 = df0.sort_values('Corrected_Frequency').reset_index(drop=True)
    df1 = DOT.load_dat_df(dat1,fils)
    df1 = df1.sort_values('Corrected_Frequency').reset_index(drop=True)
    for r,row in df0.iterrows():
        SNR0=row['SNR']
        cf=row['Corrected_Frequency']
        DR=row['Drift_Rate']
        for r1,row1 in df1.iterrows():
            if cf+1e-6>=row1['Corrected_Frequency'] and cf-1e-6<=row1['Corrected_Frequency']:
                SNR1=row1['SNR']
                print(f"dat: {d}\trow: {r}\tSNR0:{SNR0:.3f}\tSNR1:{SNR1:.3f}\ttSETI SNRr: {SNR0/SNR1:.3f}")
                mySNR0=get_SNR(fil0,DR,cf)
                mySNR1=get_SNR(fil1,DR,cf)
                print(f"\tMine: SNR0: {mySNR0:.3f}\tSNR1: {mySNR1:.3f}\tSNRr: {mySNR0/mySNR1:.3f}")

# %%
def get_SNR(fil0,DR,cf):
    fil_meta = bl.Waterfall(fil0,load_data=False)
    tsamp = fil_meta.header['tsamp']
    frez = fil_meta.header['foff']
    obs_length=fil_meta.n_ints_in_file * fil_meta.header['tsamp']
    half_span=abs(DR)*obs_length*1.2  # x1.2 for padding
    if half_span<250:
        half_span=250
    f2=round(cf+half_span*1e-6,6)
    f1=round(cf-half_span*1e-6,6)
    freqs0,s0=wf_data(fil0,f1,f2)
    peaks=[]
    for line in s0:
        peaks.append(max(line)**2)
    signal = np.sqrt(np.mean(peaks))
    f2=cf+0.05
    f1=cf-0.05
    freqs1,s1=wf_data(fil0,f1,f2)
    noise=np.sqrt(median_noise(s0**2))
    return signal/noise
# %%
# %%
import numpy as np
# import blimpy as bl
import DOT_utils as DOT

dat_file='/mnt/datac-netStorage-40G/projects/p004/PPO/2022-11-05-00:42:37/fil_59888_05429_269173583_trappist1_0001/seti-node5.1/fil_59888_05429_269173583_trappist1_0001-beam0000.dat'
fil0='/mnt/datac-netStorage-40G/projects/p004/2022-11-05-00:42:37/fil_59888_05429_269173583_trappist1_0001/seti-node5.1/fil_59888_05429_269173583_trappist1_0001-beam0000.fil'
fil1='/mnt/datac-netStorage-40G/projects/p004/2022-11-05-00:42:37/fil_59888_05429_269173583_trappist1_0001/seti-node5.1/fil_59888_05429_269173583_trappist1_0001-beam0001.fil'
filtuple=[fil0,fil1]
beam='0000'
sf=4
df0=DOT.load_dat_df(dat_file,filtuple)
df1=DOT.cross_ref(df0,sf)
# %%
df_combed=DOT.comb_df(df1,pickle_off=True)
# %%
row=df_combed[df_combed.SNR_ratio.isnull()].reset_index(drop=True)
# %%
import blimpy as bl
target_fil = row['fil_0000'][0]
fil_meta = bl.Waterfall(target_fil,load_data=False)
# determine the frequency boundaries in the .fil file
minimum_frequency = fil_meta.container.f_start
maximum_frequency = fil_meta.container.f_stop
# calculate the narrow signal window using the assumed drift rate and metadata
tsamp = fil_meta.header['tsamp']
frez = fil_meta.header['foff']
obs_length=fil_meta.n_ints_in_file * tsamp
DR = row['Drift_Rate'][0]
padding=1+np.log10(row['SNR'][0])/10
half_span=abs(DR)*obs_length*padding  # x1.1 for padding
half_span
if half_span<250:
    half_span=250
fmid = row['Corrected_Frequency'][0]
f1=round(max(fmid-half_span*1e-6,minimum_frequency),6)
f2=round(min(fmid+half_span*1e-6,maximum_frequency),6)
# grab the signal data in the target beam fil file
frange,s0=DOT.wf_data(target_fil,f1,f2)
len(s0.flatten()),len(s0[s0>0])
SNR0 = DOT.mySNR(s0)
SNR0
# %%
other_fil=row['fil_0001'][0]
_,s1=DOT.wf_data(other_fil,f1,f2)
power=s1
median_noise=DOT.noise_median(power) # get the median for the middle 90 percent of data
noise_els=DOT.mid_90(power)             # call the middle 90 percent of data the "noise"
zeroed_noise=noise_els-median_noise     # zero out the noise by subtracting off the median
std_noise=np.sqrt(np.median((zeroed_noise)**2)) # get the standard deviation of the "noise"
signal_els=power[(power>10*std_noise)&(power>np.percentile(power,95))] 
len(signal_els),len(sorted(signal_els)[-np.shape(power)[0]:])
if not bool(signal_els.size):
    signal=std_noise
else:
    signal=np.median(sorted(signal_els)[-np.shape(power)[0]:])-median_noise 
SNR1=signal/std_noise
SNR0,SNR1,SNR0/SNR1
# %%
counter=0
for i,el in enumerate(s1.flatten()):
    if isinstance(el,np.float32)==False:
        print(el,type(el))
        counter+=1
print(counter)
# %%
# %%
