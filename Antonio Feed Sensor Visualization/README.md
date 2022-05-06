# Antonio Feed Sensor Visualization

Repository for Sebastian Lang thesis project


## weatherstation-to-mysql-v0.py ## 

This program gets the data from both weather stations at the ATA and sends it to the data.hcro.org MySQL database.
The weatherstations have the data available on weatherport-primary.hcro.org and weatherport-secondary.hcro.org they provide the data with telnet on port 4001.
The program is run every 5 minutes on control.hcro.org and the data is used for the Grafana Weather station dashboard data.

<img width="1277" alt="weatherstation" src="https://user-images.githubusercontent.com/99358159/167199888-34e6822f-09e8-40e9-b511-93febbb649c2.png">
