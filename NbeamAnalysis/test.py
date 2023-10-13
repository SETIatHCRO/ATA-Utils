# %%
import pandas as pd
import os
import glob
from DOT_utils import check_logs
from DOT_utils import get_dats

# %%
df0=pd.read_csv('/home/ntusay/scripts/NbeamAnalysis/injection_test/fil_59884_17225_248799804_trappist1_0001-beam0000.dat',
                skiprows=9,delim_whitespace=True, 
                names=['Top_Hit_#','Drift_Rate','SNR', 'Uncorrected_Frequency','Corrected_Frequency',
                        'Index','freq_start','freq_end','SEFD','SEFD_freq','Coarse_Channel_Number',
                        'Full_number_of_hits']).reset_index(drop=True)
df1=pd.read_csv('/home/ntusay/scripts/NbeamAnalysis/injection_test/fil_59884_17225_248799804_trappist1_0001-beam0001.dat',
                skiprows=9,delim_whitespace=True, 
                names=['Top_Hit_#','Drift_Rate','SNR', 'Uncorrected_Frequency','Corrected_Frequency',
                        'Index','freq_start','freq_end','SEFD','SEFD_freq','Coarse_Channel_Number',
                        'Full_number_of_hits']).reset_index(drop=True)

for r0,row0 in df0.iterrows():
    fmid_0 = row0["Corrected_Frequency"]
    f1_0 = row0["freq_start"]
    f2_0 = row0["freq_end"]
    for r1,row1 in df1.iterrows():
        fmid_1 = row1["Corrected_Frequency"]
        f1_1 = row1["freq_start"]
        f2_1 = row1["freq_end"]
        if fmid_1-2e-6 <= fmid_0 <= fmid_1+2e-6 and f1_1-2e-6 <= f1_0 <= f1_1+2e-6 and f2_1-2e-6 <= f2_0 <= f2_1+2e-6:
            print(max(fmid_0,f1_0,f2_0))

# %%
import os
import glob
import pandas as pd
from DOT_utils import check_logs
from DOT_utils import get_dats

def dat_hits(dat_dir,beam):
    dat_files,errors=get_dats(dat_dir,beam)
    hits=0
    for dat in dat_files:
        hits+=len(open(dat,'r').readlines())-9
    return hits

def csv_hits(csv_dir):
    csv_hits=[]
    csvs=sorted(glob.glob(csv_dir+'*.csv'))
    for csv in csvs:
        csv_hits.append(len(pd.read_csv(csv)))
    return csv_hits

def comp_hits(dat_dirs,beam,csv_dir):
    tot=0
    totf=0
    print("original hits --> spatially filtered hits")
    csv_hits_list=csv_hits(csv_dir)
    for d,dir in enumerate(sorted(dat_dirs)):
        dhits=dat_hits(dir,beam)
        if len(csv_hits_list)<d+1:
            print(f"csv list error")
            continue
        else:
            filts=csv_hits_list[d]
        print(f'{"-".join(dir.split("/")[-1].split("-")[1:3])}: ',
                dhits,
                f" -->  {filts}",
                f"  ({(dhits-filts)/dhits*100:.1f}% reduction)")
        tot+=dhits
        totf+=filts
    print(f'{tot} total hits found in all target beam dat files')
    print(f'{totf} total hits remaining after spatial filtering')
    print(f"{(tot-totf)/tot*100:.1f}% reduction")
    return None
# %%

PPO='/mnt/datac-netStorage-40G/projects/p004/PPO/'
dat_dirs=sorted(glob.glob(PPO+'2022*'))
csv_dir='/home/ntusay/scripts/NbeamAnalysis/TRAPPIST-1/'
beam='0000'
comp_hits(dat_dirs,beam,csv_dir)
# %%
# PRINT OUT THE TOTAL NUMBER OF HITS FOR EACH OBSERVATION
PPO='/mnt/datac-netStorage-40G/projects/p004/PPO/'
beam='0000'
dat_dirs=sorted(glob.glob(PPO+'2022*'))
for dat_dir in dat_dirs:
    hits=dat_hits(dat_dir,beam)
    print(f"{dat_dir.split('/')[-1].split('2022-')[-1].split(':')[0][:-3]}\t{hits} hits")
# %%
import os
import glob
import blimpy as bl
import matplotlib.pyplot as plt
%matplotlib inline

def get_fils(root_dir,beam):
    """Recursively finds all files with the '.dat' extension in a directory
    and its subdirectories, and returns a list of the full paths of files 
    where each file corresponds to the target beam."""
    fil_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for f in filenames:
            if f.endswith('.fil') and f.split('beam')[-1].split('.')[0]==beam:
                fil_files.append(os.path.join(dirpath, f))
    return fil_files

