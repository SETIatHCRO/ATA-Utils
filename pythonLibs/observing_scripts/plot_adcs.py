import struct
import numpy as np
import matplotlib.pyplot as plt

import adc5g
import casperfpga
import sys,os

FPGA_FILE = "/home/sonata/ata_snap/snap_adc5g_spec_rpi/outputs/snap_adc5g_spec_rpi_2020-05-25_0811.fpg"
#FPGA_FILE = '/home/sonata/ATA/FPGAfirmware/snap_adc5g_spec_2018-07-07_1844.fpg'


snap_name = sys.argv[1]

snap = casperfpga.CasperFpga(snap_name, transport=casperfpga.KatcpTransport)
#snap = casperfpga.CasperFpga(snap_name)

snap.get_system_information(FPGA_FILE)
snap.write_int('vacc_ss_sel', 0)

#fig, axs = plt.subplots(2,1, figsize=(12,9))

plt.figure()
while True:
    #fig.clf()
    plt.clf()
    all_chan_data = adc5g.get_snapshot(snap, 'ss_adc')
    chanx = all_chan_data[0::2]#[0::2]
    chany = all_chan_data[1::2]#[0::2]
    print ("RMSx: %.2f, RMSy: %.2f" %(np.std(chanx), np.std(chany)))
    chanx_c = np.array(chanx, dtype=float).view("complex128")
    chany_c = np.array(chany, dtype=float).view("complex128")

    freq_x = np.abs(np.fft.fft(chanx_c))
    freq_y = np.abs(np.fft.fft(chany_c))

    #axs[0].hist(chanx, bins=50, label="X")
    #axs[0].hist(chany, bins=50, label="Y")

    #axs[1].plot(10*np.log10(freq_x), label="XX")
    #axs[1].plot(10*np.log10(freq_y), label="YY")

#    plt.hist(chanx, bins=50, label="X")
#    plt.hist(chany, bins=50, label="Y")

    plt.plot(10*np.log10(freq_x), label="XX")
    plt.plot(10*np.log10(freq_y), label="YY")


    #fig.legend()
    plt.legend()
    plt.pause(2)
