'''
Get the WS sensor data from telnet connections.
'''

from telnetlib import Telnet
import atexit


class TelnetLink():
    ''' Telnet link to one weather station.'''

    def __init__(self, host, port,link_name):
        '''Initialize the telnet connection with the host and port information'''

        self.host = host
        self.port = port
        self.link_name = link_name # WS1 or WS2 to add prefix to parsed variables
        self.tn = Telnet()
        self.tn.open(self.host, self.port) # Open telnet connection
        atexit.register(self.tn.close) # Be sure to close telnet connection if the program exits


    def read_values(self):
        '''
        Read next set of raw data from telnet connection, parse them in a dictionnary
        with readable variable names from 'var_name_dict'.

        Output:
        parsed_values_dict: python dictionnary with parsed values
        '''

        self.tn.read_until(b"0r1,") # Remove what's before
        line1 = self.tn.read_until(b"0r2,") #0r1 line
        line2 = self.tn.read_until(b"0r5,") #0r2 line
        line3 = self.tn.read_until(b"0r3,") #0r5 line
        line4 = self.tn.read_until(b"0r1,") #0r3 line

        # Transform the telnet strings to a python 2d list for each line and each variable

        # TODO: Put everything on one line to avoid all the 'for' loops
        # Then don't read line by line: replace '\n' by ','
        table_raw_values = [
            line1.decode().split(','),
            line2.decode().split(','),
            line3.decode().split(','),
            line4.decode().split(',')
        ]

        # Data to extract and length of WS data unit to remove.
        vars_to_extract_tab = ( # format: (Name in telnet, charcter length of unit)
            (('Dn=', 1), ('Dm=', 1), ('Dx=', 1), ('Sn=', 1), ('Sm=', 1), ('Sx=', 9)), #0r1 line
            (('Ta=', 1), ('Ua=', 1), ('Pa=', 9)), # 0r2 line
            (('Th=', 1), ('Vh=', 1), ('Vs=', 1), ('Vr=', 1),('Id=',-1)), # 0r5 line
            (('Rc=', 1), ('Rd=', 1), ('Ri=', 1), ('Hc=', 1),('Hd=', 1), ('Hi=', 0)), # 0r3 line
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

        parsed_values_dict = {}
        # Line by line (telnet output)
        for idx_line, one_line_values in enumerate(vars_to_extract_tab):
            pcouldnt_parse = '' # To display variables that failed to parse
            current_raw_table_line = table_raw_values[idx_line] # One line of split telnet data

            for idx, var_to_extract in enumerate(one_line_values):
                # Look if we find matching variable to extract
                if current_raw_table_line[idx][:len(var_to_extract[0])] == var_to_extract[0]:
                    translated_name = var_name_dict[var_to_extract[0][:-1]]
                    var_name = f"{self.link_name}_{translated_name}"
                    # Create result directory entery
                    parsed_values_dict[var_name] = current_raw_table_line[idx][len(var_to_extract[0]):-var_to_extract[1]]

                else: # Couldn't find the WS variable in the table
                    pcouldnt_parse += f'{var_to_extract[0][:-1]}, '

            if pcouldnt_parse != '': # Parsing of at least one WS value failed
                # TODO: Handle the error? (e.g.: reset_connection?)
                print(f"Parsing failed for vaules: {pcouldnt_parse}")

        return parsed_values_dict


    def reset_connection(self):
        ''' Close and re-open telnet link. '''

        self.tn.close()
        self.tn = Telnet(self.host, self.port)
