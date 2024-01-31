#! /usr/bin/env python3
'''
Main code to read and display the weather stations' data.
'''

from gui import WeatherInterface, update_loop

# Create the object controlling the GUI
interface = WeatherInterface()

# update the WS values periodically using telnet
update_loop(weather_interface=interface)

# Start the GUI. Script will stay in this loop
# until the GUI window is closed or the process is killed.
interface.root.mainloop()
