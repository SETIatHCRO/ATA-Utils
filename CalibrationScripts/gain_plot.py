#!/home/sonata/src/casa-6.4.0-16/bin/python3
from casatools import table
import matplotlib.pyplot as plt
import numpy as np
import toml
import argparse
import sys

"""
Script assumes 'telinfo_ata.toml' and 'obsinfo.toml' exist
"""

# Make better plots
exec(open("/home/sonata/utils/rcparams.py", "r").read())

def SEFD2Tsys(SEFD, k_per_jy = 130):
    return SEFD / k_per_jy

def Tsys2SEFD(Tsys, k_per_jy = 130):
    return Tsys * k_per_jy

SEFD_YLIM = 40000

def main():
    parser = argparse.ArgumentParser(
            description="Plots SEFDs/Tsys and beamformer weights")

    parser.add_argument(dest='calg', type=str,
            help="Name of the cal.g file produced by CASA's gaincal")
    parser.add_argument('--flux', dest='flux', type=float,
            help="Flux density in Jy of source [default: 0]", default=0)
    parser.add_argument('--freq', dest='freq', type=float,
            help="Center frequency in GHz [default: 0]", default=0)
    parser.add_argument('--lo', dest='lo', type=str,
            help="LO that was used [default: b]", default='b')
    parser.add_argument('--telinfo', dest='telinfo', type=str,
            help="telinfo toml file [default: ./telinfo_ata.toml]",
            default='./telinfo_ata.toml')
    parser.add_argument('--obsinfo', dest='obsinfo', type=str,
            help="obsinfo.toml file [default: ./obsinfo.toml]",
            default='./obsinfo.toml')
    parser.add_argument('--wout', dest='weight_file', type=str,
            help="output weights file [default: ./weights.txt]",
            default='./weights.txt')

    args = parser.parse_args()

    # Read all telescope information
    # Needed because ATA .ms metadata "sees" 42 antennas
    # But only 20 are used in observation
    tel_info = toml.load(args.telinfo)


    # Grab all antenna polarizations
    full_antpols = []
    full_antpols += ["0ax", "0ay"] #Not sure yet why this is needed...
    for antinfo in tel_info['antennas']:
        antname = antinfo['name']
        full_antpols += [antname+'x']
        full_antpols += [antname+'y']


    # Now grab the antennas used in this observation
    obsinfo = toml.load(args.obsinfo)
    antpols = [i+j for i,j in obsinfo['input_map']] # For this observation

    valid_idx = []
    for antpol in antpols:
        valid_idx += [full_antpols.index(antpol)]


    # Read gain table
    calG = table()
    calG.open(args.calg)

    g = np.abs(calG.getcol("CPARAM")).squeeze()
    g = g**2 # !!! IMPORTANT !!! g has already been squared!!
    g = g.T.flatten() #gain values are antpol now

    # Now only select the gain values for valid antennas
    g = g[valid_idx]

    tmp = g.reshape(-1, 2) # back to shape=(ant, pol)
    g_norm = tmp / np.max(tmp, axis=0) # I need to normalize wrt each polarization
    g_norm = g_norm.flatten() # back to antpol


    # Now let's compute some relevant quantities
    beamweights = g_norm


    # Let's start plotting
    #
    # beamweights
    plt.figure(figsize=(15,10))
    plt.plot(antpols, beamweights, "x")
    plt.xticks(rotation=45)
    plt.grid(b=True, which='major', color='black', alpha=0.3, linestyle='--')
    plt.ylabel("Antenna weights")
    plt.xlabel("Ant-pols")
    plt.savefig("beamweights_LO" + args.lo + ".png")

    # Save the weights in a weights.txt file
    weight_antpol = np.array([antpols, beamweights]).T
    np.savetxt(args.weight_file,  weight_antpol, fmt="%s")

    # SEFDs next!
    if args.flux == 0:
        print("GAIN CALIBRATION ONLY - EXITING")
        sys.exit(0)


    sefds = ((1 / g) * args.flux)

    # SEFD/Tsys plot
    fig, ax = plt.subplots(figsize=(15,10))

    ax.plot(antpols, sefds, "x")
    ax.set_xlabel("Ant-pols")
    ax.set_ylabel("SEFD [Jy]")
    ax.tick_params(axis='x', rotation=45)
    ax.grid(b=True, which='major', color='black', alpha=0.3, linestyle='--')
    title = "Frequency: %.06f [GHz], LO: %s" %(args.freq, args.lo)
    ax.set_title(title)

    ax.set_ylim(0, SEFD_YLIM)
    # Put a symbol for "antpol out of range"
    for i in range(0, len(antpols)):
        if sefds[i] > SEFD_YLIM:
            ax.plot(antpols[i], SEFD_YLIM * 0.97, marker = '^', color='red')

    #Plotting Tsys - assuming 130.0 as constant K/JY value
    secax = ax.secondary_yaxis('right', functions=(SEFD2Tsys, Tsys2SEFD))
    secax.set_ylabel('Tsys [K]')

    plt.savefig("sefd_tsys_LO" + args.lo + ".png")


if __name__ == "__main__":
    main()
