from ata_snap import ata_rfsoc_fengine
import matplotlib.pyplot as plt
import numpy as np
import time


fpg_file = '/home/obsuser/src/ata_snap_rfsoc/ata_rfsoc/zrf_spec_4ant/outputs/zrf_spec_4ant_2021-06-05_1337.fpg'

r = ata_rfsoc_fengine.AtaRfsocFengine('rfsoc1-10')
r.fpga.get_system_information(fpg_file)

xx = []
yy = []
for i in range(20):
    x,y = r.adc_get_samples()
    xx.append(x)
    yy.append(y)
    time.sleep(0.5)

xx = np.array(xx).flatten()
yy = np.array(yy).flatten()

plt.hist(xx, bins=2**14, label='X-pol')
plt.hist(yy, bins=2**14, label='Y-pol')
plt.xlabel("ADC values")
plt.ylabel("N datapoints")
plt.legend()


xx, yy = r.spec_read()
plt.figure()
plt.semilogy(xx, label='x')
plt.semilogy(yy,label='y');
plt.legend()

plt.show()