def freq_span(dirs,beam):
    fmin=1e12
    fmax=0
    for d,dir in enumerate(dirs):
        f1s=[]
        f2s=[]
        fil_files = get_fils(dir,beam)
        label = "-".join(dir.split('/')[-1].split('2022-')[-1].split('-')[0:2])+"-22"
        for fil in fil_files:
            waterfall_data = bl.Waterfall(fil,load_data=False)
            fch1 = waterfall_data.header['fch1']
            fch2 = fch1 + waterfall_data.header['foff'] * waterfall_data.header['nchans']
            f1s.append(min(fch1,fch2))
            f2s.append(max(fch1,fch2))
        f1s=np.array(f1s)
        f2s=np.array(f2s)
        if d==1 or d==2 or d==3 or d==5:
            f1=min(f1s)
            f2=max(f2s)
            print(f'{label}\tfmin: {f1:.6f} \tfmax: {f2:.6f} MHz.\tSpan: {(f2-f1):.6f}' )
        elif d==0 or d==4:
            f11=min(f1s)
            f21=max(f2s[f2s<7500])
            f12=min(f1s[f1s>7500])
            f22=max(f2s)
            print(f'{label}\tfmin: {f11:.6f} \tfmax: {f21:.6f} MHz.\tSpan: {(f21-f11):.6f}' )
            print(f'\t\tfmin: {f12:.6f} \tfmax: {f22:.6f} MHz.\tSpan: {(f22-f12):.6f}' )
        elif d==6:
            f11=min(f1s)
            f21=max(f2s[f2s<6600])
            f12=min(f1s[f1s>6600])
            f22=max(f2s)
            print(f'{label}\tfmin: {f11:.6f} \tfmax: {f21:.6f} MHz.\tSpan: {(f21-f11):.6f}' )
            print(f'\t\tfmin: {f12:.6f} \tfmax: {f22:.6f} MHz.\tSpan: {(f22-f12):.6f}' )
        elif d==7:
            f11=min(f1s)
            f21=max(f2s[f2s<8500])
            f12=min(f1s[f1s>8500])
            f22=max(f2s)
            print(f'{label}\tfmin: {f11:.6f} \tfmax: {f21:.6f} MHz.\tSpan: {(f21-f11):.6f}' )
            print(f'\t\tfmin: {f12:.6f} \tfmax: {f22:.6f} MHz.\tSpan: {(f22-f12):.6f}' )
        # print(f'{label}\tfmin: {f1:.6f} \tfmax: {f2:.6f} MHz.\tSpan: {(f2-f1):.6f}' )
        # plt.plot([f1,f2],[label,label],label=label)
    # plt.legend()
    # plt.xlabel(f'Frequency Coverage (MHz)')
    # plt.ylabel(f'Observation Date')
    # plt.show()
    # print(f'Frequency coverage spans {fmin:.6f} to {fmax:.6f} MHz.')
    return None

PPO='/mnt/datac-netStorage-40G/projects/p004/'
dirs=sorted(glob.glob(PPO+'2022*'))
beam='0000'
freq_span(dirs,beam)
# %%
import os
import glob
import numpy as np
import blimpy as bl
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
plt.style.use('/home/ntusay/scripts/NbeamAnalysis/plt_format.mplstyle')
plt.rcParams.update({'font.size': 22})
plt.rcParams.update({'ytick.minor.visible': False})
plt.rcParams.update({'axes.labelsize': 18})
plt.rcParams.update({'xtick.labelsize': 14})
plt.rcParams.update({'ytick.labelsize': 14})
%matplotlib inline

def get_fils(root_dir,beam):
    """Recursively finds all files with the '.dat' extension in a directory
    and its subdirectories, and returns a list of the full paths of files 
    where each file corresponds to the target beam."""
    fil_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for f in filenames:
            if f.endswith('.fil') and f.split('beam')[-1].split('.')[0]==beam:
                fil_files.append(os.path.join(dirpath, f))
    return fil_files

def freq_span(dirs,beam,save=False):
    colors=['m','r','g','turquoise','blueviolet','b','indigo','violet']
    labels=[]
    dts=[]
    xmin=5000
    xmax=5000
    fig, ax = plt.subplots(1,1,figsize=(10,6))
    for d,dir in enumerate(dirs):
        fil_files = get_fils(dir,beam)
        label = "-".join(dir.split('/')[-1].split('2022-')[-1].split('-')[0:2])+"-22"
        dt=datetime.strptime(label, '%m-%d-%y')
        dts.append(dt)
        labels.append(dt.date())
        for fil in fil_files:
            waterfall_data = bl.Waterfall(fil,load_data=False)
            fch1 = waterfall_data.header['fch1']
            fch2 = fch1 + waterfall_data.header['foff'] * waterfall_data.header['nchans']
            ax.scatter(fch1,dt,color=colors[d])
            if fch1<xmin:
                xmin=fch1
            if fch1>xmax:
                xmax=fch1
    print(xmin,xmax)
    plt.yticks(labels)
    myFmt = mdates.DateFormatter('%m-%d')
    ax.yaxis.set_major_formatter(myFmt)
    ymin, ymax = ax.get_ylim()
    ax.set_ylim(ymin,ymax)
    xmin, xmax = ax.get_xlim()
    ax.set_xlim(xmin,xmax)
    plt.xticks(np.arange(1000,10000,1000))
    ax.axvspan(300,1000,alpha=0.1, color='orange',label='UHF')
    ax.axvspan(1000,2000,alpha=0.1, color='r',label='L')
    ax.axvspan(2000,4000,alpha=0.1, color='g',label='S')
    ax.axvspan(4000,8000,alpha=0.1, color='b',label='C')
    ax.axvspan(8000,12000,alpha=0.1, color='m',label='X')
    plt.xlabel(f'Frequency Coverage (MHz)')
    plt.ylabel(f'Observation Date')
    legend=plt.legend(loc='upper left',title='Band')
    plt.grid(True, which='major', axis='both', linestyle=':', linewidth=0.25, color='gray')
    path='/home/ntusay/scripts/processed2/'
    ext='pdf'
    if save==True:
        plt.savefig(f'{path}observations.{ext}',
                    bbox_inches='tight',format=ext,dpi=fig.dpi,facecolor='white', transparent=False)
    plt.show()
    # print(f'Frequency coverage spans {fmin:.6f} to {fmax:.6f} MHz.')
    return None

