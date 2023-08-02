# The purpose of this program is to inject a bunch of signals 
# into a relatively quiet .fil file, at many different SNRs, 
# in order to test signal recovery over the band at various SNRs.

import setigen as stg
import blimpy as bl
import time
from astropy import units as u

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

# fil file taken from:
# '/mnt/datac-netStorage-40G/projects/p004/2022-11-01-04:44:33/fil_59884_17225_248799804_trappist1_0001/seti-node4.1/fil_59884_17225_248799804_trappist1_0001-beam0000.fil'
fil = '/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/fil_59884_17225_248799804_trappist1_0001-beam0000.fil'
waterfall_data = bl.Waterfall(fil,load_data=False)
fch1 = waterfall_data.header['fch1']
fch2 = fch1 + waterfall_data.header['foff'] * waterfall_data.header['nchans']
f1=min(fch1,fch2)
f2=max(fch1,fch2)

num_injections=100
fcs=[]
for i in range(num_injections):
    fstep=(f2-f1)/(num_injections+1)
    fcs.append(f1+fstep*(i+1))

print(f'Loading filterbank file into setigen frame...')
# Load the full filterbank file as frame0
frame0 = stg.Frame(fil, f_start=f1, f_stop=f2)
end, time_label = get_elapsed_time(start)
print(f'\nFull filterbank file loaded in %.2f {time_label}.\n' %end)

for f,fc in enumerate(fcs[:-1]):
    frame0.add_signal(stg.constant_path(f_start=fc*u.MHz,drift_rate=0.07*u.Hz/u.s),
                    stg.constant_t_profile(level=frame0.get_intensity(snr=1+f**2)),
                    stg.gaussian_f_profile(width=2*u.Hz),
                    stg.constant_bp_profile(level=1))

end, time_label = get_elapsed_time(mid)
print(f'\n\tSignals injected into filterbank file in %.2f {time_label}.\n' %end)

frame0.save_fil(f"/home/ntusay/scripts/NbeamAnalysis/injection_SNR_test/{fil.split('/')[-1]}")
end, time_label = get_elapsed_time(start)
print(f'\n\t\t*** Program complete in %.2f {time_label}.\n' %end)