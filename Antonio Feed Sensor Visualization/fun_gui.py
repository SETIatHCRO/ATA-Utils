from fun_get_timeseries import get_timeseries
import pytz
import numpy as np
import matplotlib.pyplot as plt
from pickle import TRUE
import pandas as pd


def vibration(startdatec,enddatec,ants,saveflg,showflg,plotpath):

    # plots vibration against the cryopower in the selected time frame

    pst = pytz.timezone('US/pacific')
    utc = pytz.timezone('UTC')

    
    start = startdatec  # time frame of the data 
    end = enddatec

    startdate = pst.localize(start)
    enddate = pst.localize(end)

    antennas = ants  #necessary parameters for the sql queries
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

        stddevlist = []     # standard deviation of the accel

        meanstdp = []       # accelmean + standard deviation
        meanstdm = []       # accelmean - standard deviation

        for cnt,y in enumerate(punique):
            accellist = [] # the acceleration values that belong to one power level
            for count,x in enumerate(roundpower):
                if punique[cnt] == x:
                    accellist.append(seriesaccel['value'][count])

            # populating the lists and creating an excel sheet to safe the data

            mean = np.mean(accellist)
            stddev = np.std(accellist)

            maxlist.append(np.max(accellist))
            minlist.append(np.min(accellist))
            meanlist.append(mean)
            amountlist.append(len(accellist))
            stddevlist.append(stddev)
            meanstdp.append(mean+stddev)
            meanstdm.append(mean-stddev)
        

        

        # creating the plots for the data

       
        # plt.savefig(r"C:\Users\sebas\Documents\Informatik\Bachelorarbeit\Measurements\Power-Accel-March\plt"+f'{ant}pt.png') # uncomment if figures should be saved
    
        
        plt.figure(n+1)
        plt.title(f'Accel/Power {ant}; average outside temp: {averagetemp}°C')
        plt.xlabel('Power in W')
        plt.ylabel('Vibration in standardeviation of accelz g ')
        plt.plot(punique,meanlist)
        plt.fill_between(punique, meanstdm, meanstdp,facecolor='b',alpha=0.2,edgecolor='none',label = 'Standard deviation')
        plt.grid()
        plt.legend()

        if saveflg == 1:
            plt.savefig(plotpath+'vibrationplt'+ant+'.png')
        # plt.savefig(r"C:\Users\sebas\Documents\Informatik\Bachelorarbeit\Measurements\Power-Accel-March\plt"+f'{ant}ap.png') # uncomment if figures should be safed

    if showflg == 1:
        plt.show()
    else:
        plt.close('all')


def cryopower(startdatec,enddatec,ants,saveflg,showflg,plotpath):

    # cryopower distribution in the selected timeframe

    pst = pytz.timezone('US/pacific')
    utc = pytz.timezone('UTC')

    
    start = startdatec  # time frame of the data 
    end = enddatec

    startdate = pst.localize(start)
    enddate = pst.localize(end)

    antennas = ants  #necessary parameters for the sql queries
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
        plt.title(f'Power/Time distribution {ant}; average outside temp: {averagetemp}°C')
        plt.plot(punique,[x/len(roundpower)*100 for x in amountlist]) # norms the y axes to make data more easyly comparable
        plt.xlabel('Power in W')
        plt.ylabel('Amount of datapoints in Timeframe in %')
        plt.grid()
        
        # plt.savefig(r"C:\Users\sebas\Documents\Informatik\Bachelorarbeit\Measurements\Power-Accel-March\plt"+f'{ant}pt.png') # uncomment if figures should be saved
        if saveflg == 1:
            plt.savefig(plotpath+'cryopowerplt'+ant+'.png')
        # plt.savefig(r"C:\Users\sebas\Documents\Informatik\Bachelorarbeit\Measurements\Power-Accel-March\plt"+f'{ant}ap.png') # uncomment if figures should be safed

    if showflg == 1:
        plt.show()
    else:
        plt.close('all')