PPO='/mnt/datac-netStorage-40G/projects/p004/'
dirs=sorted(glob.glob(PPO+'2022*'))
beam='0000'
freq_span(dirs,beam,save=False)

# %%
import pandas as pd
import numpy as np
import blimpy as bl

def mean_noise(s1,p=5):
    return np.mean(s1[(s1>np.percentile(s1,p))&(s1<np.percentile(s1,100-p))])

def median_noise(s1,p=5):
    return np.median(s1[(s1>np.percentile(s1,p))&(s1<np.percentile(s1,100-p))])

def noise_std(s1,p=5):
    return np.std(s1[(s1>np.percentile(s1,p))&(s1<np.percentile(s1,100-p))])

def SNR_ratio(s0,s1):
    return s0.max()/median_noise(s0)/(s1.max()/median_noise(s1))

def SNR_ratio2(s0,s1):
    return (s0.max()-median_noise(s0))/noise_std(s0)/(((s1.max()-median_noise(s1)))/noise_std(s1))

def SNR_ratio3(s0,s1):
    time_bins0=np.shape(s0)[0]
    signal0 = np.median(sorted(s0.flatten())[-time_bins0:])
    time_bins1=np.shape(s1)[0]
    signal1 = np.median(sorted(s1.flatten())[-time_bins1:])
    return (signal0-median_noise(s0))/noise_std(s0)/(((signal1-median_noise(s1)))/noise_std(s1))

def get_df(dat_file):
    df = pd.read_csv(dat_file,delim_whitespace=True,
                    names=['Top_Hit_#','Drift_Rate','SNR', 'Uncorrected_Frequency','Corrected_Frequency','Index',
                    'freq_start','freq_end','SEFD','SEFD_freq','Coarse_Channel_Number','Full_number_of_hits'],skiprows=9)
    return df

def wf_data(fil,f1,f2):
    return bl.Waterfall(fil,f1,f2).grab_data(f1,f2)

def ACF(s1):
    return ((s1*s1).sum(axis=1)).sum()/np.shape(s1)[0]/np.shape(s1)[1]

# %%

# dat_file0='/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/fil_59884_17225_248799804_trappist1_0001-beam0000.dat'
# dat_file1='/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/fil_59884_17225_248799804_trappist1_0001-beam0001.dat'
# fil0=dat_file0[:-3]+'h5'
# fil1=dat_file1[:-3]+'h5'

# df0=get_df(dat_file0)
# df1=get_df(dat_file1)

csv='/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/output/obs_UNKNOWN_DOTnbeam.csv'
df=pd.read_csv(csv)

for r,row in df.iterrows():
    SNR=row['SNR']
    cf=row['Corrected_Frequency']
    f1=min(row['freq_start'],row['freq_end'])
    f2=max(row['freq_start'],row['freq_end'])
    fil0=row['fil_0000']
    fil1=row['fil_0001']
    _,s0=wf_data(fil0,f1,f2)
    _,s1=wf_data(fil1,f1,f2)
    SNR0=(s0.max()-median_noise(s0))/noise_std(s0)
    SNR1=(s1.max()-median_noise(s1))/noise_std(s1)
    SNRr2=SNR_ratio2(s0,s1)
    SNRr3=SNR_ratio3(s0,s1)
    SNRr4=row['SNR_ratio']
    x=row['x']
    print(f"{r} SNR: {SNR:.2f}\tFreq: {cf}  SNRr_old: {SNRr2:.3f}  SNRr_new: {SNRr3:.3f}") 
    # print(f"{r} SNR: {SNR:.2f}\tFreq: {cf}  SNRr: {SNRr2:.3f}  SNR0: {SNR0:.2f}\tSNR1: {SNR1:.2f}  new_x2: {x/SNRr2:.3f}")
    # print(f"{r} SNR: {SNR:.2f}\tFreq: {cf}  SNRr1:{SNRr1:.3f}  SNRr2:{SNRr2:.3f}  SNRr3:{SNRr3:.3f}  x: {x:.3f}")
