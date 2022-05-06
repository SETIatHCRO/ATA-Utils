# Antonio Feed Sensor Visualization

Repository for Sebastian Lang thesis project


## weatherstation-to-mysql-v0.py ## 

This program gets the data from both weather stations at the ATA and sends it to the data.hcro.org MySQL database.
The weatherstations have the data available on weatherport-primary.hcro.org and weatherport-secondary.hcro.org they provide the data with telnet on port 4001.
The program is run every 5 minutes on control.hcro.org and the data is used for the Grafana Weather station dashboard data.

<img width="1277" alt="weatherstation" src="https://user-images.githubusercontent.com/99358159/167199888-34e6822f-09e8-40e9-b511-93febbb649c2.png">

## stddev_and_cryopower_against_time.py ##

To quantify vibration of the feeds the standard deviation of the accelerometer in z-direction is used. To calculate the standard deviation the sensor delivers 400 datapoints per second and one second of data is evaluated.
In this program the vibration and the power of the cryo cooler is plotted over the same time axis to visualize correlation between the two.

![1e](https://user-images.githubusercontent.com/99358159/167219086-3c1aa845-8b8e-47ac-8696-ee72cdb0d57c.png)