def cryotemp(startdatec,enddatec,ants,saveflg,showflg,plotpath):

    # plots cryopower against the outside temperature

    pst = pytz.timezone('US/pacific')
    utc = pytz.timezone('UTC')

    start = startdatec  # time frame of the data 
    end = enddatec

    startdate = pst.localize(start)
    enddate = pst.localize(end)

    antennas = ants  #necessary parameters for the sql queries
    table1 = 'feed_sensors'

    dataset1 = 'cryopower'
    dataset2 = 'outsideairtemp'

    for n,ant in enumerate(antennas):
        antenna = ant
        seriespower = get_timeseries(dataset1,table1,startdate,enddate,ant)
        seriestemp = get_timeseries(dataset2,table1,startdate,enddate,ant)

        roundtemp = [round(x,0) for x in seriestemp['value']] # get rounded values of the temperature levels to get good amount of different temperature levels

        tunique = [] # all the unique temperature leves that exist in the data set
            
        for x in roundtemp:
        
            if x not in tunique:
                tunique.append(x)

        tunique.sort(key=float)

        if -99 in tunique:
            tunique.remove(-99)


        maxlist = []        # maximum power at certain temp
        minlist = []        # minimum power at certain temp
        meanlist = []       # average power at certain temp
        amountlist = []     # amount of datapoints in certain temp
        stddevlist = []     # standard deviation of the power at temperature

        meanstdp = []       # mean + standard deviation
        meanstdm = []       # mean - standard deviation

        for cnt,y in enumerate(tunique):
            powerlist = [] # the power values that belong to one temp level
            for count,x in enumerate(roundtemp):
                if tunique[cnt] == x:
                    powerlist.append(seriespower['value'][count])

            # populating the lists 

            mean = np.mean(powerlist)
            stddev = np.std(powerlist)

            maxlist.append(np.max(powerlist))
            minlist.append(np.min(powerlist))
            meanlist.append(mean)
            amountlist.append(len(powerlist))
            stddevlist.append(stddev)
            meanstdp.append(mean+stddev)
            meanstdm.append(mean-stddev)

        # creating the plots for the data

        plt.figure(n+1)
        plt.title(f'Power/Temp {ant}')
        plt.xlabel('Temperature in °C')
        plt.ylabel('Power in W')
        plt.plot(tunique,meanlist)
        plt.fill_between(tunique, meanstdm, meanstdp,facecolor='b',alpha=0.2,edgecolor='none',label='Standard deviation')
        plt.grid()
        plt.legend()
        if saveflg == 1:
            plt.savefig(plotpath+'cryotemp'+ant+'.png')
        # plt.savefig(r"C:\Users\sebas\Documents\Informatik\Bachelorarbeit\Measurements\Power-Accel-March\plt"+f'{ant}ap.png') # uncomment if figures should be safed

    if showflg == 1:
        plt.show()
    else:
        plt.close('all')

def temp_distribution(startdatec,enddatec,ants,saveflg,showflg,plotpath):

    # function for the temperature distribution in the selected timeframe

    pst = pytz.timezone('US/pacific')
    utc = pytz.timezone('UTC')

    start = startdatec  # time frame of the data     
    end = enddatec

    startdate = pst.localize(start)
    enddate = pst.localize(end)

    antennas = ants  #necessary parameters for the sql queries
    table1 = 'feed_sensors'

    dataset1 = 'cryopower'
    dataset2 = 'outsideairtemp'

    for n,ant in enumerate(antennas):
        antenna = ant
        seriespower = get_timeseries(dataset1,table1,startdate,enddate,ant)
        seriestemp = get_timeseries(dataset2,table1,startdate,enddate,ant)

        roundtemp = [round(x,0) for x in seriestemp['value']] # get rounded values of the temperature levels to get good amount of different temperature levels

        tunique = [] # all the unique temperature leves that exist in the data set
                
        for x in roundtemp:
            
            if x not in tunique:
                tunique.append(x)

        tunique.sort(key=float)

        if -99 in tunique:
            tunique.remove(-99)


        maxlist = []        # maximum power at certain temp
        minlist = []        # minimum power at certain temp
        meanlist = []       # average power at certain temp
        amountlist = []     # amount of datapoints in certain temp

        for cnt,y in enumerate(tunique):
            powerlist = [] # the power values that belong to one temp level
            for count,x in enumerate(roundtemp):
                if tunique[cnt] == x:
                    powerlist.append(seriespower['value'][count])

                # populating the lists 


            

            maxlist.append(np.max(powerlist))
            minlist.append(np.min(powerlist))
            meanlist.append(np.mean(powerlist))
            amountlist.append(len(powerlist))
            

            # creating the plots for the data

        plt.figure(n+1)
        plt.title(f'Power/Temp {ant}')
        plt.xlabel('Temperature in °C')
        plt.ylabel('Temperature distribution in %')
        plt.plot(tunique,[x/len(roundtemp)*100 for x in amountlist])
        plt.grid()

        if saveflg == 1:
            plt.savefig(plotpath+'tempdist'+ant+'.png')
        # plt.savefig(r"C:\Users\sebas\Documents\Informatik\Bachelorarbeit\Measurements\Power-Accel-March\plt"+f'{ant}ap.png') # uncomment if figures should be safed
    if showflg == 1:
        plt.show()
    else:
        plt.close('all')

