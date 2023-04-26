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
from DOT_utils import check_logs
from DOT_utils import get_dats

def hits(dirs,beam):
    tot=0
    for dir in dirs:
        dat_files,errors=get_dats(dir,beam)
        hits=0
        for dat in dat_files:
            hits+=len(open(dat,'r').readlines())-9
        print(dir, hits)
        tot+=hits
    print(f'{tot} total hits found in all target beam dat files')
    return None

PPO='/mnt/buf0/PPO/'
dirs=sorted(glob.glob(PPO+'*'))
beam='0000'
hits(dirs,beam)
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
        f1=1e12
        f2=0
        fil_files = get_fils(dir,beam)
        label = "-".join(dir.split('/')[-1].split('2022-')[-1].split('-')[0:2])
        for fil in fil_files:
            waterfall_data = bl.Waterfall(fil,load_data=False)
            fch1 = waterfall_data.header['fch1']
            fch2 = fch1 + waterfall_data.header['foff'] * waterfall_data.header['nchans']
            f1=min(min(fch1,fch2),f1)
            f2=max(max(fch1,fch2),f2)
        fmin=min(fmin,f1)
        fmax=max(fmax,f2)
        plt.plot([f1,f2],[d+1,d+1],label=label)
    plt.legend()
    plt.show()
    print(f'Frequency coverage spans {fmin:.6f} to {fmax:.6f} MHz.')
    return None

PPO='/mnt/datac-netStorage-40G/projects/p004/'
dirs=sorted(glob.glob(PPO+'2022*'))
beam='0000'
freq_span(dirs,beam)
# %%
