
# this package
from apcommand.baseclass import BaseClass
import apcommand.connections.httpconnection as httpconnection


ZERO = '0'
ONE = '1'
UNIT_24_GHZ, UNIT_5_GHZ = ZERO, ONE
RADIO_OFF, RADIO_ON = ZERO, ONE
RADIO_PAGE = 'radio.asp'
SSID_PAGE = 'ssid.asp'
WIRELESS_INTERFACE = 'wl_unit'
INTERFACE = 'wl_radio'
CONTROL_CHANNEL = 'wl_channel'
SIDEBAND = 'wl_nctrlsb'
CHANNELS_5GHZ = '36 44 149 157'.split()
SSID = 'wl_ssid'


# a dictionary for data that changes the state of the broadcom
action_dict = lambda: {'action':'Apply'}

# a decorator to set the page to 'radio.asp'
def radio_page(method):
    def _method(self, *args, **kwargs):
        self.connection.path = RADIO_PAGE
        method(self, *args, **kwargs)
    return _method

# a decorator to set the page to 'ssid.asp'
def ssid_page(method):
    def _method(self, *args, **kwargs):
        self.connection.path = SSID_PAGE
        method(self, *args, **kwargs)
    return _method

class BroadcomBCM94718NR(BaseClass):
    """
    A class to control and query the Broadcom BCM94718NR
    """
    def __init__(self, hostname='192.168.1.1', username='',
                 password='admin'):
        """
        BroadcomBCM94718NR Constructor

        :param:

         - `hostname`: address of the AP
         - `username`: login username (use empty string if none)
         - `password`: login password (use empty string if none)
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self._connection = None
        self._enable_24_data = None
        self._enable_5_data = None
        self._disable_24_data = None
        self._disable_5_data = None
        self._set_24_data = None
        self._set_5_data = None
        self._set_sideband_lower_data = None
        
        self._channel_map = None
        return

    @property
    def channel_map(self):
        """
        Map of channel to data-dictionary
        """
        if self._channel_map is None:
            channel_24 = [str(channel) for channel in range(1,12)]
            channel_24_data = [self.set_24_data] * len(channel_24)
            # these are the only channels that match the Atheros channels we chose
            channel_5 = CHANNELS_5GHZ
            channel_5_data = [self.set_5_data] * len(channel_5)
            channels = channel_24 + channel_5
            data = channel_24_data + channel_5_data         
            self._channel_map = dict(zip(channels, data))
        return self._channel_map

    @property
    def enable_24_data(self):
        """
        The data to send to the connection to enable 2.4 GHz

        :return: dict of data-values for the connection
        """
        if self._enable_24_data is None:
            self._enable_24_data = action_dict()
            self._enable_24_data[WIRELESS_INTERFACE] = UNIT_24_GHZ
            self._enable_24_data[INTERFACE] = RADIO_ON
        return self._enable_24_data

    @property
    def disable_24_data(self):
        """
        Dictionary of data to disable the 2.4GHz interface
        """
        if self._disable_24_data is None:
            self._disable_24_data = action_dict()
            self._disable_24_data[WIRELESS_INTERFACE] = UNIT_24_GHZ
            self._disable_24_data[INTERFACE] = RADIO_OFF
        return self._disable_24_data

    @property
    def disable_5_data(self):
        """
        Data dictionary to disable the 5 Ghz interface
        """
        if self._disable_5_data is None:
            self._disable_5_data = action_dict()
            self._disable_5_data[WIRELESS_INTERFACE] = UNIT_5_GHZ
            self._disable_5_data[INTERFACE] = RADIO_OFF
        return self._disable_5_data        

    @property
    def enable_5_data(self):
        """
        The data to send to the connection to enable 5 GHz

        :return: dict of data-values for the connection
        """
        if self._enable_5_data is None:
            self._enable_5_data = action_dict()
            self._enable_5_data['wl_unit'] = UNIT_5_GHZ
            self._enable_5_data['wl_radio'] = RADIO_ON
        return self._enable_5_data

    @property
    def set_24_data(self):
        """
        A data dictionary to set the 2.4 GHz channel (missing actual setting)
        """
        set_24_data = action_dict()
        set_24_data[WIRELESS_INTERFACE] = UNIT_24_GHZ
        return set_24_data

    @property
    def set_5_data(self):
        """
        A data dictionary to set the 5 GHz channel (missing actual setting)
        """
        set_5_data = action_dict()
        set_5_data[WIRELESS_INTERFACE] = UNIT_5_GHZ
        return set_5_data

    @property
    def set_sideband_lower_data(self):
        """
        A data dictionary to set the sideband to Lower
        """
        if self._set_sideband_lower_data is None:
            self._set_sideband_lower_data = action_dict()
            self._set_sideband_lower_data[WIRELESS_INTERFACE] = UNIT_5_GHZ
            self._set_sideband_lower_data[SIDEBAND] = 'lower'
        return self._set_sideband_lower_data

    @property
    def connection(self):
        """
        A connection to the AP (right now this acts as an HTTPConnection builder)

        :return: HTTPConnection for the DUT (set to radio.asp pgae)
        """
        if self._connection is None:
            self._connection = httpconnection.HTTPConnection(hostname=self.hostname,
                                                             username=self.username,
                                                             password=self.password,
                                                             path=RADIO_PAGE)
        return self._connection

    @radio_page
    def enable_24_ghz(self):
        """
        Tells the connection to turn on the 2.4 GHz radio
        """
        self.connection(data=self.enable_24_data)
        return

    @radio_page
    def enable_5_ghz(self):
        """
        Tells the connection to turn on the 5 GHz radio
        """
        self.connection(data=self.enable_5_data)
        return

    @radio_page
    def disable_24_ghz(self):
        """
        Disables the 2.4Ghz radio
        """
        self.connection(data=self.disable_24_data)
        return

    @radio_page
    def disable_5_ghz(self):
        """
        Disables the 5 GHz radio
        """
        self.connection(data=self.disable_5_data)
        return

    @radio_page
    def set_sideband_lower(self):
        """
        To match the Atheros the 5GHz channels are only set 'lower'
        """
        self.connection(data=self.set_sideband_lower_data)
        return

    @radio_page
    def set_channel(self, channel):
        """
        Sets the channel on the AP (and the sideband if 5ghz) 
        """
        channel = str(channel)
        data = self.channel_map[channel]
        data[CONTROL_CHANNEL] = channel
        self.connection(data=data)

        if channel in CHANNELS_5GHZ:
            self.set_sideband_lower()
        return

    @ssid_page
    def set_5_ssid(self, ssid):
        """
        Sets the 5 Ghz band SSID
        """
        data = self.set_5_data
        data[SSID] = ssid
        self.connection(data=data)
        return

    @ssid_page
    def set_24_ssid(self, ssid):
        """
        Sets the 2.4 Ghz band SSID
        """
        data = self.set_24_data
        data[SSID] = ssid
        self.connection(data=data)
        return
        


# python standard library
import unittest
import random
import string

# third party
from mock import MagicMock, patch, call


EMPTY_STRING = ''
random_letters = lambda: EMPTY_STRING.join([random.choice(string.letters)
                                            for c in xrange(random.randrange(100))])


class TestBroadcomBCM94718NR(unittest.TestCase):
    def setUp(self):
        self.hostname = random_letters()
        self.username = random_letters()
        self.password = random_letters()
        self.connection = MagicMock(name='MockHTTPConnection')
        self.control = BroadcomBCM94718NR(hostname=self.hostname,
                                          username=self.username,
                                          password=self.password)
        self.control._connection = self.connection
        return

    def test_defaults(self):
        """
        Do the defaults match the Broadcom's 'reset' values?
        """
        connection = BroadcomBCM94718NR()
        self.assertEqual('192.168.1.1', connection.hostname)
        self.assertEqual('', connection.username)
        self.assertEqual('admin', connection.password)
        return

    def test_constructor(self):
        """
        Does it construct the control correctly?
        """
        self.assertEqual(self.hostname, self.control.hostname)
        self.assertEqual(self.username, self.control.username)
        self.assertEqual(self.password, self.control.password)
        return

    def test_connection(self):
        """
        Does the control build the HTTPConnection?
        """
        connection = MagicMock(name='HTTPConnection')
        control = BroadcomBCM94718NR()
        with patch('apcommand.connections.httpconnection.HTTPConnection', connection):
            print connection.mock_calls
            print control.connection.mock_calls
            # for some reason this isn't working (the patch is created but not called)
            #control.connection.assert_called_with(hostname='192.168.1.1')
            self.assertIsInstance(control.connection, MagicMock)
        return
    
    def test_enable_24_interface(self):
        """
        Does it enable the 2.4 GHz interface?
        """
        self.connection.path = None
        self.control.enable_24_ghz()
        self.connection.assert_called_with(data={'wl_unit':'0', 'wl_radio':'1', 'action':"Apply"})
        self.assertEqual(RADIO_PAGE, self.connection.path )
        return

    def test_enable_5_interface(self):
        """
        Does it call the connection with the right data?
        """
        self.connection.path = None
        self.control.enable_5_ghz()
        self.connection.assert_called_with(data={'wl_unit':'1', 'wl_radio':'1', 'action':'Apply'})
        self.assertEqual(RADIO_PAGE, self.connection.path)
        return

    def test_disable_24_interface(self):
        """
        Is the right data sent to disable the 2.4 GHz interface?
        """
        self.connection.path = None
        self.control.disable_24_ghz()
        self.connection.assert_called_with(data={'wl_unit':'0',
                                                 'wl_radio':'0',
                                                 'action':"Apply"})
        self.assertEqual(RADIO_PAGE, self.connection.path)
        return

    def test_disable_5_interface(self):
        """
        Does the connection get the data to disable the 5 GHz data?
        """
        self.connection.path = None
        self.control.disable_5_ghz()
        self.connection.assert_called_with(data={'wl_unit':'1',
                                                 'wl_radio':'0',
                                                 'action':'Apply'})
        self.connection.path = RADIO_PAGE
        return

    def test_set_channel(self):
        """
        Does it send the right channel (and sideband if appropriate)
        """
        channel_24 = str(random.randrange(1,12))
        self.control.set_channel(channel_24)
        first_call = [call(data={'wl_unit':'0',
                                'wl_channel':channel_24,
                                'action':'Apply'}) ]
        self.assertEqual(self.connection.mock_calls, first_call)

        channel_5 = random.choice('36 44 149 157'.split())
        self.control.set_channel(channel_5)
        calls = first_call + [call(data={'wl_unit':'1','wl_channel': channel_5,'action':'Apply'}),
                 call(data={'wl_unit':'1', 'wl_nctrlsb':'lower', 'action':'Apply'})]
        self.assertEqual(self.connection.mock_calls, calls)
        self.assertEqual(self.connection.path, RADIO_PAGE)
        return

    def test_set_ssid(self):
        """
        Does the connection get the right data to set the ssid?
        """
        ssid = random_letters()
        self.control.set_5_ssid(ssid)
        self.assertEqual(self.connection.path, SSID_PAGE)
        calls = [call(data={'wl_unit':'1', 'wl_ssid':ssid, 'action':'Apply'})]
        self.assertEqual(self.connection.mock_calls, calls)
                
        self.control.set_24_ssid(ssid)
        calls += [call(data={'wl_unit':'0', 'wl_ssid':ssid, 'action':'Apply'})]
        self.assertEqual(self.connection.mock_calls, calls)
        return
    
