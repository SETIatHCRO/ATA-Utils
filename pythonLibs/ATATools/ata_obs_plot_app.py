#!/usr/bin/env python
import tkinter as tk
import sys,os
from tkinter import ttk, messagebox
from tkinter import messagebox

from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import numpy as np

from parse import parse

from astropy.coordinates import EarthLocation, AltAz, ICRS, SkyCoord
from astropy import units as u
from astropy.time import Time, TimeDelta

import pytz
import json

import ATATools.ata_sources as check
from ATATools.ata_obs_plan import ObsPlan

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib as mpl

import datetime

# Load custom Matplotlib rc parameters
exec(open("/opt/mnt/share/rcparams.py", "r").read())

# Global font
FONT = "Helvetica"

DEFAULT_TIMEZONE = "US/Pacific"

COLOR_CYCLER_LIST = list(mpl.rcParams['axes.prop_cycle'])

HARD_EL_LIM = 16.5 #degrees
SOFT_EL_LIM = 20.0 #degrees
OBSERVING_LOCATION = EarthLocation.from_geodetic(lat=40.8178*u.deg, lon=-121.4733*u.deg)

#Time to start observing script, change frequencies, RF/IF gain set, etc...
#INITIAL_OVERHEAD_TIME = 70 # seconds

# Slew rate:
#SLEW_RATE = 1.5 #deg/sec
#OBS_OVERHEAD = 10 #seconds

#INITIAL_AZ, INITIAL_EL = (0, 18) #parked position


