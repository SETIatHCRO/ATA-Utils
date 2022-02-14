from SNAPobs import snap_if
from ata_snap import ata_rfsoc_fengine
import matplotlib.pyplot as plt

#print(snap_if.getatten(["2e", "3l", "1a"]))
snap_if.setatten({"2mx":26, "2my":26})
print(snap_if.getatten(["2m"]))

fpg_file = '/home/obsuser/src/ata_snap_rfsoc/ata_rfsoc/zrf_spec_4ant/outputs/zrf_spec_4ant_2021-06-05_1337.fpg'

r = ata_rfsoc_fengine.AtaRfsocFengine('rfsoc1-ctrl-1', pipeline_id=0)
r.fpga.get_system_information(fpg_file)


xx, yy = r.spec_read()
plt.figure()
plt.semilogy(xx, label='x')
plt.semilogy(yy, label='y')
plt.legend()


snap_if.setatten({"2mx":16, "2my":16})
print(snap_if.getatten(["2m"]))

xx, yy = r.spec_read()
plt.semilogy(xx, label='x')
plt.semilogy(yy, label='y')
plt.legend()


snap_if.setatten({"2mx":6, "2my":6})
print(snap_if.getatten(["2m"]))

xx, yy = r.spec_read()
plt.semilogy(xx, label='x')
plt.semilogy(yy, label='y')
plt.legend()

print("Done")

plt.show()
