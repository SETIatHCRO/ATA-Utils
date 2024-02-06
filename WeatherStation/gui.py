'''
GUI to display the Weather station's data.
The 'WeatherInterface' object controls the 3 frame objects 'Summary', 'WS1' and 'WS2'
'add_menu_buttons' function add the buttons to switch between the GUI frames
update_loop function uses updateData.py
'''

import tkinter as tk
from tkinter import ttk
from update_data import TelnetLink


# Global GUI variables
FONT = 'Arial'
FONTSIZE = 17
REDHEX = '#ff0000'
GREENHEX = '#006400'
BLUEHEX = '#0000ff'
WINDOW_WIDTH = 440 # To fit RPI screen
WINDOW_HEIGHT = 280

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
        self.root.title("HCRO Weather")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        self.sensor_values = {} # Will be filled with telnet data

        self.button_frame = tk.Frame()
        self.button_frame.rowconfigure(1, weight=1)
        self.button_frame.columnconfigure(3, weight=1)

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
            new_object.frame.grid(row=0, column=0, sticky="nsew")

        # Display summary page first, can be later changed using the gui buttons
        self.show_frame("Summary")


    def show_frame(self, frame_name):
        ''' Display the tk frame 'frame_name' by putting it on top of the others. '''
        #master_grid = tk.Frame()
        #master_grid.rowconfigure(1, weight=1)
        #master_grid.columnconfigure(2, weight=1)

        frame = self.frame_objects[frame_name].frame
        frame.grid(row=0, column=0, sticky='nsew')
        frame.tkraise()

        self.button_frame.tkraise()
        self.button_frame.grid(row=1, column=0, sticky='ew')


    def updatevalues(self):
        ''' Update the frames with info from the weather stations. '''

        dict_ws1 = self.telnet_link_1.read_values()
        dict_ws2 = self.telnet_link_2.read_values()
        self.sensor_values = dict_ws1 | dict_ws2 # Merge the 2 dicts

        for frame_object in self.frame_objects.items():
            # frame_object[1] is the object, [0] is the dict key
            frame_object[1].updtate_frame_values()


def add_menu_buttons(interface, button_frame):
    '''
    Buttons to select frame aligned with a grid, always there.
    
    interface: the weather interface object (used to switch frames)
    frame: the frame to display the buttons on
    button_row: Which grig row to display
    '''

    summary_button = tk.Button(
        button_frame,
        text = 'Main',
        font = (FONT,FONTSIZE),
        command = lambda: interface.show_frame("Summary"))
    summary_button.grid(row=0, column=0, sticky='ew', padx=(int(WINDOW_WIDTH/10), 20))

    ws1_button = tk.Button(
        button_frame,
        text = 'WS1',
        font = (FONT,FONTSIZE),
        command = lambda: interface.show_frame("WS1"))
    ws1_button.grid(row=0, column=1, padx=20, sticky='ew')

    ws2_button = tk.Button(
        button_frame,
        font = (FONT,FONTSIZE),
        text = 'WS2',
        command = lambda: interface.show_frame("WS2"))
    ws2_button.grid(row=0, column=2, padx=20, sticky='ew')


