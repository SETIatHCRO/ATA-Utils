# WeatherStation
02/2023: Marc Jacquart, mjacquart@seti.org

Graphical interface to display the two weather stations' data on a Raspberry Pi inside the HCRO data center.

main.py can be manually executed to start the Weather Station GUI.

## Setup to start automatically at reboot
1: The <path> '/home/sonata/ATA-Utils/WeatherStation' is hardcoded in 'WeatherStation.sh'. Change it to match your repository location. Replace <path> with this repo's path in the commands below.

2: Add the launch script as a cron job at restart
crontab -e
@reboot DISPLAY=:0 <path>/WeatherStation.sh
Note: DISPLAY=:0 is important to launch tkinter GUI at boot.

3: Make sure WeatherStation.sh and main.py are executable with chmod +x
chmod +x /<path>/WeatherStation.sh
chmod +x /<path>/main.py


## Technologies
Python - version 3.6 
