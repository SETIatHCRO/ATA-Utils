# This program plots the cryopower and the accelstandard deviation in one plot


import pytz
from datetime import datetime
from fun_get_timeseries import get_timeseries
import matplotlib.pyplot as plt
from pickle import TRUE

ants = ['1c','1e','1g','1h','1k','2a','2b','2c','2e','2h','2j','2k','2l','2m','3d','3l','4e','4j','5b'] # all the antennas that get plotted


pst = pytz.timezone('US/pacific')
utc = pytz.timezone('UTC')

start = datetime(2022,4,7,8,0,0)   # select a time frame for the data
end = datetime(2022,4,8,4,0,0)

startdate = pst.localize(start)
enddate = pst.localize(end)

for count,ant in enumerate(ants):
    dataset1 = 'accelstdz'
    dataset2 = 'cryopower'
    table = 'feed_sensors'

    timeseries1 = get_timeseries(dataset1,table,startdate,enddate,ant)
    timeseries2 = get_timeseries(dataset2,table,startdate,enddate,ant)

    data1 = timeseries1['value']
    data2 = timeseries2['value']

    time1 = [(timeseries1['time'][x].timestamp()-timeseries1['time'][0].timestamp())/3600 for x in range(len(timeseries1['time']))] # lets the timeseries time start at 0 and is then changed into hours
    time2 = [(timeseries2['time'][x].timestamp()-timeseries2['time'][0].timestamp())/3600 for x in range(len(timeseries2['time']))]

    # plotting both datasets in one plot
    plt.figure(count)

    fig, ax1 = plt.subplots()
    fig.suptitle(f'Antenna {ant}', fontsize=12)
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

plt.show()