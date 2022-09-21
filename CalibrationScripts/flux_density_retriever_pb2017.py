from argparse import ArgumentParser
import pandas as pd
import numpy as np

# Of the 20 flux calibrator sources measured in Perley and Butler (2017)
# The following sources are observable by the ATA and in the source catalog:
# - 3C48
# - 3C123
# - 3C138
# - 3C147
# - 3C196
# - 3C286
# - 3C295
# - 3C353
# - 3C380
# - CasA
#
# The following sources are NOT in the source catalog:
# (need to check the Decs to see if they should be added)
# - J0133–3629
# - Fornax_A
# - J0444-2809
# - Taurus_A
# - Pictor_A
# - Hydra_A
# - Virgo_A
# - Cygnus_A
# - 3C444

# Flux models can be found here:
# https://iopscience.iop.org/article/10.3847/1538-4365/aa6df9
# Also check VLA's flux density page:
# https://science.nrao.edu/facilities/vla/docs/manuals/oss/performance/fdscale

calibrator_df = pd.read_csv("/home/ssheikh/Observing_Tools/perley_and_butler_2017_coeffs.txt", delim_whitespace=True, index_col=False)

def get_flux(source, center_freq, verbose):
    if verbose == True:
        print(source)

    if source == "3C84" and verbose == True:
        print("Sorry, 3C84 is only a gain calibrator, not a flux calibrator. Can't do that one")
        return

    coeff_row = calibrator_df[calibrator_df["Source"] == source]
    if coeff_row.empty == True:
        if verbose == True:
            print("Source not in database")
        print(0)
        return(0)

    flux = 10**(coeff_row["a_0"] + \
                coeff_row["a_1"] * np.log10(center_freq) + \
                coeff_row["a_2"] * np.log10(center_freq)**2 + \
                coeff_row["a_3"] * np.log10(center_freq)**3 + \
                coeff_row["a_4"] * np.log10(center_freq)**4 + \
                coeff_row["a_5"] * np.log10(center_freq)**5)


    if (coeff_row["low_freq_ghz"].values)[0] > center_freq or (coeff_row["high_freq_ghz"].values)[0] < center_freq:
        if verbose == True:
            print("Careful! This source's coefficients are not valid at these frequencies!")

    if (coeff_row["chi_2"].values)[0] > 15:
        if verbose == True:
            print("Careful! This source is not recommended for use by Perley and Butler (2017)")

    if verbose == True:
        print("The expected spectral flux density at this frequency (" + str(center_freq) + "GHz) is:", (flux.values)[0], " Jy")

    flux = (flux.values)[0]
    print(flux)
    return(flux)

def cmd_tool(args=None):
    r"""  Command line utility for fetching a reference flux density to be used with the gain calibration plotting tool (plot_sefds.py)
    """
    p = ArgumentParser()

    p.add_argument('source', type=str, help='Name of calibrator source to use (see comments in source code for acceptable strings)')
    p.add_argument('center_freq', type=float, help='Center frequency, in MHz, assigned to LOb')
    p.add_argument('-v', '--verbose', action='store_true', help='Add -v if you want e.g., warnings about freq ranges')

    if args is None:
        args = p.parse_args()
    else:
        args = p.parse_args(args)

    flux = get_flux(args.source,
             args.center_freq,
             args.verbose
             )
    return(flux)

if __name__ == "__main__":
    cmd_tool()
