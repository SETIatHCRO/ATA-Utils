# This function provides a dictionary that selects data from the SQL database
# between two points in time for further analyzing

import mysql.connector
from datetime import timezone
import pytz


def get_timeseries(dataseries,table,startdate,enddate,ants=""):
    # function to create timeseries out of sql database
   
    pst = pytz.timezone('US/pacific')
    utc = pytz.timezone('UTC')

    

    startutc = startdate.astimezone(utc)    #all the timestamps in the SQL database are in UTC
    endutc = enddate.astimezone(utc)


    startstr = startutc.strftime("%Y-%m-%d %H:%M:%S")   # creating the right format time string for the SQL querie
    endstr = endutc.strftime("%Y-%m-%d %H:%M:%S")


    # if there are multiple antennas in the selected table pics one antenna, for example the weather table doesn't have ants in it

    if ants:                                                            
        sql =f"""SELECT ts, ant,{dataseries} FROM {table}\
        WHERE ant = '{ants}' AND ts BETWEEN '{startstr}' AND '{endstr}'
        ORDER BY ts ASC
        """
    else:
        sql = f"""SELECT ts,{dataseries} FROM {table}\
        WHERE ts BETWEEN '{startstr}' AND '{endstr}'
        ORDER BY ts ASC
        """

    # connectiing to the sql database    
    try:        
        conn = mysql.connector.connect(user='grafanauser', password='Mars2020', host='data.hcro.org', database='grafanadata', auth_plugin='mysql_native_password')
    except:
        print("Connection to database failed")

    #Creating a cursor object using the cursor() method
    cursor = conn.cursor()
    cursor.execute(sql)
    
    rows = cursor.fetchall()
    x = []
    y = []

    # row[0] = time row[1] = antenna/value row[2]= value if antenna is selected
    
    if ants:
        for row in rows:
            
            x.append(row[0].replace(tzinfo=timezone.utc).astimezone(tz=pytz.timezone('US/Pacific')))
            y.append(row[2])    
    else:
        for row in rows:
            
            x.append(row[0].replace(tzinfo=timezone.utc).astimezone(tz=pytz.timezone('US/Pacific')))
            y.append(row[1])

    cursor.close()

    # returns a dictionary with a time list and a value list of the same length

    timeseries = {
        'time' : x,
        'value': y
    }

    return timeseries