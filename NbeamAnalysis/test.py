# %%
import pandas as pd
import os
import glob
from CCF_utils import check_logs
from CCF_utils import get_dats

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
from CCF_utils import check_logs
from CCF_utils import get_dats

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
