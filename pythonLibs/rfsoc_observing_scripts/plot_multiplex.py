from ata_snap import ata_rfsoc_fengine
import matplotlib.pyplot as plt
import numpy as np
import time


#fpg_file = '/home/obsuser/src/ata_snap_rfsoc/ata_rfsoc/zrf_spec/outputs/zrf_spec_2021-04-27_1557.fpg'
fpg_file = '/home/obsuser/src/ata_snap_rfsoc/ata_rfsoc/zrf_spec_4ant/outputs/zrf_spec_4ant_2021-06-05_1337.fpg'

r = ata_rfsoc_fengine.AtaRfsocFengine('rfsoc1-10')
r.fpga.get_system_information(fpg_file)


ii = 1
for i,j in [[0,1], [2,3], [4,5], [6,7], [8,9], [10,11], [12,13], [14,15]]:
    print(i, j)
    r.fpga.write_int('sel0', i)
    r.fpga.write_int('sel1', j)


    xx, yy = r.spec_read()
    time.sleep(1)
    xx, yy = r.spec_read()

    plt.figure(ii)
    plt.title("In: %i %i" %(i,j))
    plt.semilogy(xx, label='x')
    plt.semilogy(yy, label='y');
    plt.legend()
    ii+=1

plt.show()
