from ata_snap import ata_rfsoc_fengine
import struct
import matplotlib.pyplot as plt
import numpy as np
import time


fpg_file = '/home/obsuser/src/ata_snap_rfsoc/ata_rfsoc/zrf_spec_4ant/outputs/zrf_spec_4ant_2021-06-05_1337.fpg'

r = ata_rfsoc_fengine.AtaRfsocFengine('rfsoc1-ctrl-1')
r.fpga.get_system_information(fpg_file)

i_j_pairs = [[0,1], [2,3], [4,5], [6,7], [8,9], [10,11], [12,13], [14,15]]

ii = 0
for i,j in i_j_pairs:
    r.fpga.write_int('sel0', i)
    r.fpga.write_int('sel1', j)
    raw_x, t = r.fpga.snapshots.ss_adc0.read_raw(man_trig=True, man_valid=True)
    raw_y, t = r.fpga.snapshots.ss_adc1.read_raw(man_trig=True, man_valid=True)
    data_x = struct.unpack(">%dh" % (raw_x['length']//2), raw_x['data'])
    data_y = struct.unpack(">%dh" % (raw_y['length']//2), raw_y['data'])
    print(np.std(data_x))
    print(np.std(data_y))
    plt.figure(i)
    plt.title("%i %i" %(i,j))
    plt.hist(data_x)
    plt.hist(data_y)

plt.show()
