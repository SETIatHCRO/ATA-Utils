from SNAPobs import snap_if


#print(snap_if.getatten(["2e", "3l", "1a"]))
snap_if.setatten({"2mx":26, "2my":26})
print(snap_if.getatten(["2m"]))


fpg_file = '/home/obsuser/src/ata_snap_rfsoc/ata_rfsoc/zrf_spec_4ant/outputs/zrf_spec_4ant_2021-06-05_1337.fpg'

rs = [ata_rfsoc_fengine.AtaRfsocFengine('rfsoc1-ctrl-%i' %(i+1), pipeline_id=i) for i in [0,1,2,3]]

for r in rs:
    r.fpga.get_system_information(fpg_file)


ii = 0
for r in rs:
    print(r)
    xx, yy = r.spec_read()
    print("spectrum read")

    plt.figure(ii)
    plt.title("Pipeline ID: %i" %ii)
    plt.semilogy(xx, label='x')
    plt.semilogy(yy, label='y')
    plt.legend()
    ii+=1
    break

print("Done")

plt.show()
