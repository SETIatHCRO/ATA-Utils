import numpy as np
import pandas as pd
from scipy import stats
import sys
import matplotlib.pyplot as plt

MADF = 1.4826 #conversion from MAD to STD

def help_statement():
    print("This script displays the results of the pointing measurement as the offsets of xelevation and elevation vs xel and el for all entennae recorded")

if len(sys.argv) == 1:
    print("Please pass some files")
    help_statement()
    sys.exit(-1)

if sys.argv[1] == "-h" or sys.argv[1] == "--help":
    help_statement()
    sys.exit(0)

MADF = 1.4826 #conversion from MAD to STD
YLIM1, YLIM2 = -300, 300

listr = []

lista = []


for i, filename in enumerate(sys.argv[1:]):
    lista.append((filename[22:24]))

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

plt.show()
