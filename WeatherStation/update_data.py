'''
Get the WS sensor data from telnet connections.
'''

from telnetlib import Telnet
import atexit
import warnings
from time import localtime, strftime, time

class TelnetLink():
    ''' Telnet link to one weather station.'''

    def __init__(self, host, port,link_name):
        '''Initialize the telnet connection with the host and port information'''

        self.host = host
        self.port = port
        self.link_name = link_name # WS1 or WS2 to add prefix to parsed variables
        self.tn = Telnet()
        self.tn.open(self.host, self.port) # Open telnet connection
        self.tries_before_restart = 3 # 1 minute of parsing errors triggers first telent restart
        self.last_weather_update_display_time = 'n/a'
        self.last_weather_update_unix_time = 0 # Number of seconds since 1970
                                               # time set at first weather data successful parsing
        atexit.register(self.tn.close) # Be sure to close telnet connection if the program exits


    def read_values(self):
        '''
        Read next set of raw data from telnet connection, parse them in a dictionnary
        with readable variable names from 'var_name_dict'.

        Output:
        parsed_values: python dictionnary with parsed values
        '''

        self.tn.read_until(b"0r1,") # Remove what's before
        telnet_data = self.tn.read_until(b"0r1,") # Read one block of telnet data


        # Transform the telnet byte string to a python list
        raw_values = telnet_data.decode().split(',')

        # Data to extract and length of WS data unit to remove.
        # Format: (Name in telnet, charcter length of unit)
        # See variable definition below in 'var_name_dict'
        vars_to_parse_tab = (
            ('Dn=', 1),
            ('Dm=', 1),
            ('Dx=', 1),
            ('Sn=', 1),
            ('Sm=', 1),
            ('Sx=', 9),
            ('Ta=', 1),
            ('Ua=', 1),
            ('Pa=', 9),
            ('Th=', 1),
            ('Vh=', 1),
            ('Vs=', 1),
            ('Vr=', 1),
            ('Id=', 8),
            ('Rc=', 1),
            ('Rd=', 1),
            ('Ri=', 1),
            ('Hc=', 1),
            ('Hd=', 1),
            ('Hi=', 0)
        )

        # Transform to human readable variable names, def in Vaisala WXT530 user guide
        var_name_dict = {
            'Dn': 'WindDirMin', # Minimum wind direction [degrees]
            'Dm': 'WindDirAvg', # Average
            'Dx': 'WindDirMax',
            'Sn': 'WindSpeedMin', # Minimum wind speed [m/s]
            'Sm': 'WindSpeedAvg',
            'Sx': 'WindSpeedMax',
            'Ta': 'AirTemp', # Air temperature [C]
            'Ua': 'RelHumidity', # Relative humidity [%]
            'Pa': 'AirPressure', # Air pressure [hPa]
            'Th': 'HeatingTemp', # [C] 
            'Vh': 'HeatingVoltage', # (N = heating is off) TODO: handle this case
            'Vs': 'SupplyVoltage', # [V]
            'Vr': 'refVoltage', # 3.5V reference voltage
            'Id': 'id', # information field, 'Primary' or 'Secondary'
            'Rc': 'RainAccu', # Rain accumulation [mm]
            'Rd': 'RainDur', # Rain duration [s]
            'Ri': 'RainIntens', # Rain intensity [mm/h]
            'Hc': 'HailAccu', # Hail accumulation [hits/cm^2]
            'Hd': 'HailDur', # Hail duration [s]
            'Hi': 'HailIntens', # Hail intensity [hits/cm^2 h]
        }

        parsed_values = {}
        couldnt_parse = '' # To display variables that failed to parse

        for idx, var_to_parse in enumerate(vars_to_parse_tab):

            # Construct readable variable name
            translated_name = var_name_dict[var_to_parse[0][:-1]]
            var_name = f"{self.link_name}_{translated_name}"

            # Look if we find matching variable to extract, independent of telnet receiving order
            raw_data = [x for x in raw_values if x.startswith(var_to_parse[0])]

            # We found exactly variable match in our telnet data
            if len(raw_data) == 1:
                # Create result directory entery
                raw_data_str = raw_data[0]
                # Removing variable name and unit from raw string
                rdata_value = raw_data_str[len(var_to_parse[0]):-var_to_parse[1]]
                # Add parsed value to dictionary
                parsed_values[var_name] = rdata_value

            # Couldn't find the variable in the table
            else:
                couldnt_parse += f'{var_to_parse[0][:-1]}, '
                parsed_values[var_name] = 'n/a'

        current_display_time = strftime("%m/%d %H:%M", localtime())
        if couldnt_parse != '': # Parsing of at least one WS value failed
            warnings.warn(f"Warning: Parsing failed for vaules: {couldnt_parse}")
            self.tries_before_restart -= 1
            parse_warning = f"{current_display_time} Warning: No weather station data. \n \
                Restarting Telnet connection in {int(self.tries_before_restart) * 20}s \
                if problem isn't solved."
            warnings.warn(parse_warning)
            if self.tries_before_restart <= 0:
                warnings.warn(f"{current_display_time} Warning: \
                    Restarting {self.host}:{self.port} telnet connection.")
                self.tries_before_restart = 15 # Wait 5 minutes before next restart
                self.restart_connection()
        else: # Parsing successful
            self.last_weather_update_display_time = current_display_time
            current_unix_time = time()
            self.last_weather_update_unix_time = current_unix_time

            if self.tries_before_restart > 3:
                # Connection reset happened but works fine now
                # We want to slowly go back to 1 minute restart buffer
                self.tries_before_restart -=1
        parsed_values[f'{self.link_name}_update_display_time'] = self.last_weather_update_display_time
        parsed_values[f'{self.link_name}_update_unix_time'] = self.last_weather_update_unix_time
        return parsed_values


    def restart_connection(self):
        ''' Close and re-open telnet link. '''

        self.tn.close()
        self.tn = Telnet()
        self.tn.open(self.host, self.port)