# %%
import matplotlib.pyplot as plt
%matplotlib inline
i=5
row=df.iloc[i]
DR=row['Drift_Rate']
fmid=row['Corrected_Frequency']
fil_meta0=bl.Waterfall(fil0,load_data=False)
obs_length=fil_meta0.n_ints_in_file * fil_meta0.header['tsamp']
half_span=abs(row['Drift_Rate'])*obs_length*1.2  # x1.2 for padding
f2=round(fmid+half_span*1e-6,6)+500*1e-6
f1=round(fmid-half_span*1e-6,6)-500*1e-6
_,s0=wf_data(fil0,f1,f2)
_,s1=wf_data(fil1,f1,f2)
def normalize(x):
    return (x-x.min())/(x.max()-x.min())
s0=10*np.log10(s0)
s1=10*np.log10(s1)
s0=normalize(s0)
s1=normalize(s1)
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(20,7))
ax[0].imshow(s0,aspect='auto',origin='lower',rasterized=True,interpolation='nearest',cmap='viridis')
ax[1].imshow(s1,aspect='auto',origin='lower',rasterized=True,interpolation='nearest',cmap='viridis')
fig.tight_layout(rect=[0, 0, 1, 1.05])
plt.show()
# %%
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 22})
csv='/home/ntusay/scripts/TRAPPIST-1/obs_11-05_DOTnbeam.csv'
csv='/home/ntusay/scripts/parallel_test/obs_11-01_DOTnbeam.csv'
df=pd.read_csv(csv)
fig,ax=plt.subplots(figsize=(12,10))
plt.scatter(df.SNR_ratio,df.SNR,color='orange',alpha=0.5,edgecolor='k')
sf=4
plt.xlabel('SNR ratio')
plt.ylabel('SNR')
plt.yscale('log')
ylims=plt.gca().get_ylim()
plt.axhspan(sf,ylims[1],color='green',alpha=0.25,label='Attenuated Signals')
plt.axhspan(1/sf,sf,color='grey',alpha=0.25,label='Similar SNRs')
plt.axhspan(ylims[0],1/sf,color='brown',alpha=0.25,label='Off-beam Attenuated')
plt.ylim(ylims[0],ylims[1])
# plt.hlines(4.5,0,1,color='k',linestyle='--')
# plt.hlines(1,0,1,color='k',linestyle='--')
# plt.xlim(-0.01,1.01)
plt.legend().get_frame().set_alpha(0) 
plt.grid(which='major', axis='both', alpha=0.5,linestyle=':')
print(len(df[df.SNR_ratio>4.5]))
plt.show()
# %%
df.SNR_ratio_0001.max()
# %%
# %%
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 22})
%matplotlib inline
csv='/home/ntusay/scripts/parallel_test/obs_11-01_DOTnbeam.csv'
# csv='/home/ntusay/scripts/parallel_test/obs_10-27_DOTnbeam.csv'
# csv='/home/ntusay/scripts/parallel_test/obs_11-02_DOTnbeam.csv'
# csv='/home/ntusay/scripts/mars/output/obs_UNKNOWN_DOTnbeam.csv'
df=pd.read_csv(csv)
sf=4.5
fig,ax=plt.subplots(figsize=(12,10))
plt.scatter(df.SNR,df.SNR_ratio,color='orange',alpha=0.5,edgecolor='k')
xlims=plt.gca().get_xlim()
plt.axhspan(sf,ylims[1],color='green',alpha=0.25,label='Attenuated Signals')
plt.axhspan(1/sf,sf,color='grey',alpha=0.25,label='Similar SNRs')
plt.axhspan(ylims[0],1/sf,color='brown',alpha=0.25,label='Off-beam Attenuated')
# plt.hlines(sf,0.1*xlims[0],1.1*xlims[1],color='k',linestyle='--')
# plt.hlines(1/sf,0.1*xlims[0],1.1*xlims[1],color='k',linestyle='--')
plt.xscale('log')
ylims=plt.gca().get_ylim()
plt.ylim(ylims[0],ylims[1])
# plt.xlim(-0.01,1.01)
plt.ylabel('SNR-ratio')
plt.xlabel('SNR')
plt.grid(which='major', axis='both', alpha=0.5,linestyle=':')
plt.show()
# %%
# %%
sf=4.5
fig,ax=plt.subplots(figsize=(12,10))
plt.hist(df.SNR_ratio,bins=100)
ylims=plt.gca().get_ylim()
plt.vlines(sf,-0.1,ylims[1]*1.1,color='k',linestyle='--')
# plt.hlines(1/sf,-0.1,1.1,color='k',linestyle='--')
plt.ylim(1,ylims[1]*1.05)
plt.xlabel('SNR-ratio')
plt.ylabel('Count')
plt.yscale('log')
plt.grid(which='major', axis='both', alpha=0.5,linestyle=':')
plt.show()

