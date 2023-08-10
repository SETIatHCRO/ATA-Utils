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
freq_span(dirs,beam,save=True)

# %%
import pandas as pd
import numpy as np
import blimpy as bl

def median_noise(s1,p=5):
    return np.median(s1[(s1>np.percentile(s1,p))&(s1<np.percentile(s1,100-p))])

def noise_std(s1,p=5):
    return np.std(s1[(s1>np.percentile(s1,p))&(s1<np.percentile(s1,100-p))])

def SNR_ratio(s0,s1):
    return s0.max()/median_noise(s0)/(s1.max()/median_noise(s1))

def SNR_ratio2(s0,s1):
    return (s0.max()-median_noise(s0))/noise_std(s0)/(((s1.max()-median_noise(s1)))/noise_std(s1))

def get_df(dat_file):
    df = pd.read_csv(dat_file,delim_whitespace=True,
                    names=['Top_Hit_#','Drift_Rate','SNR', 'Uncorrected_Frequency','Corrected_Frequency','Index',
                    'freq_start','freq_end','SEFD','SEFD_freq','Coarse_Channel_Number','Full_number_of_hits'],skiprows=9)
    return df

def wf_data(fil,f1,f2):
    return bl.Waterfall(fil,f1,f2).grab_data(f1,f2)

def ACF(s1):
    return ((s1*s1).sum(axis=1)).sum()/np.shape(s1)[0]/np.shape(s1)[1]

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
    SNRr3=row['SNR_ratio']
    x=row['x']
    print(f"{r} SNR: {SNR:.2f}\tFreq: {cf}  SNRr: {SNRr2:.3f}  SNR0: {SNR0:.2f}\tSNR1: {SNR1:.2f}  new_x2: {x/SNRr2:.3f}")
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
csv='/home/ntusay/scripts/parallel_test/obs_11-09_DOTnbeam.csv'
df=pd.read_csv(csv)
fig,ax=plt.subplots(figsize=(12,10))
plt.scatter(df.corrs,df.SNR_ratio,color='orange',alpha=0.5,edgecolor='k')
sf=4
plt.xlabel('Average X Scores')
plt.ylabel('SNR ratio')
ylims=plt.gca().get_ylim()
plt.axhspan(sf,ylims[1],color='green',alpha=0.25,label='Attenuated Signals')
plt.axhspan(1/sf,sf,color='grey',alpha=0.25,label='Similar SNRs')
plt.axhspan(ylims[0],1/sf,color='brown',alpha=0.25,label='Off-beam Attenuated')
plt.ylim(ylims[0],ylims[1])
# plt.hlines(4.5,0,1,color='k',linestyle='--')
# plt.hlines(1,0,1,color='k',linestyle='--')
plt.xlim(-0.01,1.01)
plt.legend().get_frame().set_alpha(0) 
plt.grid(which='major', axis='both', alpha=0.5,linestyle=':')
print(len(df[df.SNR_ratio>4.5]))
plt.show()
# %%
sf=4.5
plt.scatter(df.x,df.SNR_ratio,color='orange',alpha=0.5,edgecolor='k')
plt.hlines(sf,0,1,color='k',linestyle='--')
plt.hlines(1/sf,0,1,color='k',linestyle='--')
# plt.yscale('log')
plt.show()
# %%