def cryoplot(startdatec,enddatec,ants,saveflg,showflg,plotpath):

    # function to plot cryopower and vibration over the same x-axes
    antens = ants # all the antennas that get plotted


    pst = pytz.timezone('US/pacific')
    utc = pytz.timezone('UTC')

    start = startdatec   # select a time frame for the data
    end = enddatec

    startdate = pst.localize(start)
    enddate = pst.localize(end)

    for count,ant in enumerate(antens):
        dataset1 = 'accelstdz'
        dataset2 = 'cryopower'
        table = 'feed_sensors'

        timeseries1 = get_timeseries(dataset1,table,startdate,enddate,ant)
        timeseries2 = get_timeseries(dataset2,table,startdate,enddate,ant)

        data1 = timeseries1['value']
        data2 = timeseries2['value']

        time1 = [(timeseries1['time'][x].timestamp()-timeseries1['time'][0].timestamp())/3600 for x in range(len(timeseries1['time']))] # lets the timeseries time start at 0 and is then changed into hours
        time2 = [(timeseries2['time'][x].timestamp()-timeseries2['time'][0].timestamp())/3600 for x in range(len(timeseries2['time']))]

        df = pd.DataFrame({
            'value1':data1,
            'value2':data2
            })  

        corrlevel = round((df['value2'].corr(df['value1'])),3)

        # plotting both datasets in one plot
        plt.figure(count+1)

        fig, ax1 = plt.subplots()
        fig.suptitle(f'Antenna {ant} Corrlevel: {corrlevel}', fontsize=12)
        color = 'tab:red'
        ax1.set_xlabel('time in h')
        ax1.set_ylabel(dataset1+' '+ant+' in g', color=color)
        ax1.plot(time1, data1, color=color)
        ax1.tick_params(axis='y', labelcolor=color)

        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

        color = 'tab:blue'
        ax2.set_ylabel(dataset2+' '+ant+' in W', color=color)  # we already handled the x-label with ax1
        ax2.plot(time2, data2, color=color)
        ax2.tick_params(axis='y', labelcolor=color)

        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        plt.grid(visible=TRUE, which='both', axis='both')

        if saveflg == 1:
            plt.savefig(plotpath+'plot'+ant+'.png')

    if showflg == 1:
        plt.show()
    else:
        plt.close('all')


