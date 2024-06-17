'''
GUI to display the Weather station's data.
The 'WeatherInterface' object controls the 3 frame objects 'Summary', 'WS1' and 'WS2'
'add_menu_buttons' function add the buttons to switch between the GUI frames
update_loop function uses updateData.py
'''

import tkinter as tk
from update_data import TelnetLink
from time import time, strftime, localtime

# Global GUI variables
FONT = 'Arial'
FONTSIZE = 30
REDHEX = '#ff0000'
GREENHEX = '#006400'
BLUEHEX = '#0000ff'


WINDOW_WIDTH = 720
WINDOW_HEIGHT = 480

HOSTNAME1 = 'weatherport-primary.hcro.org'
PORT1 = 4001
HOSTNAME2 = 'weatherport-secondary.hcro.org'
PORT2 = 4001
DEGREESIGN = '\N{DEGREE SIGN}'


class WeatherInterface():
    ''' Controll the 3 weather frames. '''

    def __init__(self):
        # GUI window (root) setup
        self.root = tk.Tk()
        self.root.winfo_width()
        self.root.title("HCRO Weather")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        self.sensor_values = {} # Will be filled with telnet data

        self.button_frame = tk.Frame()
        self.button_frame.rowconfigure(1, weight=1)
        self.button_frame.columnconfigure(3, weight=1)

        #self.background = tk.PhotoImage(file = "background.png")

        add_menu_buttons(
            interface=self,
            button_frame=self.button_frame)

        # Open both telnet connections, ready to read weather station's data
        self.telnet_link_1 = TelnetLink(host = HOSTNAME1, port = PORT1, link_name = 'WS1')
        self.telnet_link_2 = TelnetLink(host = HOSTNAME2, port = PORT2, link_name = 'WS2')

        # Create each tk frame object and add it to the directory
        self.frame_objects = {}
        for frameObject in (Summary, WS1, WS2):
            new_object = frameObject(parent=self.root, interface=self)
            self.frame_objects[frameObject.__name__] = new_object
            new_object.frame.place(x=0, y=0, relwidth=1, relheight=1)

        # Display summary page first, can be later changed using the gui buttons
        self.show_frame("Summary")


    def show_frame(self, frame_name):
        ''' Display the tk frame 'frame_name' by putting it on top of the others. '''

        frame = self.frame_objects[frame_name].frame
        frame.place(x=0, y=0, relwidth=1, relheight=0.75)
        frame.tkraise()

        self.button_frame.tkraise()
        self.button_frame.place(relx=0.5, rely=0.85, relwidth=1, relheight=0.2, anchor=tk.CENTER)



    def updatevalues(self):
        ''' Update the frames with info from the weather stations. '''

        dict_ws1 = self.telnet_link_1.read_values()
        dict_ws2 = self.telnet_link_2.read_values()
        self.sensor_values = {**dict_ws1, **dict_ws2} # Merge the 2 dicts

        # Update title bar with last updated time:
        current_unix_time = time()
        t_disp_WS1 = self.sensor_values['WS1_update_display_time']
        t_disp_WS2 = self.sensor_values['WS2_update_display_time']
        t_unix_WS1 = self.sensor_values['WS1_update_unix_time']
        t_unix_WS2 = self.sensor_values['WS2_update_unix_time']

        # Use the oldest of the two WS time to be conservative:
        if t_unix_WS1 < t_unix_WS2:
            t_disp = t_disp_WS1
            t_unix = t_unix_WS1
        else:
            t_disp = t_disp_WS2
            t_unix = t_unix_WS2

        if current_unix_time - t_unix < 120: # Good: has updated < 2min ago
            self.root.title(f"HCRO Weather - Last Update: {t_disp}")
        else: # There is a problem, not updated since 2 minutes
            self.root.title(f"HCRO Weather - [WARNING] Last Update: {t_disp}")
            # Print telenet values to help troubleshooting tkinter window not updating
            print(f"Latest sensor values from tenet: {strftime('%m/%d %H:%M', localtime())}")
            print(self.sensor_values)
            print(" -------------------------------- \n\n")

        for frame_object in self.frame_objects.items():
            # frame_object[1] is the object, [0] is the dict key
            current_frame_object = frame_object[1]
            self.clear_widgets(frame=current_frame_object.frame)
            #background_image = tk.Label(current_frame_object.frame, image=self.background)
            #background_image.place(x=0, y=0, relwidth=1, relheight=1)
            current_frame_object.update_frame_values()


    def clear_widgets(self,frame):
        ''' 
        Destroy all widgets from tk frame to prevent number from growing
        when updating the frame with new telnet values.
        '''

        for widget in frame.winfo_children():
            widget.destroy()


def add_menu_buttons(interface, button_frame):
    '''
    Buttons to select frame aligned with a grid, always there.
    
    interface: the weather interface object (used to switch frames)
    frame: the frame to display the buttons on
    '''

    summary_button = tk.Button(
        button_frame,
        text = 'Main',
        font = (FONT,FONTSIZE),
        command = lambda: interface.show_frame("Summary"))
    summary_button.place(relx=0.25, rely=0.5, relwidth=0.2, relheight=0.8, anchor=tk.CENTER)

    ws1_button = tk.Button(
        button_frame,
        text = 'WS1',
        font = (FONT,FONTSIZE),
        command = lambda: interface.show_frame("WS1"))
    ws1_button.place(relx=0.5, rely=0.5, relwidth=0.2, relheight=0.8, anchor=tk.CENTER)

    ws2_button = tk.Button(
        button_frame,
        font = (FONT,FONTSIZE),
        text = 'WS2',
        command = lambda: interface.show_frame("WS2"))
    ws2_button.place(relx=0.75, rely=0.5, relwidth=0.2, relheight=0.8, anchor=tk.CENTER)


