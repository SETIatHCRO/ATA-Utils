from ata_snap import ata_snap_fengine
import casperfpga

n = [1,2,3,4,6,8,9,10,11,12]
n = [5,7]
hosts = ['frb-snap%i-pi' %i for i in n]
fengs = [ata_snap_fengine.AtaSnapFengine(host, 
    transport=casperfpga.KatcpTransport) 
        for host in hosts]

for feng in fengs:
    feng.fpga.get_system_information("/home/obsuser/src/ata_snap/snap_adc5g_feng_rpi/outputs/snap_adc5g_feng_rpi_2020-10-29_1727.fpg")
    feng.fpga.write_int('sync_sel', 1)