# %%
dat_file='/mnt/datac-netStorage-40G/projects/p004/PPO/2022-11-01-04:44:33/fil_59884_17225_248799804_trappist1_0001/seti-node4.1/fil_59884_17225_248799804_trappist1_0001-beam0000.dat'
dat_df = pd.read_csv(dat_file,delim_whitespace=True, 
                names=['Top_Hit_#','Drift_Rate','SNR', 'Uncorrected_Frequency','Corrected_Frequency','Index',
                        'freq_start','freq_end','SEFD','SEFD_freq','Coarse_Channel_Number','Full_number_of_hits'],
                skiprows=9)
fil='/mnt/datac-netStorage-40G/projects/p004/2022-11-01-04:44:33/fil_59884_17225_248799804_trappist1_0001/seti-node4.1/fil_59884_17225_248799804_trappist1_0001-beam0000.fil'
fil_meta=bl.Waterfall(fil,load_data=False)
obs_length=fil_meta.n_ints_in_file * fil_meta.header['tsamp']
for r,row in dat_df.iterrows():
    tSETI_SNR=row['SNR']
    DR=row['Drift_Rate']
    half_span=abs(DR)*obs_length*1.2  # x1.2 for padding
    if half_span<100:
        half_span=5
    cf=row['Corrected_Frequency']
    f1=min(row['freq_start'],row['freq_end'])
    f2=max(row['freq_start'],row['freq_end'])
    f1=cf-0.025
    f2=cf+0.025
    big_diff=f2-f1
    _,s0=wf_data(fil,f1,f2)
    # SNR0=(s0-np.median(s0))/np.std(s0)
    fstart=round(cf+half_span*1e-6,6)
    fend=round(cf-half_span*1e-6,6)
    small_diff=fstart-fend
    _,s1=wf_data(fil,fend,fstart)
    s1=shift_array_with_drift(s1, DR*1e-6, fil_meta.header['tsamp'], fil_meta.header['foff'])
    peaks=[]
    for row in s1:
        peaks.append(max(row)**2)
    np.sqrt(np.mean(peaks))
    SNR0=(np.sqrt(np.mean(peaks))/np.sqrt(mean_noise(s0**2)))#/noise_std(s0)
    SNR1=(np.sqrt(np.mean(s1[(s1>np.percentile(s1,95))]**2))/np.sqrt(mean_noise(s0**2)))#/noise_std(s0)
    print(f"tSETI SNR: {tSETI_SNR:.2f}\ts0: {big_diff:.6f}\ts1: {small_diff:.6f}")
    print(f"My SNR: {SNR0:.2f}\t{SNR1:.2f}\n")
# %%
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
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 22})
%matplotlib inline

csv='/home/ntusay/scripts/parallel_test/obs_11-01_DOTnbeam.csv'
csv='/home/ntusay/scripts/parallel_test/obs_11-09_DOTnbeam.csv'
sf=4

full_df=pd.read_csv(csv)
x = full_df.corrs
SNRr = full_df.SNR_ratio
fig,ax=plt.subplots(figsize=(9,7))
xcutoff=np.linspace(0,1,10)
ycutoff=0.9*sf*xcutoff**2
plt.plot(xcutoff,ycutoff,linestyle='--',color='k',alpha=0.5,label='cutoff?')
plt.scatter(x,SNRr,color='orange',alpha=0.5,edgecolor='k')
plt.xlabel('Correlation Score')
plt.ylabel('SNR-ratio')
# plt.xscale('log')
ylims=plt.gca().get_ylim()
xlims=plt.gca().get_xlim()
plt.axhspan(sf,max(ylims[1],6.5),color='green',alpha=0.25,label='Attenuated Signals')
plt.axhspan(1/sf,sf,color='grey',alpha=0.25,label='Similar SNRs')
plt.axhspan(min(0.2,ylims[0]),1/sf,color='brown',alpha=0.25,label='Off-beam Attenuated')
plt.ylim(min(0.2,ylims[0]),max(ylims[1],6.5))
plt.xlim(-0.1,1.1)
plt.legend().get_frame().set_alpha(0) 
plt.grid(which='major', axis='both', alpha=0.5,linestyle=':')
plt.show()
counter=0
for i,score in enumerate(x):
    if np.interp(score,xcutoff,ycutoff)<SNRr[i]:
        counter+=1
print(f"{counter} signals above cutoff")
# %%
# %%
# PLOT MARS DATA

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 22})
%matplotlib inline

answers='/home/ntusay/scripts/mars/output/spacecraft_08-03-2023_no_pickle.csv'
csv='/home/ntusay/scripts/mars/output2/obs_UNKNOWN_DOTnbeam.csv'
csv='/home/ntusay/scripts/mars/output4/obs_UNKNOWN_DOTnbeam.csv'
df_ans=pd.read_csv(answers)
df_out=pd.read_csv(csv)
sf=4