class Summary():
    ''' Most important info from WS1 and WS2.'''

    def __init__(self, parent, interface):
        self.frame = tk.Frame(parent)
        self.interface = interface

        # Row/column distances for place() function
        self.column0 = 0.04
        self.column1 = 0.25
        self.column2 = 0.7
        self.row0 = 0.05
        self.row1 = 0.20
        self.row2 = 0.5
        self.row3 = 0.65

    def update_frame_values(self):
        ''' 
        Called by WeatherInterface.updatevalues() to update the tk frame values 
        once they are pulled from telnet.
        Define here what will appear on the 'Summary' GUI page.
        '''

        values_dict = self.interface.sensor_values

        # WS1:
        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text="WS1:")
        tmp_label.place(relx=self.column0, rely=self.row0)

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            fg = REDHEX,
            text=f"T: {values_dict['WS1_AirTemp']}{DEGREESIGN}C")
        tmp_label.place(relx=self.column1, rely=self.row0)

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            fg = BLUEHEX,
            text=f"H: {values_dict['WS1_RelHumidity']}%")
        tmp_label.place(relx=self.column2, rely=self.row0)

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            fg=GREENHEX,
            text=f"W: {'{:.1f}'.format(float(values_dict['WS1_WindSpeedAvg'])*3.6)}km/h")
        tmp_label.place(relx=self.column1, rely=self.row1)

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            fg=GREENHEX,
            text=f"Dir: {values_dict['WS1_WindDirAvg']}{DEGREESIGN}")
        tmp_label.place(relx=self.column2, rely=self.row1)

        # WS2:
        tmp_label = tk.Label(
                    self.frame,
                    font=(FONT, FONTSIZE),
                    text="WS2:")
        tmp_label.place(relx=self.column0, rely=self.row2)

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            fg=REDHEX,
            text=f"T: {values_dict['WS2_AirTemp']}{DEGREESIGN}C")
        tmp_label.place(relx=self.column1, rely=self.row2)

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            fg=BLUEHEX,
            text=f"H:{values_dict['WS2_RelHumidity']}%")
        tmp_label.place(relx=self.column2, rely=self.row2)

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            fg=GREENHEX,
            text=f"W: {'{:.1f}'.format(float(values_dict['WS2_WindSpeedAvg'])*3.6)}km/h")
        tmp_label.place(relx=self.column1, rely=self.row3)

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            fg=GREENHEX,
            text=f"Dir: {values_dict['WS2_WindDirAvg']}{DEGREESIGN}")
        tmp_label.place(relx=self.column2, rely=self.row3)


class WS1():
    ''' Detailled info about the first weather station WS1.'''

    def __init__(self, parent, interface):
        self.frame = tk.Frame(parent)
        self.frame.rowconfigure(3, weight=1)
        self.frame.columnconfigure(2, weight=1)
        self.interface = interface
        self.column = 0.01 # for text alignment


    def update_frame_values(self):
        ''' 
        Called by WeatherInterface.updatevalues() to update the tk frame values 
        once they are pulled from telnet.
        Define here what will appear on the 'WS1' GUI page.
        '''

        values_dict = self.interface.sensor_values

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Vaisala WXT530 Id: {values_dict['WS1_id']}",
            #bg='grey'
            )
        tmp_label.place(relx=self.column, rely=0.06)

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Heating Temperature: {values_dict['WS1_HeatingTemp']}{DEGREESIGN}C")
        tmp_label.place(relx=self.column, rely=0.23)

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Heating Voltage: {values_dict['WS1_HeatingVoltage']}V")
        tmp_label.place(relx=self.column, rely=0.4)

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Supply Voltage: {values_dict['WS1_SupplyVoltage']}V")
        tmp_label.place(relx=self.column, rely=0.57)

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Reference Voltage: {values_dict['WS1_refVoltage']}V")
        tmp_label.place(relx=self.column, rely=0.74)


class WS2():
    ''' Detailled info about the second weather station WS2.'''

    def __init__(self, parent, interface):
        self.frame = tk.Frame(parent)
        self.frame.rowconfigure(3, weight=1)
        self.frame.columnconfigure(2, weight=1)
        self.interface = interface
        self.column = 0.01 # place() text alignment


    def update_frame_values(self):
        ''' 
        Called by WeatherInterface.updatevalues() to update the tk frame values 
        once they are pulled from telnet.
        Define here what will appear on the 'WS2' GUI page.
        '''

        values_dict = self.interface.sensor_values

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Vaisala WXT530 Id: {values_dict['WS2_id']}")
        tmp_label.place(relx=self.column, rely=0.06)

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Heating Temperature: {values_dict['WS2_HeatingTemp']}{DEGREESIGN}C")
        tmp_label.place(relx=self.column, rely=0.23)

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Heating Voltage: {values_dict['WS2_HeatingVoltage']}V")
        tmp_label.place(relx=self.column, rely=0.4)

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Supply Voltage: {values_dict['WS2_SupplyVoltage']}V")
        tmp_label.place(relx=self.column, rely=0.57)

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Reference Voltage: {values_dict['WS2_refVoltage']}V")
        tmp_label.place(relx=self.column, rely=0.74)


def update_loop(weather_interface):
    '''Periodic actions that will be executed even when the script stays in the tk mainloop()'''

    weather_interface.updatevalues()

    # Function will be called every 20s to make it recurrent
    weather_interface.root.after(20000, lambda: update_loop(weather_interface))
