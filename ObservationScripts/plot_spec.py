from ata_snap import ata_snap_fengine, ata_rfsoc_fengine
import numpy as np
import matplotlib.pyplot as plt

fpg_file = "/home/obsuser/src/ata_snap_rfsoc/ata_rfsoc/zrf_spec_4ant/outputs/zrf_spec_4ant_2021-06-14_1301.fpg"

rfsoc = ata_rfsoc_fengine.AtaRfsocFengine("rfsoc1-ctrl-1", pipeline_id=0)
rfsoc.fpga.get_system_information(fpg_file)
spec_x, spec_y = rfsoc.spec_read()
plt.plot(10*np.log10(spec_x), label="X-Pid0")
plt.plot(10*np.log10(spec_y), label="Y-Pid0")

rfsoc = ata_rfsoc_fengine.AtaRfsocFengine("rfsoc1-ctrl-2", pipeline_id=1)
rfsoc.fpga.get_system_information(fpg_file)
spec_x, spec_y = rfsoc.spec_read()
plt.plot(10*np.log10(spec_x), label="X-Pid1")
plt.plot(10*np.log10(spec_y), label="Y-Pid1")

rfsoc = ata_rfsoc_fengine.AtaRfsocFengine("rfsoc1-ctrl-3", pipeline_id=2)
rfsoc.fpga.get_system_information(fpg_file)
spec_x, spec_y = rfsoc.spec_read()
plt.plot(10*np.log10(spec_x), label="X-Pid2")
plt.plot(10*np.log10(spec_y), label="Y-Pid2")

rfsoc = ata_rfsoc_fengine.AtaRfsocFengine("rfsoc1-ctrl-4", pipeline_id=3)
rfsoc.fpga.get_system_information(fpg_file)
spec_x, spec_y = rfsoc.spec_read()
plt.plot(10*np.log10(spec_x), label="X-Pid3")
plt.plot(10*np.log10(spec_y), label="Y-Pid3")

plt.legend()
plt.show()