counter=0
cutoff_tp=0
cutoff_fp=0
cutoff_rfi=0
redx=0
rfi=0
fig,ax=plt.subplots(figsize=(8,6))
xcutoff=np.linspace(0,1,10)
ycutoff=0.9*sf*xcutoff**2
plt.plot(xcutoff,ycutoff,linestyle='--',color='k',alpha=0.5,label='Nominal Cutoff')
for r,row in df_out.iterrows():
    x=row['corrs']
    y=row['SNR_ratio']
    test=False
    for r1,row1 in df_ans.iterrows():
        if row['Corrected_Frequency']==row1['frequency_on'] and row1['beam_centered']==1:
            if counter==0:
                plt.scatter(x,y,marker='o',color='g',s=100,alpha=0.75,edgecolors='k',label='Mars Probes')
            else:
                plt.scatter(x,y,marker='o',color='g',s=100,alpha=0.75,edgecolors='k')
            counter+=1
            test=True
            if np.interp(x,xcutoff,ycutoff)<y:
                cutoff_tp+=1
        elif row['Corrected_Frequency']==row1['frequency_on'] and row1['beam_centered']==0:
            if redx==0:
                plt.scatter(x,y,marker='x',color='r',s=75,label='False Positive')
            else:
                plt.scatter(x,y,marker='x',color='r',s=75)
            redx+=1
            test=True
            if np.interp(x,xcutoff,ycutoff)<y:
                cutoff_fp+=1
    if test==False:
        if rfi==0:
            plt.scatter(x,y,facecolors='k',edgecolors='r',s=100,alpha=0.5,label='Unidentified RFI')      
        else:
            plt.scatter(x,y,facecolors='k',edgecolors='r',s=100,alpha=0.5)      
        rfi+=1
        if np.interp(x,xcutoff,ycutoff)<y:
            cutoff_rfi+=1
print(f"Correctly Identified Spacecraft Signals: {counter}")
xlims=plt.gca().get_xlim()
ylims=plt.gca().get_ylim()
plt.axhspan(sf,max(ylims[1],6.5),color='green',alpha=0.25,label='Attenuated\nSignals')
plt.axhspan(1/sf,sf,color='grey',alpha=0.25,label='Similar SNRs')
plt.axhspan(min(0.2,ylims[0]),1/sf,color='brown',alpha=0.25,label='Off-beam\nAttenuated')
if ylims[1]>1000:
    plt.yscale('log')
    # plt.ylim(8,ylims[1])
plt.xlim(xlims[0],xlims[1])
plt.ylim(ylims[0],ylims[1])
plt.xlabel('DOT Scores')
plt.ylabel('SNR-ratio')
plt.legend(bbox_to_anchor=(1, 1)).get_frame().set_alpha(0) 
plt.grid(which='major', axis='both', alpha=0.5,linestyle=':')
save=True
save=False
if save==True:
    plt.savefig(f"{csv.split('.csv')[0]}.pdf",
                    bbox_inches='tight',format='pdf',dpi=fig.dpi,facecolor='white', transparent=False)
plt.show()
print(f"{cutoff_tp} true signals above cutoff")
print(f"{cutoff_fp} false positive signals above cutoff")
print(f"{cutoff_rfi} rfi signals above cutoff")
# %%
for r,row in df_out.iterrows():
    x=row['corrs']
    y=row['SNR_ratio']
    test=False
    for r1,row1 in df_ans.iterrows():
        SNR0=row1['snr_on']
        SNR1=row1['snr_off']
        if row['Corrected_Frequency']==row1['frequency_on'] and row1['beam_centered']==1:
            print(f"{r1}\tSNR0: {SNR0:.3f}\tSNR1: {SNR1:.3f}\tSNRr: {SNR0/SNR1:.3f}\tmySNRr: {row['SNR_ratio']:.3f}")
        elif row['Corrected_Frequency']==row1['frequency_on'] and row1['beam_centered']==0:
            print(f"{r1}\tSNR0: {SNR0:.3f}\tSNR1: {SNR1:.3f}\tSNRr: {SNR0/SNR1:.3f}\tmySNRr: {row['SNR_ratio']:.3f}")
# %%
import blimpy as bl
from bisect import bisect
import scipy.interpolate as inter

def noise_median(s1,p=5):
    return np.median(s1[(s1>np.percentile(s1,p))&(s1<np.percentile(s1,100-p))])

def noise_std(s1,p=5):
    return np.std(s1[(s1>np.percentile(s1,p))&(s1<np.percentile(s1,100-p))])

def mid_90(s1,p=5):
    return s1[(s1>np.percentile(s1,p))&(s1<np.percentile(s1,100-p))]

def mySNR(power):
    median_noise=noise_median(power)
    noise_els=mid_90(power)
    zeroed_noise=noise_els-median_noise
    std_noise=np.sqrt(np.median((zeroed_noise)**2))
    # std_noise=noise_std(power)
    signal_els=power[(power>10*std_noise)&(power>np.percentile(power,95))]
    signal=np.median(sorted(signal_els)[-np.shape(power)[0]:])-median_noise
    # signal=np.max(signal_els)-median_noise
    SNR=signal/std_noise
    return SNR

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
        frange,s0=bl.Waterfall(fil,f1,f2).grab_data(f1,f2)
        power_medians[fslice]=noise_median(s0)
        freq_mids[fslice]=np.median(frange)
    power_fit = inter.UnivariateSpline(freq_mids, power_medians, s=0.1)
    return freq_mids,power_fit(freq_mids)

