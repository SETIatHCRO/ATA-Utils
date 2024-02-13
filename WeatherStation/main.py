#! /usr/bin/env python3
'''
Main code to read and display the weather stations' data.
'''

from gui import WeatherInterface, update_loop
import time, os

dir_name = os.path.dirname(__file__)
error_log_file = f"{dir_name}/launch_error.log"

try:
	# Create the object controlling the GUI
	interface = WeatherInterface()
except Exception as exception:
	with open(error_log_file, "a+") as log_file:
		log_file.write(str(exception)+'\n') 

	quit()
# update the WS values periodically using telnet
update_loop(weather_interface=interface)

# Start the GUI. Script will stay in this loop
# until the GUI window is closed or the process is killed.
interface.root.mainloop()
