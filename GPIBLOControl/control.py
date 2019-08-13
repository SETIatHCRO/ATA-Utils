import numpy,re,socket



class PrologixGPIBEthernet:
    PORT=1234

    def __init__(self, host, timeout=3):
        self.host = host
        self.timeout = timeout
        self.socket = socket.socket(socket.AF_INET,
                                    socket.SOCK_STREAM,
                                    socket.IPPROTO_TCP)
        self.socket.settimeout(self.timeout)

    def connect(self):
        self.socket.connect((self.host, self.PORT))

        self._setup()
        return True

    def close(self):
        self.socket.close()
        return True

    def select(self, addr):
        self._send('++addr %i' % int(addr))

    def write(self, cmd):
        self._send(cmd)

    def read(self, num_bytes=1024):
        self._send('++read eoi')
        return self._recv(num_bytes)

    def query(self, cmd, buffer_size=1024*1024):
        self.write(cmd)
        return self.read(buffer_size)

    def _send(self, value):
        encoded_value = ('%s\n' % value).encode('ascii')
        self.socket.send(encoded_value)

    def _recv(self, byte_num):
        value = self.socket.recv(byte_num)
        return value.decode('ascii')

    def _setup(self):
        # set device to CONTROLLER mode
        self._send('++mode 1')

        # disable read after write
        self._send('++auto 0')

        # set GPIB timeout
        self._send('++read_tmo_ms %i' % int(self.timeout*1e3))

        # do not require CR or LF appended to GPIB data
        self._send('++eos 3')


class defaultVals:
    """Default frequency in Hz"""
    defFreq = 14.9e9
    """Default power in dBm"""
    defPow = 13 

class control():
    """This class implements the methods to control the Cryocon temperature controller"""
    def __init__(self):
        ''' Constructor for this class. '''
        self.__adapter = 0

    def __del__(self):
        ''' Destructor for this class. '''
        if self.__is_open:
            self.close()


    def open(self, ip='lo2.hcro.org', gpib=30):
        """ Open connection to GPIB adapter and creates a socket
                :param ip: IP address/host name of the GPIB adapter. Default='lo2.hcro.org'
                :param gpib: GPIB address of the generator. Default=30
                :returns Boolean value True or False """
        self.__adapter = PrologixGPIBEthernet(ip)
        self.__gpib = gpib
        self.__is_open = self.__adapter.connect()
        return self.__is_open

    def close(self):
        """ Close socket """
        self.__adapter.close()

    def reset_device(self):
        """ Reset the device to default settings.
            It is HIGHLY recommended to reset it for the first use"""
        try:
            self.__adapter.select(self.__gpib)
            self.__adapter.write('*RST')
            self.__adapter.write('*CLS')
            self.__adapter.write('OUTP OFF')
        except:
             print"ERROR no communication possible, check if the connection has been opened with open()"   

    def get_error(self):
        """ Get lastest error message
            :returns unicode: error code
            :returns unicode: error message"""
        try:
            self.__adapter.select(self.__gpib)
            devresp = self.__adapter.query('SYST:ERR?')
            resp=re.split(',',devresp)
            error_code= int(resp[0])
            error_message = ','.join(resp[0:])
            return error_code,error_message

        except:
            print"ERROR no communication possible, check if the connection has been opened with open(). Or device did not send a reply!!!"

    def is_transmitting(self):
        """Get information if device is transmitting
            :returns bool: device output status"""
        
        try:
            self.__adapter.select(self.__gpib)
            return bool(int(self.__adapter.query('OUTP?')))

        except:
            print"ERROR no communication possible, check if the connection has been opened with open(). Or device did not send a reply!!!"


    def send_query(self,cmd):
        """ Send query to the GPIB device
                :param cmd: string which gets send to device'
                :returns unicode: response of device """
        try:
            self.__adapter.select(self.__gpib)
            return self.__adapter.query(cmd)

        except:
            print"ERROR no communication possible, check if the connection has been opened with open(). Or device did not send a reply!!!"

    def send_command(self,cmd,wait=True):
        """ Send command to the GPIB device
                :param cmd: string which gets send to device'
                :param wait: bool to indicate if function should wait for the device, default=True
                :returns unicode: string 1 on success """
        try:
            self.__adapter.select(self.__gpib)
            self.__adapter.write(cmd)
            if wait:
                retval = self.__adapter.query('*OPC?')
            else:
                retval = '1'
            return retval

        except:
            print"ERROR no communication possible, check if the connection has been opened with open(). Or device did not send a reply!!!"

    def set_defaults(self):
        """ Set the default values of frequency and power"""
        try:
            self.__adapter.select(self.__gpib)
            self.__adapter.write(':FREQ ' + str(defaultVals.defFreq))
            self.__adapter.write(':POW ' + str(defaultVals.defPow) + ' dBm')
        except:
            print"ERROR no communication possible, check if the connection has been opened with open()"

    def output_on(self,wait=True):
        """Enable transmission 
            :param wait: should function wait for setting up, default=True
            :returns unicode: string 1 on success """
        
        try:
            self.__adapter.select(self.__gpib)
            self.__adapter.write(':OUTP ON')
            
            if wait:
                retval = self.__adapter.query('*OPC?')
            else:
                retval = '1'
                
            return retval

        except:
            print"ERROR no communication possible, check if the connection has been opened with open(). Or device did not send a reply!!!"

    def output_off(self,wait=True):
        """Disable transmission 
            :param wait: should function wait for setting up, default=True
            :returns unicode: string 1 on success """
        
        try:
            self.__adapter.select(self.__gpib)
            self.__adapter.write(':OUTP OFF')
            
            if wait:
                retval = self.__adapter.query('*OPC?')
            else:
                retval = '1'
                
            return retval
        
        except:
            print"ERROR no communication possible, check if the connection has been opened with open(). Or device did not send a reply!!!"

    def set_frequency(self,freq=defaultVals.defFreq,wait=True):
        """Set the frequency of the LO (and forces power to default)
            :param freq: frequency to set up (float), default is control.defaultVals.defFreq
            :param wait: should function wait for setting up, default=True
            :returns unicode: string 1 on success """
        
        try:
            self.__adapter.select(self.__gpib)
            self.__adapter.write(':FREQ ' + str(freq))
            self.__adapter.write(':POW ' + str(defaultVals.defPow) + ' dBm')
            
            if wait:
                retval = self.__adapter.query('*OPC?')
            else:
                retval = '1'
                
            return retval
        
        except:
            print"ERROR no communication possible, check if the connection has been opened with open(). Or device did not send a reply!!!"

    def get_frequency(self):
        """Asks the device about current frequency
            :returns float: current frequency"""
        
        try:
            self.__adapter.select(self.__gpib)
            retfreq = self.__adapter.query(':FREQ?')
            #print retfreq
            return float(retfreq)

        except:
            print"ERROR no communication possible, check if the connection has been opened with open(). Or device did not send a reply!!!"