def fitted_noise_median(fil,frange):
    fmid=np.median(frange)
    freqs,power=fit_noise(fil,fmid)
    return np.interp(frange,freqs,power)

def betterSNR(fil,f1,f2):
    frange,power=bl.Waterfall(fil,f1,f2).grab_data(f1,f2)
    noise_profile = fitted_noise_median(fil,frange)
    zeroed_power = power-noise_profile
    zeroed_noise=mid_90(zeroed_power)
    std_noise=np.sqrt(np.median((zeroed_noise)**2))
    # std_noise=noise_std(power)
    signal_els=zeroed_power[(zeroed_power>10*std_noise)&(zeroed_power>np.percentile(power,95))]
    signal=np.median(sorted(signal_els)[-np.shape(zeroed_power)[0]:])
    # signal=np.max(signal_els)-median_noise
    SNR=signal/std_noise
    return SNR
#%%
fmid=8430.747957
df=df_out[df_out.Corrected_Frequency==fmid].reset_index(drop=True)
fil0=df.fil_0000[0]
fil1=df.fil_0001[0]
fil_meta = bl.Waterfall(fil0,load_data=False)
minimum_frequency = fil_meta.container.f_start
maximum_frequency = fil_meta.container.f_stop
tsamp = fil_meta.header['tsamp']
frez = fil_meta.header['foff']
obs_length=fil_meta.n_ints_in_file * tsamp
DR = df.Drift_Rate[0]
half_span=abs(DR)*obs_length*1.1  # x1.1 for padding
if half_span<250:
    half_span=250
f2=round(min(fmid+half_span*1e-6,maximum_frequency),6)
f1=round(max(fmid-half_span*1e-6,minimum_frequency),6)

# frange,power0=bl.Waterfall(fil0,f1,f2).grab_data(f1,f2)
# frange,power1=bl.Waterfall(fil1,f1,f2).grab_data(f1,f2)
# SNR0=mySNR(power0)
# SNR1=mySNR(power1)
# SNR0,SNR1,SNR0/SNR1
SNR0=betterSNR(fil0,f1,f2)
SNR1=betterSNR(fil1,f1,f2)
SNR0,SNR1,SNR0/SNR1
# %%
import matplotlib.pyplot as plt
import numpy as np

# Generate two sample data arrays
x1 = np.random.rand(10, 10)  # First data array
x2 = x1*0.5  # Second data array

# Calculate the minimum and maximum values across both data arrays
global_min = min(x1.min(), x1.min())
global_max = max(x1.max(), x1.max())

# Create a figure with two subplots
fig, ax = plt.subplots(1, 2, figsize=(10, 4))

# Plot the first subplot with the colormap 'viridis' and normalization to the global range
im1 = ax[0].imshow(x1, aspect='auto', origin='lower', cmap='viridis', vmin=global_min, vmax=global_max)
ax[0].set_title('Plot 1')

# Plot the second subplot with the same colormap and normalization as the first subplot
im2 = ax[1].imshow(x2, aspect='auto', origin='lower', cmap='viridis', vmin=global_min, vmax=global_max)
ax[1].set_title('Plot 2')

# Create a colorbar for one of the subplots (they will share the same colormap)
cbar1 = fig.colorbar(im1, ax=ax[0])
cbar1.set_label('Colorbar Label')
cbar2 = fig.colorbar(im2, ax=ax[1])
cbar2.set_label('Colorbar Label')
# Show the plots
plt.show()



# %%
# SHOW MULTIPLE FREQUENCY SPANS DUE TO FSCRUNCH
import blimpy as bl
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use('/home/ntusay/scripts/NbeamAnalysis/plt_format.mplstyle')
plt.rcParams.update({'font.size': 22})
plt.rcParams.update({'ytick.minor.visible': False})
plt.rcParams.update({'axes.labelsize': 18})
plt.rcParams.update({'xtick.labelsize': 14})
plt.rcParams.update({'ytick.labelsize': 14})
%matplotlib inline

csv='/home/ntusay/scripts/TRAPPIST-1/obs_10-29_DOTnbeam.csv'
csv='/home/ntusay/scripts/TRAPPIST-1/obs_11-02_DOTnbeam.csv'

df=pd.read_csv(csv)
# plt.scatter(df.Corrected_Frequency,df.corrs,s=1,color='k')

# # Calculate actual frequency span based on drift rate
# target_fil = df.fil_0000
# fil_meta = [bl.Waterfall(fil,load_data=False) for fil in target_fil]
# obs_length=[meta.n_ints_in_file * meta.header['tsamp'] for meta in fil_meta] # total length of observation in seconds
# DR = df['Drift_Rate']              # reported drift rate
# padding=[1+np.log10(SNR)/10 for SNR in df.SNR]   # padding based on reported strength of signal
# half_span=[max(abs(drift)*obs_length[j]*padding[j],250) for j,drift in enumerate(DR)]
# fmid = df['Corrected_Frequency']*1e6
# f1=fmid-half_span
# f2=fmid+half_span
# f_span=f2-f1