class Summary():
    ''' Most important info from WS1 and WS2.'''

    def __init__(self, parent, interface):
        self.frame = tk.Frame(parent)
        self.frame.rowconfigure(5, weight=1) # Configure tk grid layout
        self.frame.columnconfigure(3, weight=1)
        self.interface = interface

        # Add horizontal spaces in the GUI
        for row_idx in range(self.frame.grid_size()[1]):
            self.frame.grid_rowconfigure(row_idx, minsize=30)


    def updtate_frame_values(self):
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
        tmp_label.grid(row=0, column=0, sticky='w',padx=(int(WINDOW_WIDTH/10), 10))

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            fg = REDHEX,
            text=f"T: {values_dict['WS1_AirTemp']}{DEGREESIGN}C")
        tmp_label.grid(row=0, column=1, sticky='w')

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            fg = BLUEHEX,
            text=f"H: {values_dict['WS1_RelHumidity']}%")
        tmp_label.grid(row=0, column=2, sticky='w', padx=(0, 50))

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            fg=GREENHEX,
            text=f"W: {values_dict['WS1_WindSpeedAvg']}km/h")
        tmp_label.grid(row=1, column=1, sticky='w')

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            fg=GREENHEX,
            text=f"Dir: {values_dict['WS1_WindDirAvg']}{DEGREESIGN}")
        tmp_label.grid(row=1, column=2, sticky='w')

        # WS2:
        tmp_label = tk.Label(
                    self.frame,
                    font=(FONT, FONTSIZE),
                    text="WS2:")
        tmp_label.grid(row=3, column=0, sticky='w',padx=(int(WINDOW_WIDTH/10), 5))

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            fg=REDHEX,
            text=f"T: {values_dict['WS2_AirTemp']}{DEGREESIGN}C")
        tmp_label.grid(row=3, column=1, sticky='w')

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            fg=BLUEHEX,
            text=f"H:{values_dict['WS2_RelHumidity']}%")
        tmp_label.grid(row=3, column=2, sticky='w')

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            fg=GREENHEX,
            text=f"W: {values_dict['WS2_WindSpeedAvg']}km/h")
        tmp_label.grid(row=4, column=1, sticky='w')

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            fg=GREENHEX,
            text=f"Dir: {values_dict['WS2_WindDirAvg']}{DEGREESIGN}")
        tmp_label.grid(row=4, column=2, sticky='w')

        # Horizontal line between WS data
        tmp_separator = ttk.Separator(
            self.frame,
            orient='horizontal')
        tmp_separator.grid(
            row=2,
            column=0,
            columnspan=3,
            ipadx=100,
            sticky='ew')

        tmp_separator = ttk.Separator(
            self.frame,
            orient='horizontal')
        tmp_separator.grid(
            row=5,
            column=0,
            columnspan=3,
            ipadx=100,
            sticky='ew')


class WS1():
    ''' Detailled info about the first weather station WS1.'''

    def __init__(self, parent, interface):
        #super(WS1, self).__init__() # initialize parent (tk.Frame)
        self.frame = tk.Frame(parent)
        self.frame.rowconfigure(3, weight=1)
        self.frame.columnconfigure(2, weight=1)
        self.interface = interface


    def updtate_frame_values(self):
        ''' 
        Called by WeatherInterface.updatevalues() to update the tk frame values 
        once they are pulled from telnet.
        Define here what will appear on the 'WS1' GUI page.
        '''

        values_dict = self.interface.sensor_values

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Vaisala WXT530 Id: {values_dict['WS1_id']}")
        tmp_label.grid(row=0, column=0, sticky='w')

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Heating Temperature: {values_dict['WS1_HeatingTemp']}{DEGREESIGN}C")
        tmp_label.grid(row=1, column=0, sticky='w')

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Heating Voltage: {values_dict['WS1_HeatingVoltage']}V")
        tmp_label.grid(row=2, column=0, sticky='w')

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Supply Voltage: {values_dict['WS1_SupplyVoltage']}V")
        tmp_label.grid(row=3, column=0, sticky='w')

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Reference Voltage: {values_dict['WS1_refVoltage']}V")
        tmp_label.grid(row=4, column=0, sticky='w')


class WS2():
    ''' Detailled info about the second weather station WS2.'''

    def __init__(self, parent, interface):
        #super(WS2, self).__init__() # initialize parent (tk.Frame)
        self.frame = tk.Frame(parent)
        self.frame.rowconfigure(3, weight=1)
        self.frame.columnconfigure(2, weight=1)
        self.interface = interface


    def updtate_frame_values(self):
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
        tmp_label.grid(row=0, column=0, sticky='w')

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Heating Temperature: {values_dict['WS2_HeatingTemp']}{DEGREESIGN}C")
        tmp_label.grid(row=1, column=0, sticky='w')

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Heating Voltage: {values_dict['WS2_HeatingVoltage']}V")
        tmp_label.grid(row=2, column=0, sticky='w')

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Supply Voltage: {values_dict['WS2_SupplyVoltage']}V")
        tmp_label.grid(row=3, column=0, sticky='w')

        tmp_label = tk.Label(
            self.frame,
            font=(FONT, FONTSIZE),
            text=f"Reference Voltage: {values_dict['WS2_refVoltage']}V")
        tmp_label.grid(row=4, column=0, sticky='w')


def update_loop(weather_interface):
    '''Periodic actions that will be executed even when the script stays in the tk mainloop()'''

    weather_interface.updatevalues()

     # Function will be called again in 20s to make it recurrent
    weather_interface.root.after(20000, lambda: update_loop(weather_interface))