class AutoCompleteCombobox(ttk.Combobox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_completion_list()

    def set_completion_list(self):
        """Use our completion list as the drop down selection menu."""
        completion_list = self['values']
        self._completion_list = sorted(completion_list)  # sorted list of strings
        self._hits = []
        self._hit_index = 0
        self.position = 0
        self.bind('<KeyRelease>', self.handle_keyrelease)

    def autocomplete(self, delta=0):
        """Autocomplete the Combobox, delta may be 0/1/-1 to cycle through possible hits."""
        if delta:  # need to delete selection otherwise we would fix the current position
            self.delete(self.position, tk.END)
        else:  # set position to end so selection starts where the text entry ended
            self.position = len(self.get())
        # collect hits
        _hits = [item for item in self._completion_list if item.lower().startswith(self.get().lower())]

        # if we have a hit, display it
        if _hits != self._hits:
            self._hit_index = 0
            self._hits = _hits
        if _hits:
            self._hit_index = (self._hit_index + delta) % len(_hits)
            self.delete(0, tk.END)
            self.insert(0, _hits[self._hit_index])
            self.select_range(self.position, tk.END)

    def handle_keyrelease(self, event):
        """Event handler for the keyrelease event on this widget."""
        if event.keysym in ('BackSpace', 'Delete'):
            self.delete(self.index(tk.INSERT), tk.END) #?
            self.position = self.index(tk.END)
            return
        if event.keysym == 'Return':
            return
        elif event.keysym in ('Left', 'Right', 'Up', 'Down'):
            return  # Do nothing for arrow keys
        self.autocomplete()



class ObsPlotApp:
    PLAN_OK = 0
    PLAN_WARNING = 1
    PLAN_ERROR = 2

    def __init__(self, root):
        self.root = root
        self.root.title("Observing plan plotter")

        self.error_in_plan = self.PLAN_OK # whether source would set or not during obs
        self.to_enable_disable = [] #list of everything to enable and disable

        # Create a menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Add Help menu to the menu bar
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu, font=(FONT, 14))
        help_menu.add_command(label="How to Use", command=self.show_help, font=(FONT, 14))
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about, font=(FONT, 14))

        # Create a frame for the plot
        self.frame_plot = tk.Frame(root)
        self.frame_plot.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a frame for user input
        self.frame_input = tk.Frame(root)
        self.frame_input.pack(side=tk.RIGHT, fill=tk.Y, padx=20, pady=20)

        # Date selection
        #self.date_label = tk.Label(self.frame_input, text="Select Start Date:", font=(FONT, 14))
        #self.date_label.pack(pady=2, anchor='w')

        # Frame for date and timezone
        self.frame_date_timezone = tk.Frame(self.frame_input)
        self.frame_date_timezone.pack(pady=0, anchor="w")

        # Timezone selection (dropdown)
        self.timezone_label = tk.Label(self.frame_date_timezone, text="Select Start Date:", font=(FONT, 14))
        self.timezone_label.grid(row=0, column=0, padx=0, sticky="w")

        # Populate the dropdown with all timezones using pytz
        self.timezone_combobox = AutoCompleteCombobox(self.frame_date_timezone, values=pytz.all_timezones, font=(FONT, 14))
        self.timezone_combobox.option_add('*TCombobox*Listbox.font', (FONT, 14))
        self.timezone_combobox.grid(row=0, column=1, padx=25, sticky="w")
        self.timezone_combobox.set(DEFAULT_TIMEZONE)  # Set default value
        self.to_enable_disable.append(self.timezone_combobox)

        # Bind Enter key and FocusOut event
        self.timezone_combobox.bind("<Return>", self.register_selection)
        self.timezone_combobox.bind("<FocusOut>", self.register_selection)

        # Bind the event to the combobox selection
        self.timezone_combobox.bind("<<ComboboxSelected>>", self.on_timezone_selected)

        # Apply a larger font directly to the DateEntry
        self.date_entry = DateEntry(self.frame_input, width=12, background='darkblue', 
                                    foreground='white', borderwidth=2, font=(FONT, 14))
        self.date_entry.pack(pady=2, anchor='w')
        self.to_enable_disable.append(self.date_entry)

        # Time input using Spinboxes for hours and minutes
        self.time_label = tk.Label(self.frame_input, text="Select Time (HH:MM):", font=(FONT, 14))
        self.time_label.pack(pady=2, anchor='w')

        self.time_frame = tk.Frame(self.frame_input)  # Container for spinboxes
        self.time_frame.pack(pady=1, anchor='w')

        # Get time now to fill in defaults
        dt_now = datetime.datetime.now(
                tz=pytz.timezone(self.timezone_combobox.get()))
        hh_now, mm_now = dt_now.hour, dt_now.minute

        self.hours_spin = tk.Spinbox(self.time_frame, from_=0, to=23, width=5, 
            format="%02.0f", font=(FONT, 14), textvariable=tk.DoubleVar(value=hh_now))
        self.minutes_spin = tk.Spinbox(self.time_frame, from_=0, to=59, width=5, 
            format="%02.0f", font=(FONT, 14), textvariable=tk.DoubleVar(value=mm_now))
        self.hours_spin.pack(side=tk.LEFT, padx=(0, 5))
        self.minutes_spin.pack(side=tk.LEFT)
        self.to_enable_disable.append(self.hours_spin)
        self.to_enable_disable.append(self.minutes_spin)

        # Source Name input
        self.source_name_label = tk.Label(self.frame_input, text="Source Name:", font=(FONT, 14))
        self.source_name_label.pack(pady=5, anchor='w')
        self.source_name_entry = tk.Entry(self.frame_input, font=(FONT, 14))
        self.source_name_entry.pack(pady=2, fill=tk.X)
        self.to_enable_disable.append(self.source_name_entry)

        # Observing Time input
        self.observing_time_label = tk.Label(self.frame_input, text="Observing Time [sec]:", font=(FONT, 14))
        self.observing_time_label.pack(pady=5, anchor='w')
        self.observing_time_entry = tk.Entry(self.frame_input, font=(FONT, 14))
        self.observing_time_entry.pack(pady=2, fill=tk.X)
        self.to_enable_disable.append(self.observing_time_entry)

        # Frame to hold the checkboxes
        self.checkbox_frame = tk.Frame(self.frame_input)
        self.checkbox_frame.pack(pady=5)

        # Checkboxes for "Initial Overhead" and "Slew Time"
        self.obs_overhead_var = tk.IntVar()
        self.slew_time_var = tk.IntVar()

        self.obs_overhead_check = tk.Checkbutton(self.checkbox_frame, text="Observation Overhead", variable=self.obs_overhead_var, font=(FONT, 14))
        self.to_enable_disable.append(self.obs_overhead_check)

        self.obs_overhead_check.grid(row=0, column=0, padx=5)
        self.obs_overhead_check.select()

        self.slew_time_check = tk.Checkbutton(self.checkbox_frame, text="Slew Time", variable=self.slew_time_var, font=(FONT, 14))
        self.slew_time_check.grid(row=0, column=1, padx=5)
        self.slew_time_check.select()
        self.to_enable_disable.append(self.slew_time_check)

        # Frame for entry_buttons
        self.entry_buttons_frame = tk.Frame(self.frame_input)
        self.entry_buttons_frame.pack(pady=0)

        # Add Entry Button
        self.add_button = tk.Button(self.entry_buttons_frame, text="Add Entry", command=self.add_entry, font=(FONT, 14))
        self.add_button.grid(row=0, column=0, padx=0)
        self.to_enable_disable.append(self.add_button)

        # Duplicate Entry Button
        self.duplicate_button = tk.Button(self.entry_buttons_frame, text="Duplicate Entries", command=self.duplicate_entry, font=(FONT, 14))
        self.duplicate_button.grid(row=0, column=1, padx=0)
        self.to_enable_disable.append(self.duplicate_button)

        # Button to remove selected entries
        self.remove_button = tk.Button(self.entry_buttons_frame, text="Remove Entries", command=self.remove_entry, font=(FONT, 14))
        self.remove_button.grid(row=0, column=2, padx=0)
        self.to_enable_disable.append(self.remove_button)

        # Frame to hold the listbox and scrollbar
        self.listbox_frame = tk.Frame(self.frame_input)
        self.listbox_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        # Listbox to display added entries
        self.entry_listbox = tk.Listbox(self.listbox_frame, height=15, selectmode=tk.SINGLE, font=(FONT, 14))
        self.entry_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.to_enable_disable.append(self.entry_listbox)

        # Scrollbar for the listbox
        self.scrollbar = tk.Scrollbar(self.listbox_frame, orient="vertical", command=self.entry_listbox.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Link the scrollbar with the listbox
        self.entry_listbox.config(yscrollcommand=self.scrollbar.set)


        # Error display label
        self.error_label = tk.Label(self.frame_input, text="", fg="red", font=(FONT, 14))
        self.error_label.pack(pady=5)


        # Frame for generate and reset buttons
        self.gen_reset_buttons_frame = tk.Frame(self.frame_input)
        self.gen_reset_buttons_frame.pack(pady=0)

        # Generate button at the bottom
        self.generate_button = tk.Button(self.gen_reset_buttons_frame, text="Generate Plot", command=self.generate_plot, font=(FONT, 14))
        self.generate_button.grid(row=0, column=0, padx=0)
        self.to_enable_disable.append(self.generate_button)

        # Reset Button
        self.reset_button = tk.Button(self.gen_reset_buttons_frame, text="Reset All", command=self.reset_all, font=(FONT, 14))
        self.reset_button.grid(row=0, column=1, padx=5)
        self.to_enable_disable.append(self.reset_button)

        # Reset Button
        self.quit_button = tk.Button(self.gen_reset_buttons_frame, text="Quit", command=self.quit_app, font=(FONT, 14))
        self.quit_button.grid(row=0, column=2, padx=5)


        # Create a Matplotlib figure with increased size
        self.figure, self.ax = plt.subplots(figsize=(10, 6))  # Width: 10 inches, Height: 6 inches
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.frame_plot)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.ax.axes.get_xaxis().set_visible(False)
        self.ax.axes.get_yaxis().set_visible(False)

        # To store source names and observing times
        self.entries = []

        # Bind the "Q" key to quit the app
        self.root.bind("<q>", self.quit_app)

        # Bind the "Q" key to delete the selected entry
        self.root.bind("<d>", self.remove_entry)

        # Bind the "BackSpace" key to delete the selected entry
        self.root.bind("<BackSpace>", self.remove_entry)

        # Initialize dragging variables
        self.dragging = False
        self.dragged_index = None

        # Bind mouse events for dragging
        self.entry_listbox.bind("<Button-1>", self.on_click)
        self.entry_listbox.bind("<B1-Motion>", self.on_drag)
        self.entry_listbox.bind("<ButtonRelease-1>", self.on_release)

        # Bind the "Escape" key to reset the selection
        self.root.bind("<Escape>", self.reset_selection)

        # Make sure to destroy when exiting
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)


    def show_help(self):
        """Display a larger Help dialog with scrollable content."""
        help_window = tk.Toplevel(self.root)
        help_window.title("Help - How to Use")
        help_window.geometry("1000x400")  # Set size for larger window

        # Create a text widget for the help content
        help_text_widget = tk.Text(help_window, wrap="word", font=(FONT, 12), padx=10, pady=10)
        help_text_widget.pack(expand=True, fill=tk.BOTH)

        help_text = (
            "How to Use the Application:\n\n"
            "1. Select a timezone from the dropdown menu.\n"
            "2. Select the start date and time.\n"
            "3. Enter source names and expected observation times.\n"
            "4. Use the 'Generate Plot' button to generate a graph for tracks of the input sources.\n"
            "4. You can reset all inputs by pressing the 'Reset All' button.\n"
            "5. Check the listbox to manage and add new sources or observing times.\n\n"
            "Notes:\n\n"
            "- 'Observation overhead' attempts to simulate the time taken for setting frequencies, RF/IF gain setting, and backend overhead.\n"
            f"- 'Slew time' assumes a slew rate of {SLEW_RATE} deg/s for the telescope.\n"
            "- You can input custom RADEC pairs by inputing a source with format:\n"
            "  'RADECXX.XX,+/-YY.YY' where 'XX.XX' is in decimal hour, and '+/-YY.YY' is in decimal degree"
        )
        help_text_widget.insert(tk.END, help_text)
        help_text_widget.config(state=tk.DISABLED)  # Disable editing of the help content

        # Add a scrollbar to the help text
        scrollbar = tk.Scrollbar(help_text_widget)
        help_text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=help_text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # OK button to close the window
        ok_button = tk.Button(help_window, text="OK", command=help_window.destroy,
                font=(FONT, 12))
        ok_button.pack(pady=10)


    def show_about(self):
        """Display an About dialog."""
        about_text = (
            "ATA Observation planner\n"
            "Version: 1.0\n\n"
            "This application allows you to generate tracks of sources and manage observing plans.\n"
            "Developed by: Wael Farah"
        )
        messagebox.showinfo("About", about_text)

    def quit_app(self, event=None):
        """Close the application."""
        #self.root.quit()
        self.root.destroy()  # Destroy the main window

    def remove_entry(self, event=None):
        """Removes selected entries from the listbox."""
        selected_indices = list(self.entry_listbox.curselection())  # Get selected indices
        
        # Remove selected entries in reverse order to maintain indices
        for index in reversed(selected_indices):
            self.entry_listbox.delete(index)

    def add_entry(self):
        """Adds a source name and observing time to the list."""
        source_name = self.source_name_entry.get()
        observing_time = self.observing_time_entry.get()

        if source_name and observing_time:
            entry = f"{source_name}, {observing_time} sec"
            self.entries.append(entry)

            # Update the listbox with the new entry
            self.entry_listbox.insert(tk.END, entry)

            # Clear the input fields after adding
            self.source_name_entry.delete(0, tk.END)
            self.observing_time_entry.delete(0, tk.END)

    def duplicate_entry(self):
        """Duplicates the selected entries in the listbox."""
        selected_indices = self.entry_listbox.curselection()
        
        if selected_indices:  # Check if any entries are selected
            for index in selected_indices:
                selected_entry = self.entry_listbox.get(index)
                # Insert the duplicated entry at the end
                self.entry_listbox.insert(tk.END, selected_entry)
        else:
            print("No entry selected to duplicate.")

    def on_timezone_selected(self, event):
        # Get the selected timezone from the combobox
        selected_timezone = self.timezone_combobox.get()

        # reset time for given timezone
        dt_now = datetime.datetime.now(
                tz=pytz.timezone(self.timezone_combobox.get()))
        hh_now, mm_now = dt_now.hour, dt_now.minute

        self.hours_spin.delete(0, tk.END)
        self.hours_spin.insert(0, f'{hh_now:02}')
        self.minutes_spin.delete(0, tk.END)
        self.minutes_spin.insert(0, f'{mm_now:02}')

    def reset_selection(self, event=None):
        """Reset the selection of the listbox."""
        self.entry_listbox.selection_clear(0, tk.END)  # Clear selection

    def on_click(self, event):
        """Handle mouse click on the listbox."""
        self.dragging = True
        self.dragged_index = self.entry_listbox.nearest(event.y)  # Get the index of the clicked item

    def on_drag(self, event):
        """Handle dragging of listbox items."""
        if self.dragging:
            current_index = self.entry_listbox.nearest(event.y)  # Get the index of the item currently under the mouse
            if current_index != self.dragged_index:
                # Move the item if the indices are different
                item_text = self.entry_listbox.get(self.dragged_index)
                self.entry_listbox.delete(self.dragged_index)
                self.entry_listbox.insert(current_index, item_text)
                self.dragged_index = current_index  # Update the index of the dragged item

    def on_release(self, event):
        """Handle mouse release to stop dragging."""
        self.dragging = False
        self.dragged_index = None  # Reset the dragged index

    def display_all_entries(self):
        """Displays all entries in the listbox."""
        all_entries = self.entry_listbox.get(0, tk.END)  # Get all entries
        print("All entries in the listbox:")
        for entry in all_entries:
            print(entry)

    def generate_plot(self, obs_plan=None):
        #self.save_to_json()
        if len(self.entry_listbox.get(0, tk.END)) == 0:
            return
        self.clear_error()
        self.root.config(cursor="watch")
        self.root.update()

        # Clear the previous plot
        self.ax.clear()
        self.ax.axes.get_xaxis().set_visible(True)
        self.ax.axes.get_yaxis().set_visible(True)

        # Get user input
        date_selected = self.date_entry.get()
        hours = int(self.hours_spin.get())
        minutes = int(self.minutes_spin.get())
        time_selected = hours + minutes / 60.0

        # Temporary default title
        default_title = f"Plot generated on {date_selected} at {hours:02}:{minutes:02}"

        start_time = datetime.datetime.strptime(
                f"{date_selected} {hours:02}:{minutes:02}", "%m/%d/%y %H:%M")
        selected_tz = pytz.timezone(self.timezone_combobox.get())

        localized_time = selected_tz.localize(start_time)

        start_time = Time(localized_time)

        # I'm already given the ObsPlan 
        if obs_plan:
            obs = obs_plan

        # Create the obs plan from the graph
        else:
            obs = ObsPlan(start_time, self.obs_overhead_var.get(),
                    self.slew_time_var.get())

            # Cycle through all the entries:
            for entry in self.entry_listbox.get(0, tk.END):
                res = parse('{source_name}, {observing_time} sec', entry)
                source_name = res['source_name']
                try:
                    obs_time = int(res['observing_time'])
                except ValueError as e:
                    self.display_error("Input correct obstime for source %s" %source_name)
                    self.root.config(cursor="")
                    self.root.update()
                    raise
                try:
                    obs.add_obs_block(source_name, obs_time)
                except Exception as e:
                    self.root.config(cursor="")
                    self.root.update()
                    self.display_error(str(e))
                    raise


        obs_tracks = []

        t_all = (obs.time_incr - obs.start_time).to_value(u.second)
        obs_times = obs.start_time + t_all * np.linspace(-0.05, 1.05, 500) * u.second
        obs_times_pdate = obs_times.to_value("plot_date")

        unique_sources = list(set(i['object'] for i in obs.obs_plan))
        color_cycler = {}
        tracks = {}

        try:
            # loop through sources to plot the tracks
            for isource, source in enumerate(unique_sources):
                if source.lower().startswith("radec"):
                    source_info = obs.parse_radec(source)
                else:
                    source_info = check.check_source(source)
                ra = source_info['ra']
                dec = source_info['dec']
                source_coords = ICRS(ra=ra*u.hour, dec=dec*u.deg)
                target = SkyCoord(source_coords)

                altaz = target.transform_to(AltAz(obstime=obs_times, location=OBSERVING_LOCATION))
                tracks[source_info['object']] = altaz.alt

                #plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=10))
                #plt.plot(days,y)
                self.ax.plot(obs_times_pdate, altaz.alt, label=source_info['object'])
                color_cycler[source_info['object']] = COLOR_CYCLER_LIST[isource]['color']

            # plot the start and end times, and the overhead fill
            if self.obs_overhead_var.get() or self.slew_time_var.get():
                sdate = obs.start_time.to_value("plot_date")
                edate = obs.time_incr.to_value("plot_date")
                self.ax.axvline(x = sdate, color = 'black', linestyle = ':', alpha=1)
                self.ax.axvline(x = edate, color = 'black', linestyle = ':', alpha=1)

                obs_block0 = obs.obs_plan[0]
                sdate_obs0 = obs_block0['start_time'].to_value("plot_date")
                self.ax.fill_betweenx([0,90], sdate_obs0, sdate, hatch="//", alpha=0,
                        label="overhead + slew")
                edate_obs0 = obs_block0['end_time'].to_value("plot_date")

                for obs_block in obs.obs_plan[1:]:
                    sdate = obs_block['start_time'].to_value("plot_date")
                    self.ax.fill_betweenx([0,90], edate_obs0, sdate, hatch="//", alpha=0)
                    edate_obs0 = obs_block['end_time'].to_value("plot_date")

            self.error_in_plan = self.PLAN_OK

            set_list = []

            # now loop through the observing plan
            for obs_block in obs.obs_plan:
                source_name = obs_block['object']
                color = color_cycler[source_name]
                sdate = obs_block['start_time'].to_value("plot_date")
                edate = obs_block['end_time'].to_value("plot_date")
                self.ax.fill_betweenx([0,90], edate, sdate, color = color, alpha=0.5)
                self.ax.axvline(x = sdate, color = 'black', linestyle = ':', alpha=1)
                self.ax.axvline(x = edate, color = 'black', linestyle = ':', alpha=1)

                el_track = tracks[source_name]

                el_track_seg = el_track[(obs_times_pdate >= sdate) & (obs_times_pdate <= edate)]
                el_track_seg = el_track_seg.deg

                # if any source has set
                if np.any(el_track_seg <= HARD_EL_LIM):
                    self.error_in_plan = self.PLAN_ERROR
                    label = f"{source_name} is set!"
                    if label not in set_list:
                        set_list.append(label)
                    else:
                        label=""
                    self.ax.fill_betweenx([0,HARD_EL_LIM], edate, sdate, color = 'red', alpha=1,
                                          hatch="X", edgecolor="black", label=label)
                elif np.any(el_track_seg <= SOFT_EL_LIM):
                    if self.error_in_plan != self.PLAN_ERROR:
                        self.error_in_plan = self.PLAN_WARNING
                    self.ax.fill_betweenx([0,SOFT_EL_LIM], edate, sdate, color = 'orange', alpha=1,
                            hatch="X", edgecolor="black")

            self.ax.legend(fontsize=18)
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d:%H:%M'))
            self.figure.autofmt_xdate()

            if self.error_in_plan == self.PLAN_ERROR:
                self.ax.set_title("CHECK PLAN - SOURCE[S] BELOW HORIZON", color='red')
            elif self.error_in_plan == self.PLAN_WARNING:
                self.ax.set_title("Check plan - source[s] can get below horizon", color='orange')
            else:
                self.ax.set_title("No errors in plan", color='green')

            self.ax.axhline(y = HARD_EL_LIM, color = 'r', linestyle = '--') 
            self.ax.axhline(y = SOFT_EL_LIM, color='orange', linestyle='--')
            self.ax.grid(alpha=0.5)

            # plot start date
            self.ax.axvline(x = obs.start_time.to_value("plot_date"),
                    color = 'black', alpha=1)
            
            self.ax.set_ylim([-0, 90])

            self.ax.set_ylabel("Elevation [deg]")
            self.ax.set_xlabel("Time [UTC]")

            self.canvas.draw()

        except Exception as e:
            print("Error:", e)

        self.root.config(cursor="")
        self.root.update()

    def plan_has_error(self):
        if self.error_in_plan != None:
            if self.error_in_plan == self.PLAN_ERROR:
                return True
        return False

    def plan_has_warning(self):
        if self.error_in_plan != None:
            if self.error_in_plan == self.PLAN_WARNING:
                return True
        return False

    def plan_is_ok(self):
        if self.error_in_plan != None:
            if self.error_in_plan == self.PLAN_OK:
                return True
        return False

    def register_selection(self, event=None):
        """Method to register the combobox selection when Enter is pressed or focus is lost."""
        selected_value = self.timezone_combobox.get()
        self.timezone_combobox.set(selected_value)
        # Update feedback label with the selected value
        #self.feedback_label.config(text=f"Selected Timezone: {selected_value}")

    def reset_all(self):
        """Resets all input fields and clears the listbox."""
        # Reset Date and Time fields
        self.date_entry.set_date(self.date_entry._date.today())

        # Reset timezone
        self.timezone_combobox.set(DEFAULT_TIMEZONE)

        # Get time now to fill in defaults
        dt_now = datetime.datetime.now(
                tz=pytz.timezone(self.timezone_combobox.get()))
        hh_now, mm_now = dt_now.hour, dt_now.minute

        self.hours_spin.delete(0, tk.END)
        self.hours_spin.insert(0, f'{hh_now:02}')
        self.minutes_spin.delete(0, tk.END)
        self.minutes_spin.insert(0, f'{mm_now:02}')

        # Reset Source Name and Observing Time fields
        self.source_name_entry.delete(0, tk.END)
        self.observing_time_entry.delete(0, tk.END)

        # Clear the Listbox and reset entries
        self.entry_listbox.delete(0, tk.END)
        self.entries.clear()

        # Clear the plot
        self.ax.clear()
        self.ax.axes.get_xaxis().set_visible(False)
        self.ax.axes.get_yaxis().set_visible(False)
        self.canvas.draw()

        # Clear any errors
        self.clear_error()

        # Check all the overhead
        self.obs_overhead_check.select()
        self.slew_time_check.select()

    def disable_everything(self):
        self.root.update()
        for button in self.to_enable_disable:
            button.config(state=tk.DISABLED)
        self.root.update()

    def enable_eveything(self):
        self.root.update()
        for button in self.to_enable_disable:
            button.config(state=tk.NORMAL)
        self.root.update()

    def display_error(self, message):
        """Display an error message in the error label."""
        self.error_label.config(text=message)

    def clear_error(self):
        """Clear the error message."""
        self.error_label.config(text="")

    def save_to_json(self):
        # Get the selected date
        selected_date = self.date_entry.get()

        # Get the selected time (hours and minutes)
        selected_hours = self.hours_spin.get()
        selected_minutes = self.minutes_spin.get()

        # Get the timezone
        selected_timezone = self.timezone_combobox.get()

        # Check the state of the "Initial Overhead" and "Slew Time" checkboxes
        overhead_toggled = self.obs_overhead_var.get()  # 1 if checked, 0 if unchecked
        slew_time_toggled = self.slew_time_var.get()  # 1 if checked, 0 if unchecked

        # Get all the sources in the listbox
        sources = self.entry_listbox.get(0, tk.END)  # Get all the items in the listbox

        # Create a dictionary with all the information
        data = {
            "start_date": selected_date,
            "start_time": f"{selected_hours}:{selected_minutes}",
            "timezone": selected_timezone,
            "initial_overhead": bool(overhead_toggled),
            "slew_time": bool(slew_time_toggled),
            "sources": list(sources)
        }

        # Save to a JSON file
        filename = f"session_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        
        print(f"Data saved to {filename}")

    def load_from_obsplan(self, obsplan):
        # Set the checkbox values
        self.obs_overhead_var.set(1)  # 1 or 0
        self.slew_time_var.set(1)

        dt_now = datetime.datetime.now(
                tz=pytz.timezone(DEFAULT_TIMEZONE))

        # Set the start time in the Spinboxes for hours and minutes
        #hours, minutes = map(int, data['start_time'].split(':'))
        hours, minutes = dt_now.hour, dt_now.minute
        self.hours_spin.delete(0, tk.END)
        self.hours_spin.insert(0, hours)
        self.minutes_spin.delete(0, tk.END)
        self.minutes_spin.insert(0, minutes)

        # Clear the listbox and add the saved sources
        self.entry_listbox.delete(0, tk.END)
        for source_info in obsplan.obs_plan:
            name = source_info['object']
            tobs = str(source_info['duration'])
            source = f"{name}, {tobs} sec"
            self.entry_listbox.insert(tk.END, source)


        self.disable_everything()
        self.generate_button.config(state=tk.NORMAL)
        self.root.update()
        try:
            self.generate_plot(obsplan)
        except Exception as e:
            messagebox.showerror("Error: ", f"{e}")


    def load_from_json(self, filename=None):
        if filename:
            self.loaded_data_externally = True
        else:
            self.loaded_data_externally = False
        # Open the JSON file
        try:
            if not self.loaded_data_externally:
                filename = tk.filedialog.askopenfilename(
                    title="Select JSON File",
                    filetypes=(("JSON files", "*.json"), ("All files", "*.*")))#, 
                if not filename:
                    return  # User cancelled the file selection

            with open(filename, 'r') as json_file:
                data = json.load(json_file)

            # Populate the widgets with the loaded data

            # Set the start date in the DateEntry widget
            #self.date_entry.set_date(data['start_date'])
            dt_now = datetime.datetime.now(
                    tz=pytz.timezone(DEFAULT_TIMEZONE))

            # Set the start time in the Spinboxes for hours and minutes
            #hours, minutes = map(int, data['start_time'].split(':'))
            hours, minutes = dt_now.hour, dt_now.minute
            self.hours_spin.delete(0, tk.END)
            self.hours_spin.insert(0, hours)
            self.minutes_spin.delete(0, tk.END)
            self.minutes_spin.insert(0, minutes)

            # Set the timezone in the Combobox
            if data['timezone'] in self.timezone_combobox['values']:
                self.timezone_combobox.set(data['timezone'])
            else:
                messagebox.showwarning("Timezone Warning", f"Timezone '{data['timezone']}' not found!")

            # Set the checkbox values
            self.obs_overhead_var.set(int(data['initial_overhead']))  # 1 or 0
            self.slew_time_var.set(int(data['slew_time']))

            # Clear the listbox and add the saved sources
            self.entry_listbox.delete(0, tk.END)
            for source in data['sources']:
                self.entry_listbox.insert(tk.END, source)

            #messagebox.showinfo("Success", "Data loaded successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")

        if self.loaded_data_externally:
            self.disable_everything()
            self.generate_button.config(state=tk.NORMAL)
            self.root.update()
            try:
                self.generate_plot()
            except Exception as e:
                messagebox.showerror("Error: ", f"{e}")