def vibrationxyz(startdatec,enddatec,ants,saveflg,showflg,plotpath):

    # plots vibration against the cryopower in the selected time frame

    pst = pytz.timezone('US/pacific')
    utc = pytz.timezone('UTC')

    
    start = startdatec  # time frame of the data 
    end = enddatec

    startdate = pst.localize(start)
    enddate = pst.localize(end)

    antennas = ants  #necessary parameters for the sql queries
    table = 'feed_sensors'
    dataset1 = 'accelstdz'
    dataset2 = 'cryopower'
    dataset3 = 'primary_outside_temp_c'
    dataset4 = 'accelstdy'
    dataset5 = 'accelstdx'

    seriestemp = get_timeseries(dataset3,'weather',startdate,enddate) # for calculating the average temperature during the time frame of the data

    averagetemp = round(np.mean(seriestemp['value']),1)

    for n,ant in enumerate(antennas):
        antenna = ant
        seriesaccelx = get_timeseries(dataset5,table,startdate,enddate,antenna)
        seriesaccely = get_timeseries(dataset4,table,startdate,enddate,antenna)
        seriesaccelz = get_timeseries(dataset1,table,startdate,enddate,antenna)
        seriespower = get_timeseries(dataset2,table,startdate,enddate,antenna)

        roundpower = [round(x,0) for x in seriespower['value']] # get rounded values of the power levels to get good amount of different power levels

        punique = [] # all the unique power leves that exist in the data set
            
        for x in roundpower:
        
            if x not in punique:
                punique.append(x)

        punique.sort(key=float)




        maxlistx = []        # maximum accel at certain powerlevel
        minlistx = []        # minimum accel at certain powerlevel
        meanlistx = []       # average accel at certain powerlevel
        amountlistx = []     # amount of datapoints in certain powerlevel

        stddevlistx = []     # standard deviation of the accel

        meanstdpx = []       # accelmean + standard deviation
        meanstdmx = []       # accelmean - standard deviation

        for cnt,y in enumerate(punique):
            accellist = [] # the acceleration values that belong to one power level
            for count,x in enumerate(roundpower):
                if punique[cnt] == x:
                    accellist.append(seriesaccelx['value'][count])

            # populating the lists and creating an excel sheet to safe the data

            mean = np.mean(accellist)
            stddev = np.std(accellist)

            maxlistx.append(np.max(accellist))
            minlistx.append(np.min(accellist))
            meanlistx.append(mean)
            amountlistx.append(len(accellist))
            stddevlistx.append(stddev)
            meanstdpx.append(mean+stddev)
            meanstdmx.append(mean-stddev)
        
        maxlisty = []        # maximum accel at certain powerlevel
        minlisty = []        # minimum accel at certain powerlevel
        meanlisty = []       # average accel at certain powerlevel
        amountlisty = []     # amount of datapoints in certain powerlevel

        stddevlisty = []     # standard deviation of the accel

        meanstdpy = []       # accelmean + standard deviation
        meanstdmy = []       # accelmean - standard deviation

        for cnt,y in enumerate(punique):
            accellist = [] # the acceleration values that belong to one power level
            for count,x in enumerate(roundpower):
                if punique[cnt] == x:
                    accellist.append(seriesaccely['value'][count])

            # populating the lists and creating an excel sheet to safe the data

            mean = np.mean(accellist)
            stddev = np.std(accellist)

            maxlisty.append(np.max(accellist))
            minlisty.append(np.min(accellist))
            meanlisty.append(mean)
            amountlisty.append(len(accellist))
            stddevlisty.append(stddev)
            meanstdpy.append(mean+stddev)
            meanstdmy.append(mean-stddev)
        

        maxlistz = []        # maximum accel at certain powerlevel
        minlistz = []        # minimum accel at certain powerlevel
        meanlistz = []       # average accel at certain powerlevel
        amountlistz = []     # amount of datapoints in certain powerlevel

        stddevlistz = []     # standard deviation of the accel

        meanstdpz = []       # accelmean + standard deviation
        meanstdmz = []       # accelmean - standard deviation

        for cnt,y in enumerate(punique):
            accellist = [] # the acceleration values that belong to one power level
            for count,x in enumerate(roundpower):
                if punique[cnt] == x:
                    accellist.append(seriesaccelz['value'][count])

            # populating the lists and creating an excel sheet to safe the data

            mean = np.mean(accellist)
            stddev = np.std(accellist)

            maxlistz.append(np.max(accellist))
            minlistz.append(np.min(accellist))
            meanlistz.append(mean)
            amountlistz.append(len(accellist))
            stddevlistz.append(stddev)
            meanstdpz.append(mean+stddev)
            meanstdmz.append(mean-stddev)

        # creating the plots for the data

       
        # plt.savefig(r"C:\Users\sebas\Documents\Informatik\Bachelorarbeit\Measurements\Power-Accel-March\plt"+f'{ant}pt.png') # uncomment if figures should be saved
    
        
       
        
        

        figure, axs = plt.subplots(3, sharex=True)
        figure.suptitle(f'Accel/Power {ant}; average outside temp: {averagetemp}°C')
        axs[0].plot(punique, meanlistx)
        axs[0].fill_between(punique, meanstdmx, meanstdpx,facecolor='b',alpha=0.2,edgecolor='none',label = 'Standard deviation')
        axs[0].grid()
        axs[0].legend()
        axs[0].set(ylabel='x-vibration')
        axs[1].plot(punique, meanlisty)
        axs[1].fill_between(punique, meanstdmy, meanstdpy,facecolor='b',alpha=0.2,edgecolor='none',label = 'Standard deviation')
        axs[1].grid()
        axs[1].legend()
        axs[1].set(ylabel='y-vibration')
        axs[2].plot(punique, meanlistz)
        axs[2].fill_between(punique, meanstdmz, meanstdpz,facecolor='b',alpha=0.2,edgecolor='none',label = 'Standard deviation')
        axs[2].grid()
        axs[2].legend()
        axs[2].set(ylabel='z-vibration',xlabel='Cryopower in W')

        if saveflg == 1:
            plt.savefig(plotpath+'vibrationxyzplt'+ant+'.png')
        # plt.savefig(r"C:\Users\sebas\Documents\Informatik\Bachelorarbeit\Measurements\Power-Accel-March\plt"+f'{ant}ap.png') # uncomment if figures should be safed

    if showflg == 1:
        plt.show()
    else:
        plt.close('all')
