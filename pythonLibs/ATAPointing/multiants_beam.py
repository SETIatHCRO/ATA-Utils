import matplotlib.pyplot as plt
import numpy as np
import sys
import glob

from sigpyproc.Readers import FilReader

import argparse

PLOT_BASEDIR="./"
FMT="png"

obsdir = "/mnt/datax-netStorage-40G/raster_obs/nov10_1k/2021-11*"

NRANGE = 3

STEP =  0.5

PLOT_BASEDIR="../"+obsdir

ant_list = ['2eB', '2jB', '2kB', '2mB', '3dB' ]

def main():
    parser = argparse.ArgumentParser(
            description='Raster Scan plot for multiple antennas')
#    parser.add_argument('in_files', nargs = '+', type=str,
#            help = 'Input  files')
    parser.add_argument('-d', dest='plot_basedir', type=str,
            default=PLOT_BASEDIR, required=False,
            help = 'Base directory for output plots [default=%s]'%PLOT_BASEDIR)
    parser.add_argument('-s', '--save_plot', dest='save_plot',
            action='store_true',
            help = 'Save plots rather than display to screen')
    parser.add_argument('-f', dest='plot_format', type=str,
            default=FMT, required=False,
            help = 'Image format for output plots [default=%s]' %FMT)

    parser.add_argument('-n', dest='n_pts', type=float,
            default=NRANGE, required=False,
            help = 'Range of the raster scan (degrees) [default=%i]' %NRANGE)
    parser.add_argument('-p', dest='step_size', type=float,
            default=STEP, required=False,
            help = 'Step size for each increment [default=%i]' %STEP)
    args = parser.parse_args()

    plot_basedir = args.plot_basedir

    plot_format = args.plot_format

    n_range = args.n_pts#.astype('int')
    n_steps = args.step_size#.astype('int') 

    for i, ant in enumerate(ant_list):
        
        listx = []
        listy = []
        for filename in sorted(glob.glob(obsdir)):
        
            filx = FilReader(glob.glob(filename+"/"+ant+"/*_x.fil")[0])
           
            blockx = filx.readBlock(0, filx.header.nsamples)[1660:1740]

            fily = FilReader(glob.glob(filename+"/"+ant+"/*_y.fil")[0])
            
            blocky = fily.readBlock(0, filx.header.nsamples)[1660:1740]

            xmean = blockx.mean()
            ymean = blocky.mean()
        

            listx.append(xmean)
            listy.append(ymean)

        arrx = np.array(listx)
        arry = np.array(listy)
        
        steps = n_steps
        
        imgx = arrx.reshape(int(2*n_range/steps),int(2*n_range/steps))
        imgy = arry.reshape(int(2*n_range/steps),int(2*n_range/steps))


        az_list = np.arange(-1*(n_range),n_range, steps)
        el_list = np.arange(-1*(n_range),n_range, steps)

        centers = [-1*(n_range),n_range-steps,-1*(n_range),n_range-steps]
        dx, = np.diff(centers[:2])/(imgx.shape[1]-1)
        dy, = -np.diff(centers[2:])/(imgx.shape[0]-1)
        extent = [centers[0]-dx/2, centers[1]+dx/2, centers[2]+dy/2, centers[3]-dy/2]

        plt.figure(i*2, figsize=[12,8])

        plt.imshow(10*np.log10(imgx.T), interpolation='none', extent=[-1*(n_range),n_range-steps,-1*(n_range),n_range-steps], origin='lower')
        plt.xticks(np.arange(centers[0], centers[1]+dx, dx))
        plt.yticks(np.arange(centers[3], centers[2]+dy, dy))
        plt.axhline(y=0, color='red', linestyle='-')
        plt.axvline(x=0, color='red', linestyle='-')
        plt.ylabel("Elevation (deg)")
        plt.xlabel("Azimuth (deg)")
        plt.title("Antenna " + str(ant) + " X-Polarization")
        plt.colorbar()

        plt.figure(i*2+1, figsize=[12,8])

        plt.imshow(10*np.log10(imgy.T), interpolation='none', extent=[-1*(n_range),n_range-steps,-1*(n_range),n_range-steps], origin='lower')
        plt.title("Antenna " + str(ant) + " Y-Polarization")
        plt.xticks(np.arange(centers[0], centers[1]+dx, dx))
        plt.yticks(np.arange(centers[3], centers[2]+dy, dy))
        plt.axhline(y=0, color='red', linestyle='-')
        plt.axvline(x=0, color='red', linestyle='-')
        plt.ylabel("Elevation (deg)")
        plt.xlabel("Azimuth (deg)")
        plt.colorbar()
        print("Done with ant: %s" %ant)

        if args.save_plot:
            pname = os.path.splitext(ant)+'.'+args.plot_format #plot_name
            #pname = os.path.join(plot_basedir, pname)
            plt.savefig(pname, format=plot_format, bbox_inches='tight')

    if not args.save_plot:
        plt.show()


if __name__ == "__main__":
    main()  
