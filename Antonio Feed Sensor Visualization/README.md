# Antonio Feed Sensor Visualization

Repository for Sebastian Lang thesis project

## Python modules used ##

- telnetlib
- mysql.connector
- datetime
- pytz
- matplotlib
- tkinter
- tkcalendar

## weatherstation-to-mysql-v0.py ## 

This program gets the data from both weather stations at the ATA and sends it to the data.hcro.org MySQL database.
The weatherstations have the data available on weatherport-primary.hcro.org and weatherport-secondary.hcro.org they provide the data with telnet on port 4001.
The program is run every 5 minutes on control.hcro.org and the data is used for the Grafana Weather station dashboard data.

<img width="1277" alt="weatherstation" src="https://user-images.githubusercontent.com/99358159/167199888-34e6822f-09e8-40e9-b511-93febbb649c2.png">

## stddev_and_cryopower_against_time.py ##

To quantify vibration of the feeds the standard deviation of the accelerometer in z-direction is used. To calculate the standard deviation the sensor delivers 400 datapoints per second and one second of data is evaluated.
In this program the vibration and the power of the cryo cooler is plotted over the same time axis to visualize correlation between the two.

![1e](https://user-images.githubusercontent.com/99358159/167219086-3c1aa845-8b8e-47ac-8696-ee72cdb0d57c.png)

## vibration_by_power.py ##

To look at the vibration caused by the cryo cooler the average vibration at each power level of the cryo cooler is plotted. Also this program creates a histogram of the selected time frame to see the amount of time the cryo cooler ran at each power level. 

![plt2hap](https://user-images.githubusercontent.com/99358159/167479902-4204aaee-e7a9-4e1c-927e-bd155ea210f9.png)

![plt2hpt](https://user-images.githubusercontent.com/99358159/167479914-96a6896d-8658-467d-ad2b-174593968688.png)

## vibration_gui.py ##

To run this program you need fun_gui.py and fun_get_timeseries.py it's a graphical user interface to create the different plots, with an easy way to select a time frame and singular antennas. The program lets you plot and save the plots to a selected directory. To add new antennas to the program in the vibration_gui.py the checkbox for the new antenna needs to be activated.

<img width="560" alt="data analyzing tool" src="https://user-images.githubusercontent.com/99358159/168887769-4a278f96-e58e-428b-a7fe-3c4e5ef6fe7c.png">



