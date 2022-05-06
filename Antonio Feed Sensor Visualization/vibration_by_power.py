# This program creates a histogram of the cryopower per antenna over a certain time frame
# also it shows the average standard deviation of the accelerometer at each power level in the time frame


import pytz
from datetime import datetime
from fun_get_timeseries import get_timeseries
import numpy as np
import matplotlib.pyplot as plt


pst = pytz.timezone('US/pacific')
utc = pytz.timezone('UTC')

start = datetime(2022,3,10,9,30,0)  # time frame of the data 
end = datetime(2022,5,1,23,30,0)

startdate = pst.localize(start)
enddate = pst.localize(end)

antennas = ['1c','1e','1g','1h','1k','2a','2b','2c','2h','2j','2k','2l','2m','3d','3l','4e','4j','5b']  #necessary parameters for the sql queries
table = 'feed_sensors'
dataset1 = 'accelstdz'
dataset2 = 'cryopower'
dataset3 = 'primary_outside_temp_c'

seriestemp = get_timeseries(dataset3,'weather',startdate,enddate) # for calculating the average temperature during the time frame of the data

averagetemp = round(np.mean(seriestemp['value']),1)

for n,ant in enumerate(antennas):
    antenna = ant
    seriesaccel = get_timeseries(dataset1,table,startdate,enddate,antenna)
    seriespower = get_timeseries(dataset2,table,startdate,enddate,antenna)

    roundpower = [round(x,0) for x in seriespower['value']] # get rounded values of the power levels to get good amount of different power levels

    punique = [] # all the unique power leves that exist in the data set
        
    for x in roundpower:
    
        if x not in punique:
            punique.append(x)

    punique.sort(key=float)




    maxlist = []        # maximum accel at certain powerlevel
    minlist = []        # minimum accel at certain powerlevel
    meanlist = []       # average accel at certain powerlevel
    amountlist = []     # amount of datapoints in certain powerlevel

    for cnt,y in enumerate(punique):
        accellist = [] # the acceleration values that belong to one power level
        for count,x in enumerate(roundpower):
            if punique[cnt] == x:
                accellist.append(seriesaccel['value'][count])

        # populating the lists and creating an excel sheet to safe the data


       

        maxlist.append(np.max(accellist))
        minlist.append(np.min(accellist))
        meanlist.append(np.mean(accellist))
        amountlist.append(len(accellist))
    

    

    # creating the plots for the data

    plt.figure(n+1)
    plt.title(f'Power/Time distribution {ant} over 1 month; average temp: {averagetemp}°C')
    plt.plot(punique,[x/len(roundpower)*100 for x in amountlist]) # norms the y axes to make data more easyly comparable
    plt.xlabel('Power in W')
    plt.ylabel('Amount of datapoints in Timeframe in %')
    plt.grid()
    # plt.savefig(r"C:\Users\sebas\Documents\Informatik\Bachelorarbeit\Measurements\Power-Accel-March\plt"+f'{ant}pt.png') # uncomment if figures should be saved
   
    
    plt.figure(-(n+1))
    plt.title(f'Accel/Power {ant} over 1 month; average temp: {averagetemp}°C')
    plt.xlabel('Power in W')
    plt.ylabel('Vibration in standardeviation of accelz g ')
    plt.plot(punique,meanlist)
    plt.grid()
    # plt.savefig(r"C:\Users\sebas\Documents\Informatik\Bachelorarbeit\Measurements\Power-Accel-March\plt"+f'{ant}ap.png') # uncomment if figures should be safed

    plt.show()
   