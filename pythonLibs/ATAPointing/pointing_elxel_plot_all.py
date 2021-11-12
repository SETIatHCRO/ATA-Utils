import numpy as np
import pandas as pd
from scipy import stats
import sys,os
import matplotlib.pyplot as plt

import argparse

#YLIM1, YLIM2 = -3600, 3600
#YLIM1, YLIM2 = -600, 600
YLIM=600
PLOT_BASEDIR="./"
FMT="png"


def main():
    parser = argparse.ArgumentParser(
            description='Plot el/xel offsets using .tpoint files')
    parser.add_argument('in_files', nargs = '+', type=str,
            help = 'Input .tpoint files')
    parser.add_argument('-l', dest='plot_lim', type=float,
            default=YLIM, required=False, 
            help = 'Plot limit for offsets in arcsec [default=%i]' %YLIM)
    parser.add_argument('-d', dest='plot_basedir', type=str,
            default=PLOT_BASEDIR, required=False,
            help = 'Base directory for output plots [default=%s]'%PLOT_BASEDIR)
    parser.add_argument('-s', '--save_plot', dest='save_plot', 
            action='store_true',
            help = 'Save plots rather than display to screen')
    parser.add_argument('-f', dest='plot_format', type=str,
            default=FMT, required=False,
            help = 'Image format for output plots [default=%s]' %FMT)

    args = parser.parse_args()

    YLIM1, YLIM2 = -args.plot_lim, args.plot_lim
    plot_basedir = args.plot_basedir
    
    plot_format = args.plot_format

    listr = []

    lista = []


    for i, filename in enumerate(args.in_files):
        lista.append((filename))

        with open(filename) as f:
            lines1 = f.readlines()[25:]

            eloff =[]
            azoff = []
            el_com = []
            az_com = []

            for x in lines1:
                eloff.append(x.split(',')[6])

            pd.__version__

            for y in lines1:
                g = np.array(y.split(','))
                #print(g)
                df = pd.DataFrame(g).T
                #print(df[5])
                df[5] = df[5].str.split(r'!').str.get(1)
                #print(df[5])
                azoff.append(df[5])
                #print(df)


            for z in lines1:
                el_com.append(z.split(',')[1])

            for p in lines1:
                az_com.append(p.split(',')[0])

            f.close()


        rese  = np.array(eloff).astype(np.float64).squeeze()
        resa  = np.array(azoff).astype(np.float64).squeeze()
        elcom = np.array(el_com).astype(np.float64).squeeze()
        azcom = np.array(az_com).astype(np.float64).squeeze()

        resx = resa*np.cos(np.radians(elcom))

        xcom = azcom*np.cos(np.radians(elcom))

        #converting offsets to arcsec
        rese = rese*3600
        resx = resx*3600

        fig, axs = plt.subplots(2, 2)
        #fig.suptitle("Antenna" + str(filename[22:24]))
        
        fig.suptitle(filename)
        
        axs[0, 0].scatter(elcom, rese, s=4, color='blue')
        #axs[0, 0].set_xlabel('el (degrees)')
        axs[0, 0].set_ylabel('el_off (")')
        axs[0, 0].set_ylim(YLIM1, YLIM2)
        axs[0, 0].grid(which='major')
        axs[0, 0].grid(which='minor', linestyle=':', linewidth=0.5)
        axs[0, 0].minorticks_on()
        axs[0, 0].axhline(y=0, color='black', linestyle='-')
        #axs[0, 0].set_title('el_off vs el')
        
        axs[1, 0].scatter(elcom, resx, s=4, color='red')
        axs[1, 0].set_xlabel('el (deg)')
        axs[1, 0].set_ylabel('xel_off (")')
        axs[1, 0].set_ylim(YLIM1, YLIM2)
        axs[1, 0].grid(which='major')
        axs[1, 0].grid(which='minor', linestyle=':', linewidth=0.5)
        axs[1, 0].minorticks_on()
        axs[1, 0].axhline(y=0, color='black', linestyle='-')
        #axs[1, 0].set_title('xel_off vs el')
        
        axs[0, 1].scatter(xcom, rese, s=4, color='green')
        #axs[0, 1].set_xlabel('xel (degrees)')
        #axs[0, 1].set_ylabel('el_off (arcsec)')
        axs[0, 1].set_ylim(YLIM1, YLIM2)
        axs[0, 1].grid(which='major')
        axs[0, 1].grid(which='minor', linestyle=':', linewidth=0.5)
        axs[0, 1].minorticks_on()
        axs[0, 1].axhline(y=0, color='black', linestyle='-')
        #axs[0, 1].set_title('el_off vs xel')


        axs[1, 1].scatter(xcom, resx, s=4, color='orange')
        #axs[1, 1].set_title('xel_off vs xel')
        axs[1, 1].set_xlabel('xel (deg)')
        #axs[1, 1].set_ylabel('xel_off (arcsec)')
        axs[1, 1].set_ylim(YLIM1, YLIM2)
        axs[1, 1].grid(which='major')
        axs[1, 1].grid(which='minor', linestyle=':', linewidth=0.5)
        axs[1, 1].minorticks_on()
        axs[1, 1].axhline(y=0, color='black', linestyle='-')

        if args.save_plot:
            pname = os.path.splitext(filename)[0]+'.'+args.plot_format #plot_name
            pname = os.path.join(plot_basedir, pname)
            plt.savefig(pname, format=plot_format, bbox_inches='tight')

    if not args.save_plot:
        plt.show()


if __name__ == "__main__":
    main()