# Just grab reported frequency span from dat files
f_span=(df.freq_start-df.freq_end)*1e6
# %%
fig, ax = plt.subplots(1,1,figsize=(10,6))
plt.scatter(df.Corrected_Frequency,f_span,s=1,color='k')
plt.yscale('log')
plt.ylabel('Frequency Span (Hz)')
plt.xlabel('Frequency (MHz)')
# plt.xlim(4870,4910)
plt.show()
# %%
# Plot Frequency and SNR for each beam to see need for spatial filtering
import DOT_utils as DOT
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use('/home/ntusay/scripts/NbeamAnalysis/plt_format.mplstyle')
plt.rcParams.update({'font.size': 22})
plt.rcParams.update({'ytick.minor.visible': False})
plt.rcParams.update({'axes.labelsize': 18})
plt.rcParams.update({'xtick.labelsize': 14})
plt.rcParams.update({'ytick.labelsize': 14})
%matplotlib inline

fig, ax = plt.subplots(1,1,figsize=(10,6))
datdir='/mnt/datac-netStorage-40G/projects/p004/PPO/2022-11-02-00:38:44'
dat_files,errors=DOT.get_dats(datdir,'0000')
for dat_file in dat_files:
    dat_df0 = pd.read_csv(dat_file, 
                delim_whitespace=True, 
                names=['Top_Hit_#','Drift_Rate','SNR', 'Uncorrected_Frequency','Corrected_Frequency','Index',
                        'freq_start','freq_end','SEFD','SEFD_freq','Coarse_Channel_Number','Full_number_of_hits'],
                skiprows=9)
    dat_df1 = pd.read_csv(dat_file.replace('0000.dat','0001.dat'), 
                delim_whitespace=True, 
                names=['Top_Hit_#','Drift_Rate','SNR', 'Uncorrected_Frequency','Corrected_Frequency','Index',
                        'freq_start','freq_end','SEFD','SEFD_freq','Coarse_Channel_Number','Full_number_of_hits'],
                skiprows=9)
    dx0=dat_df0.Corrected_Frequency
    dy0=(dat_df0.freq_start-dat_df0.freq_end)*1e3
    # dy0=dat_df0.SNR
    dx1=dat_df1.Corrected_Frequency
    dy1=(dat_df1.freq_start-dat_df1.freq_end)*1e3
    # dy1=dat_df1.SNR
    plt.scatter(dx0,dy0,color='g',alpha=0.75,s=20,zorder=-20)
    plt.scatter(dx1,dy1,color='r',alpha=0.25,s=5,marker='x',zorder=20)
plt.scatter(dx0[0],dy0[0],color='g',alpha=0.75,s=20,label='target beam',zorder=-20)
plt.scatter(dx1[0],dy1[0],color='r',alpha=0.25,s=5,marker='x',zorder=20,label='off-target beam')
plt.legend()
plt.ylabel('Frequency Span (kHz)')
# plt.ylabel('SNR')
plt.xlabel('Frequency (MHz)')
plt.yscale('log')
plt.grid(which='both',axis='x',alpha=0.25)
plt.xlim(4860,4920)
# plt.xlim(5075,5125)
plt.title(datdir.split('/')[-1].split(':')[0][:-3])
plt.show()
# %%
import os
import glob
path='/mnt/datac-netStorage-40G/projects/p004/PPO/2022-10-28-00:36:08/'
def add_time(line):
    if 'hour' in line:
        inc='hour'
        return float(line.split(f' {inc}')[0].split(': ')[-1])*3600
    elif 'minute' in line:
        inc='minute'
        return float(line.split(f' {inc}')[0].split(': ')[-1])*60
    elif 'second' in line:
        inc='second'
        return float(line.split(f' {inc}')[0].split(': ')[-1])
    else:
        print('\n\tERROR in getting times\n')
        return 0
secs=0
log_num=0
logs=sorted(glob.glob(path+'fil_*/seti-node*/fil*.log'))
for log in logs:
    lines=open(log,'r').readlines()
    for line in lines:
        if '===== Search time:' in line:
            secs+=add_time(line)
    log_num+=1
print(secs,log_num)
# %%
csv='/home/ntusay/scripts/TRAPPIST-1/obs_10-29_DOTnbeam.csv'
df=pd.read_csv(csv)
# plt.scatter(df.Corrected_Frequency,df.SNR_ratio)
# plt.scatter(df.Corrected_Frequency,df.corrs)
# plt.scatter(df.Corrected_Frequency,df.Drift_Rate)
plt.hist(df.SNR_ratio,bins=40)
plt.yscale('log')
# plt.ylim(-.5,.5)
plt.show()
# %%
