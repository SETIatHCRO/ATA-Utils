import setigen as stg
import numpy as np
import pandas as pd
import blimpy as bl
import time
import gc
from scipy.stats import truncnorm
import blimpy.waterfall as wf
import blimpy.io.sigproc as sp
import matplotlib.pyplot as plt
from astropy import units as u
from astropy.stats import sigma_clip as sc

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

start=time.time()

csv = '/home/ntusay/scripts/processed/obs_11-01_CCFnbeam.csv'
df=pd.read_csv(csv)

i=24
fil0=df.fil_0000[i]

waterfall_data = bl.Waterfall(fil0,load_data=False)
fch1 = waterfall_data.header['fch1']
fch2 = fch1 + waterfall_data.header['foff'] * waterfall_data.header['nchans']
f1=min(fch1,fch2)+10
f2=max(fch1,fch2)-70

'''
Note: The injection test filterbank file comes from this filepath:
/mnt/datac-netStorage-40G/projects/p004/2022-11-01-04:44:33/fil_59884_17225_248799804_trappist1_0001/seti-node4.1/fil_59884_17225_248799804_trappist1_0001-beam0000.fil
# '''

# ### Signal 1
# '''The first signal is a very strong attenuated signal in both beams added to a 
#     blank slice where no other signals are present, only noise.'''

# fil0 = '/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/fil_59884_17225_248799804_trappist1_0001-beam0000.fil'
# frame0 = stg.Frame(fil0, f_start=f1, f_stop=f2)
# end, time_label = get_elapsed_time(start)
# print(f'\nFull filterbank file loaded in %.2f {time_label}.\n' %end)

# mid=time.time()

# # # df.freq_start[0],df.freq_end[0] = 6856.000266, 6855.999763

# f2 = df.freq_start[i]-500/1e6
# f1 = df.freq_end[i]-500/1e6
# signal1 = frame0.add_signal(stg.constant_path(f_start=f1*u.MHz+220*u.Hz,drift_rate=0.07*u.Hz/u.s),
#                           stg.constant_t_profile(level=frame0.get_intensity(snr=45000)),
#                           stg.gaussian_f_profile(width=2*u.Hz),
#                           stg.constant_bp_profile(level=1))

# end, time_label = get_elapsed_time(mid)
# print(f'\n\tSignal1 added to filterbank file loaded in %.2f {time_label}.\n' %end)

# frame0.save_fil(f"/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/{fil0.split('/')[-1]}")
# end, time_label = get_elapsed_time(start)
# print(f'\n\t\t*** First part of program complete in %.2f {time_label}.\n' %end)

# del frame0, signal1
# gc.collect()

# mid=time.time()
# fil1 = '/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/fil_59884_17225_248799804_trappist1_0001-beam0001.fil'
# f1=min(fch1,fch2)+10
# f2=max(fch1,fch2)-70
# frame1 = stg.Frame(fil1, f_start=f1, f_stop=f2)
# end, time_label = get_elapsed_time(mid)
# print(f'\nFull filterbank file loaded in %.2f {time_label}.\n' %end)


# # # df.freq_start[0],df.freq_end[0] = 6856.000266, 6855.999763

# f2 = df.freq_start[i]-500/1e6
# f1 = df.freq_end[i]-500/1e6
# signal2 = frame1.add_signal(stg.constant_path(f_start=f1*u.MHz+220*u.Hz,drift_rate=0.07*u.Hz/u.s),
#                           stg.constant_t_profile(level=frame1.get_intensity(snr=10000)),
#                           stg.gaussian_f_profile(width=2*u.Hz),
#                           stg.constant_bp_profile(level=1))

# end, time_label = get_elapsed_time(end)
# print(f'\n\tSignal1 added to filterbank file loaded in %.2f {time_label}.\n' %end)

# frame1.save_fil(f"/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/{fil1.split('/')[-1]}")
# end, time_label = get_elapsed_time(start)
# print(f'\n\t\t*** Final Program complete in %.2f total {time_label}.\n' %end)

### Signal 2
'''The second signal is a very weak attenuated signal added to a separate
    blank slice where no other signals are present, only noise.'''

fil0 = '/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/fil_59884_17225_248799804_trappist1_0001-beam0000.h5'
frame0 = stg.Frame(fil0, f_start=f1, f_stop=f2)
end, time_label = get_elapsed_time(start)
print(f'\nFull filterbank file loaded in %.2f {time_label}.\n' %end)

mid=time.time()

f2 = df.freq_start[i]-500000/1e6
f1 = df.freq_end[i]-500000/1e6
signal1 = frame0.add_signal(stg.constant_path(f_start=f1*u.MHz+220*u.Hz,drift_rate=0.07*u.Hz/u.s),
                          stg.constant_t_profile(level=frame0.get_intensity(snr=450)),
                          stg.gaussian_f_profile(width=2*u.Hz),
                          stg.constant_bp_profile(level=1))

end, time_label = get_elapsed_time(mid)
print(f'\n\tSignal1 added to filterbank file loaded in %.2f {time_label}.\n' %end)

frame0.save_fil(f"/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/{fil0.split('/')[-1]}")
end, time_label = get_elapsed_time(start)
print(f'\n\t\t*** First part of program complete in %.2f {time_label}.\n' %end)

del frame0, signal1
gc.collect()

    # beam 0001
mid=time.time()
fil1 = '/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/fil_59884_17225_248799804_trappist1_0001-beam0001.h5'
f1=min(fch1,fch2)+10
f2=max(fch1,fch2)-70
frame1 = stg.Frame(fil1, f_start=f1, f_stop=f2)
end, time_label = get_elapsed_time(mid)
print(f'\nFull filterbank file loaded in %.2f {time_label}.\n' %end)


f2 = df.freq_start[i]-500000/1e6
f1 = df.freq_end[i]-500000/1e6
signal2 = frame1.add_signal(stg.constant_path(f_start=f1*u.MHz+220*u.Hz,drift_rate=0.07*u.Hz/u.s),
                          stg.constant_t_profile(level=frame1.get_intensity(snr=100)),
                          stg.gaussian_f_profile(width=2*u.Hz),
                          stg.constant_bp_profile(level=1))

end, time_label = get_elapsed_time(end)
print(f'\n\tSignal1 added to filterbank file loaded in %.2f {time_label}.\n' %end)

frame1.save_fil(f"/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/{fil1.split('/')[-1]}")
end, time_label = get_elapsed_time(start)
print(f'\n\t\t*** Final Program complete in %.2f total {time_label}.\n' %end)