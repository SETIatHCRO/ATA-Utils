from ata_snap import ata_rfsoc_fengine
import matplotlib.pyplot as plt
import numpy as np
import time


#fpg_file = '/home/obsuser/src/ata_snap_rfsoc/ata_rfsoc/zrf_spec/outputs/zrf_spec_2021-04-27_1557.fpg'
fpg_file = '/home/obsuser/src/ata_snap_rfsoc/ata_rfsoc/zrf_spec_4ant/outputs/zrf_spec_4ant_2021-06-05_1337.fpg'

rs = [ata_rfsoc_fengine.AtaRfsocFengine('rfsoc1-ctrl-%i' %(i+1), pipeline_id=i) for i in [0,1,2,3]]

for r in rs:
    r.fpga.get_system_information(fpg_file)


ii = 0
for r in rs:
    print(r)
    xx, yy = r.spec_read()
    x,y = r.adc_get_samples()
    x = np.array(x)
    y = np.array(y)
    print("spectrum read")
    print("x: %.2f, y: %.2f" %(x.std(),y.std()))

    plt.figure(ii)
    plt.title("Pipeline ID: %i" %ii)
    plt.semilogy(xx, label='x')
    plt.semilogy(yy, label='y')
    plt.legend()
    ii+=1

print("Done")

plt.show()
