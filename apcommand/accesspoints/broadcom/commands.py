
# python standard library
from abc import ABCMeta, abstractproperty, abstractmethod
from contextlib import closing
import shelve

# this package
from apcommand.baseclass import BaseClass

# this package
from commons import action_dict, radio_page
from commons import BroadcomWirelessData, BroadcomRadioData
from commons import BroadcomPages, set_page
from commons import BandEnumeration
from querier import BroadcomRadioQuerier, BroadcomSSIDQuerier

class BroadcomBaseData(object):
    """
    The base-data to hold the data-dict
    """
    def __init__(self):
        """
        Base Data constructor
        """
        super(BroadcomBaseData, self).__init__()
        return

    @classmethod
    def base_data(cls):
        """
        Returns data dictionary that only has action:Apply 
        """
        return action_dict()

    @classmethod
    def base_24_ghz_data(cls):
        """
        data-dictionary to choose the 2.4 GHz interface
        """
        bwd = BroadcomWirelessData
        base_24_ghz_data = {bwd.wireless_interface: bwd.interface_24_ghz}
        return base_24_ghz_data

    @classmethod
    def base_5_ghz_data(cls):
        """
        data-dictionary to chose the 5 Ghz interface
        """
        bwd = BroadcomWirelessData
        base_5_ghz_data = {bwd.wireless_interface:bwd.interface_5_ghz}
        return base_5_ghz_data

    @classmethod
    def data(cls, action=True, band=None):
        """
        Builds a data-dict based on action and band

        :param:

         - `action`: if True, add action:Apply to the dict
         - `band`: if 2.4 or 5 add the interface selection data

        :return: base data-dict
        """
        band = str(band)
        if action:
            base_data = cls.base_data()
        else:
            base_data = {}

        if band.startswith('2'):
            base_data.update(cls.base_24_ghz_data())
        elif band.startswith('5'):
            base_data.update(cls.base_5_ghz_data())
        return base_data

    def __repr__(self):
        """
        Returns a representation of the data
        """
        return "{0}: Base: {1} 5GHz: {1} 2.4GHz: {2}".format(self.__class__.__name__,
                                                             self.base_data(),
                                                             self.base_5_ghz_data(),
                                                             self.base_24_ghz_data())

class BroadcomBaseCommand(BaseClass):
    """
    A base-class for the commands that change settings
    """
    __metaclass__ = ABCMeta
    def __init__(self, connection, band=None):
        """
        BroadcomBaseCommand constructor

        :param:

         - `connection`: A connection to the AP (HTTPConnection)
         - `band`: 2.4, 5, or None (chooses the data-dictionary)
        """
        super(BroadcomBaseCommand, self).__init__()
        self._logger = None
        self.connection = connection
        self._band = band
        self._base_data = None
        self._singular_data = None
        self._added_data = None
        self._non_base_data = None
        self._data = None
        self.previous_state = None
        self._querier = None
        self._shelf_name = None
        self._shelf_objects = None
        self._shelf_key = None
        self._asp_page = None
        return

    @abstractproperty
    def asp_page(self):
        """
        The page for the decorators to use (e.g. 'radio.asp')
        """

    @property
    def shelf_key(self):
        """
        a key to use for the cases where there's only one object to shelve
        """
        if self._shelf_key is None:
            self._shelf_key = "{0}_{1}".format(self.__module__,
                                               self.__class__.__name__)

    @property
    def shelf_objects(self):
        """
        The key:object dictionary to save (defaults to current singular-data)
        """
        return {self.shelf_key:self.singular_data}

    @property
    def shelf_name(self):
        """
        A name to use for any shelves created
        """
        if self._shelf_name is None:
            self._shelf_name = "{0}.shelve".format(__package__.split('.')[0])
        return self._shelf_name

    @property
    def querier(self):
        """
        A querier to get the previous state for the undo.

        This assumes radio.asp right now
        """
        if self._querier is None:
            self._querier = BroadcomRadioQuerier(connection=self.connection,
                                                 refresh=False,
                                                 band=self.band)
        return self._querier

    @property
    def band(self):
        """
        the band (2.4, 5, or None)
        """
        return self._band

    @band.setter
    def band(self, new_band):
        """
        sets the band and sets base_data, non_base_data to None
        """
        self.logger.debug('Setting to band: {0}'.format(new_band))
        self._band = str(new_band)
        self._data = None
        self._base_data = self._non_base_data = None
        self._querier = None
        return

    @property
    def base_data(self):
        """
        A data-dictionary to add commands to
        """
        if self._base_data is None:
            self.logger.debug("setting the base-data using band {0}".format(self.band))
            self._base_data = BroadcomBaseData.data(band=self.band)
            self.logger.debug('base-data: {0}'.format(self._base_data))
        return self._base_data

    @abstractproperty
    def singular_data(self):
        """
        A data dictionary with the command-specific data (or empty if querying)
        """
        if self._singular_data is None:
            self._singular_data = {}
        return self._singular_data    

    @property
    def added_data(self):
        """
        Maintains data added from other commands
        """
        if self._added_data is None:
            self._added_data = {}
        return self._added_data

    @property
    def non_base_data(self):
        """
        The singular data updated with any added data
        """
        if self._non_base_data is None:
            self._non_base_data = self.singular_data.copy()
            self._non_base_data.update(self.added_data)
        return self._non_base_data

    @property
    def data(self):
        """
        The data dictionary to send to the server
        """
        if self._data is None:
            self._data = self.base_data.copy()
            self._data.update(self.non_base_data)
        return self._data

    def __iadd__(self, other):
        """
        Adds the other's non_base_data to this added_data

        """
        self.added_data.update(other.non_base_data)
        self._data = self._non_base_data = None
        return self

    def __add__(self, other):
        """
        Adds the other's non_base_data to this added_data

        **For this to work the sub-classes can't change the constructor interface**
        """
        new_object = self.__class__(connection=self.connection,
                                    band=self.band)
        new_object.added_data.update(other.non_base_data)
        return new_object

    def __sub__(self, other):
        """
        Removes the other's non-base data from added_data in new object

        :return: object with this data minus other's non_base_data
        """
        new_object = self.__class__(connection=self.connection,
                                    band=self.band)
        new_object._added_data = self.added_data.copy()
        
        for key in other.non_base_data.iterkeys():
            if key in new_object.added_data:
                del new_object.added_data[key]
        return new_object

    @set_page
    def __call__(self):
        """
        The main method to change settings 
        """
        self.store()
        self.connection(data=self.data)
        return

    def undo(self):
        """
        This is an attempt to start bringing this into line with the Command Pattern

        But it isn't clear that it will be easy (or possible) in every case -
        so it isn't made a requirement        
        """
        raise NotImplemented("undo not supported for this command")

    def store(self):
        """
        shelve data from this class (use in __call__, not meant for public)

        :precondition: self.shelf_objects is a dictionary of things to shelve
        :postocondition: objects is shelf_objects is shelved
        """
        with closing(shelve.open(self.shelf_name, writeback=True)) as open_shelf:
            for key, value in self.shelf_objects.iteritems():
                open_shelf[key] = value
        return

    def load(self):
        """ 
        Loads the shelved data for the undo method
        (to prevent circular calls using shelf_objects' keys, just uses shelf_key)

        :return: dictionary of objects using shelf_objects' keys
        :raise: KeyError if an item in shelf_objects isn't on the shelf
        """
        with closing(shelve.open(self.shelf_name, flag='r')) as open_shelf:
            data = open_shelf[self.shelf_key]
        return data

# end class BroadcomBaseCommand

class StateData(object):
    __slots__ = ()
    state = 'state'
    band = 'band'

class EnableInterface(BroadcomBaseCommand):
    """
    An interface enabler
    """
    def __init__(self, *args, **kwargs):
        super(EnableInterface, self).__init__(*args, **kwargs)
        self._enable_24_data = None
        self._enable_5_data = None
        self._disable = None
        return

    @property
    def asp_page(self):
        """
        radio.asp
        """
        if self._asp_page is None:
            self._asp_page = BroadcomPages.radio
        return self._asp_page

    @property
    def disable(self):
        """
        An interface disabler
        """
        if self._disable is None:
            self._disable = DisableInterface(connection=self.connection,
                                             band=self.band)
        return self._disable

    @property
    def shelf_objects(self):
        """
        A dictionary of shelf_key: band
        """
        previous_state = self.querier.state
        return {self.shelf_key:self.band}

    def undo(self):
        """
        Disable the interface 

        This is actually just a call to DisableInterface...
        """
        try:
            self.band = self.load()
            self.disable()
        except KeyError as error:
            self.logger.debug(error)
            self.logger.debug('No entry on the shelf for {0}'.format(self.shelf_key))
        return

    @property
    def singular_data(self):
        """
        The data to enable the interface
        """
        band = str(self.band)
        if band.startswith('2'):
            return self.enable_24_data
        elif band.startswith('5'):
            return self.enable_5_data

    @property
    def enable_5_data(self):
        """
        The data to send to the connection to enable 5 GHz

        :return: dict of data-values for the connection
        """
        if self._enable_5_data is None:
            radio_data = BroadcomRadioData
            self._enable_5_data = {radio_data.interface :radio_data.radio_on}
        return self._enable_5_data


    @property
    def enable_24_data(self):
        """
        The data to send to the connection to enable 2.4 GHz

        :return: dict of data-values for the connection
        """
        if self._enable_24_data is None:
            radio_data = BroadcomRadioData
            self._enable_24_data = {radio_data.interface:radio_data.radio_on}
        return self._enable_24_data

class DisableInterface(BroadcomBaseCommand):
    """
    An interface enabler
    """
    def __init__(self, *args, **kwargs):
        super(DisableInterface, self).__init__(*args, **kwargs)
        self._disable_24_data = None
        self._disable_5_data = None
        self._enable = None
        return

    @property
    def asp_page(self):
        """
        radio.asp
        """
        if self._asp_page is None:
            self._asp_page = BroadcomPages.radio
        return self._asp_page

    @property
    def enable(self):
        """
        An interface enabler for the undo
        """
        if self._enable == None:
            self._enable = EnableInterface(connection=self.connection,
                                           band=self.band)
        return self._enable                                           

    @property
    def querier(self):
        """
        A querier to get the previous state
        """
        if self._querier is None:
            self._querier = BroadcomQuerier(connection=self.connection,
                                            refresh=True,
                                            band=self.band)
        return self._querier

    @property
    def shelf_objects(self):
        """
        dictionary of shelf_key: band
        """
        return {self.shelf_key: self.band}
        
    def undo(self):
        """
        enables the interface 
        """
        try:
            self.band = self.load()
            self.enable()
        except KeyError as error:
            self.logger.debug(error)
            self.logger.debug('No entry on the shelf for {0}'.format(self.shelf_key))    
        return

    @property
    def singular_data(self):
        """
        The data to enable the interface

        This isn't persistent, as changing the band changes the data
        """
        band = str(self.band)
        if band.startswith('2'):
            return self.disable_24_data
        elif band.startswith('5'):
            return self.disable_5_data

    @property
    def disable_5_data(self):
        """
        The data to send to the connection to disable 5 GHz

        :return: dict of data-values for the connection
        """
        if self._disable_5_data is None:
            radio_data = BroadcomRadioData
            self._disable_5_data = {radio_data.interface: radio_data.radio_off}
        return self._disable_5_data

    @property
    def disable_24_data(self):
        """
        The data to send to the connection to enable 2.4 GHz

        :return: dict of data-values for the connection
        """
        if self._disable_24_data is None:
            radio_data = BroadcomRadioData
            self._disable_24_data = {radio_data.interface: radio_data.radio_off}
        return self._disable_24_data

class SetChannel(BroadcomBaseCommand):
    """
    A channel setter for the AP
    """
    def __init__(self, *args, **kwargs):
        super(SetChannel, self).__init__(*args, **kwargs)
        self._channel_map = None
        self._channel = None       
        return

    @property
    def asp_page(self):
        """
        radio.asp
        """
        if self._asp_page is None:
            self._asp_page = BroadcomPages.radio
        return self._asp_page

    @property
    def shelf_objects(self):
        """
        A dictionary of shelf_key: channel for current band
        """
        self.querier.band = self.band
        channel = self.querier.channel
        return {self.shelf_key: channel}
        
    @property
    def channel(self):
        """
        returns the channel
        """
        return self._channel

    @channel.setter
    def channel(self, new_channel):
        """
        Sets the channel, the band, and singular_data based on the channel.
        """
        channel = str(new_channel)
        self.band = self.channel_map[channel]
        self._singular_data = {BroadcomRadioData.control_channel:channel}
        return

    @property
    def channel_map(self):
        """
        Map of channel to data-dictionary
        """
        if self._channel_map is None:
            channel_24 = [str(channel) for channel in range(1,12)]
            channel_24_data = ['2.4'] * len(channel_24)
            # these are the only channels that match the Atheros channels we chose
            channel_5 = BroadcomRadioData.channels_5ghz
            channel_5_data = ['5'] * len(channel_5)
            channels = channel_24 + channel_5
            data = channel_24_data + channel_5_data         
            self._channel_map = dict(zip(channels, data))
        return self._channel_map

    @property
    def singular_data(self):
        """
        This is a pass-through (it has to be set when given a channel)
        """
        return self._singular_data

    def undo(self):
        """
        Sets the channels found on the shelve
        """
        try:
            self.channel = self.load()
            self()
        except KeyError as error:
            self.logger.debug(error)
            self.logger.debug("No entry on shelf for {0}".format(self.shelf_key))
        return

class SetSideband(BroadcomBaseCommand):
    """
    A side-band ('upper' or 'lower') setter
    """
    def __init__(self, *args, **kwargs):
        super(SetSideband, self).__init__(*args, **kwargs)
        self.band = '5'
        self._direction = None
        return

    @property
    def asp_page(self):
        """
        radio.asp
        """
        if self._asp_page is None:
            self._asp_page = BroadcomPages.radio
        return self._asp_page

    @property
    def singular_data(self):
        """
        This has to be set in the call when you know what the direction is
        """
        return self._singular_data

    @property
    def direction(self):
        """
        upper or lower
        """
        return self._direction

    @direction.setter
    def direction(self, new_direction):
        """
        sets the direction, band, and singular_data
        """
        direction = new_direction.lower()
        if direction.startswith('l'):
            self._direction = 'lower'
        elif direction.startswith('u'):
            self._direction = 'upper'
        #else raise some kind of error
        self._singular_data = {BroadcomRadioData.sideband:self._direction}
        return
    
    def __call__(self):
        """
        Sets the sideband ('upper' or 'lower') for 5GHz
        """
        self.connection(data=self.data)
        return
# end SetSideband

# python standard library
import unittest
import random
import string

# third-party
from mock import MagicMock, call, patch

random_letters = lambda: ",".join((random.choice(string.letters) for char in xrange(random.randint(1,5))))

class BadChild(BroadcomBaseCommand):
    def query(self):
        return

class BadChild2(BroadcomBaseCommand):
    def base_data(self):
        return

class EvilChild(BroadcomBaseCommand):
    def asp_page(self):
        return
        
    def base_data(self):
        return
    
    def query(self):
        return

    @property
    def singular_data(self):
        return

    def __call__(self):
        return

    def path(self):
        return

# this can't be random in the class for testing to work
# Because __add__  creates a new object
test_data = {random_letters(): random_letters()}
test_data_2 = {random_letters(): random_letters()}
test_data_3 = {random_letters(): random_letters()}    
class TestChild(BroadcomBaseCommand):
    def __init__(self, *args, **kwargs):
        super(TestChild, self).__init__(*args, **kwargs)
        return

    def asp_page(self):
        return BroadcomPages.radio

    @property
    def singular_data(self):
        if self._singular_data is None:
            self._singular_data = test_data
        return self._singular_data

    def __call__(self):
        return

    def __add__(self, other):
        t = TestChild(self.connection)
        t.added_data.update(other.non_base_data)
        return t

    def path(self):
        return

class TestChild2(TestChild):
    def __init__(self, *args, **kwargs):
        super(TestChild2, self).__init__(*args, **kwargs)
        return

    @property
    def singular_data(self):
        if self._singular_data is None:
            self._singular_data = test_data_2
        return self._singular_data

class TestChild3(TestChild):
    def __init__(self, *args, **kwargs):
        super(TestChild3, self).__init__(*args, **kwargs)
        return

    @property
    def singular_data(self):
        if self._singular_data is None:
            self._singular_data = test_data_3
        return self._singular_data
    
class TestBroadcomCommands(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock()
        return

    def test_abstract_property(self):
        """
        Does a class without the properties defined crash on creation?
        """
        self.assertRaises(TypeError, BroadcomBaseCommand, args=(self.connection,))
        self.assertRaises(TypeError, BadChild, args=(self.connection,))
        self.assertRaises(TypeError, BadChild2, args=(self.connection,))
        EvilChild(self.connection)
        return

    def test_add(self):
        """
        Can you add two commands?        
        """
        command_1 = TestChild(self.connection)
        command_2 = TestChild2(self.connection)
        
        data_1, data_2 = command_1.data, command_2.data

        data_changed = data_1.copy()
        data_changed.update(data_2)

        # first __add__
        command_3 = command_1 + command_2

        # creates a new object with the combined data
        self.assertEqual(data_changed, command_3.data)
        self.assertEqual(self.connection, command_3.connection)
        # leaves the originals alone
        self.assertEqual(command_1.data, data_1)
        self.assertEqual(command_2.data, data_2)

        # now __iadd__
        command_1 += command_2
        # changes LHS in place
        self.assertEqual(command_1.data, data_changed)
        self.assertEqual(command_2.data, data_2)
        return

    def test_subtract(self):
        """
        Can you subtract two commands?
        """
        command_1 = TestChild(self.connection)
        command_2 = TestChild2(self.connection)
        command_3 = TestChild3(self.connection)

        data_1, data_2, data_3 = command_1.data, command_2.data, command_3.data
        data_changed = data_1.copy()
        data_changed.update(data_2)
        data_changed.update(data_3)

        # first add so the commands are different
        command_1 += command_2
        command_1 += command_3
        
        # First __sub__
        command_4 = command_1 - command_2

        data_1_3 = data_1.copy()
        data_1_3.update(data_3)
        # new cleaned object
        self.assertEqual(command_4.data, data_1_3)

        command_4 = command_1 - command_2 - command_3
        self.assertEqual(command_4.data, data_1)

        # old objects unchanged
        self.assertEqual(command_1.data, data_changed)
        self.assertEqual(command_2.data, data_2)

        # now __isub__
        self.assertNotEqual(command_1.data, data_1)
        command_1 -= command_2
        self.assertEqual(command_1.data, data_1_3)
        self.assertEqual(command_2.data, data_2)

        command_1 -= command_3
        self.assertEqual(command_1.data, data_1)
        return

class TestEnableInterface(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock(name='connection')
        self.html = MagicMock(name='html')
        self.connection.return_value = self.html
        self.html.text = open('radio_asp.html').read()
        self.command = EnableInterface(connection=self.connection)        
        return

    def test_previous_state(self):
        """
        Does it get the previous state correctly?
        """
        command = EnableInterface(connection=self.connection,
                                  band='2')
        command()

        command.band = '5'
        command()    
        return

    def test_24ghz(self):
        """
        Does it construct the right set of data to Enable the interface?
        """
        command = EnableInterface(connection=self.connection,
                                  band='2.4')
        expected_data =  {'wl_unit':'0',
                          'action':'Apply',
                          'wl_radio':'1'}

        self.assertEqual(command.data, expected_data)
        command()
        self.assertEqual(self.connection.path, 'radio.asp')
        self.connection.assert_called_with(data=expected_data)
        return

    def test_5_ghz(self):
        """
        Does it send the 5 GHz data to the connection?
        """
        command = EnableInterface(connection=self.connection,
                                  band='5')
        expected_data ={'action':'Apply',
                        'wl_unit':'1',
                        'wl_radio':'1'}
        self.assertEqual(command.data, expected_data)

        # what happens if you change it to 2.4?
        command.band = '2.4'
        expected_data ={'action':'Apply',
                        'wl_unit':'0',
                        'wl_radio':'1'}
        self.assertEqual(command.data, expected_data)
        return

    def test_undo(self):
        """
        Does the undo disable the interface?
        """
        connection = MagicMock(name='connection')
        html = MagicMock(name='html')
        connection.return_value = html
        html.text = open('radio_asp.html').read()
        command = EnableInterface(connection=connection)        

        command.band = 5
        command()

        html.text = open('radio_5_asp.html').read()

        command.undo()
        query_call = call(data={'wl_unit':'1'})
        calls = [query_call,
                 call(data={'action':'Apply',
                        'wl_unit':'1',
                        'wl_radio':'1'}),
                            call(data ={'action':'Apply',
                        'wl_unit':'1',
                        'wl_radio':'0'})]
        self.assertEqual(connection.mock_calls, calls)
        self.command.previous_state = 'Enabled'

        # the disable checks the state so we need to change the html so it is Disabled
        #self.html.text = open('radio_5_asp.html').read()
        #self.command.undo()
        #self.assertEqual(self.connection.mock_calls, calls)
        return

class TestDisableInterface(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock(name='connection')
        self.html = MagicMock(name='html')
        self.connection.return_value = self.html
        self.html.text = open('radio_5_asp.html').read()
        return

    def test_24_ghz(self):
        """
        Does it setup the right data dictionary and make the right call?
        """
        command = DisableInterface(connection=self.connection,
                                   band='2.4')
        expected_data = {'action':'Apply',
                        'wl_unit':'0',
                        'wl_radio':'0'}
        self.assertEqual(command.data, expected_data)
        command()
        self.connection.assert_called_with(data=expected_data)
        self.assertEqual(self.connection.path, 'radio.asp')
        return

    def test_5_ghz(self):
        """
        Does it set up the right data dictionary to disable the 5 Ghz interface?
        """
        command = DisableInterface(connection=self.connection,
                                   band='5')
        expected_data = {'action':'Apply',
                        'wl_unit':'1',
                        'wl_radio':'0'}
        self.assertEqual(command.data, expected_data)

class TestSetChannel(unittest.TestCase):
    def setUp(self):
        self.fake_channel = random_letters()
        self.querier = MagicMock()
        self.querier.channel = self.fake_channel
        self.connection = MagicMock()
        self.command = SetChannel(connection=self.connection)
        self.command._querier = self.querier
        return

    def test_24_ghz(self):
        """
        Does it pass in the correct data to set the (2.4 GHz) channel?
        """
        channel = random.choice(BroadcomRadioData.channels_24ghz)
        self.command.channel = channel
        expected_data = {'action':'Apply',
                        'wl_unit':'0',
                        'wl_channel':str(channel)}
        # setup the shelving
        self.command._querier = self.querier
        mock_shelf = MagicMock(spec_set=dict)
        mock_closing = MagicMock()
        mock_closing.return_value = mock_shelf
        with patch('contextlib.closing', mock_closing):
            #with patch('shelve', mock_shelf):
            self.command()
        self.connection.assert_called_with(data=expected_data)
        return

    def test_5_ghz(self):
        """
        Does it pass in the correct data to set the (5GHz) channel?
        """
        channel = random.choice(BroadcomRadioData.channels_5ghz)
        self.command.channel = channel
        expected_data = {'action':'Apply',
                        'wl_unit':'1',
                        'wl_channel':str(channel)}
        # setup the shelving
        self.command._querier = self.querier
        mock_shelf = MagicMock(spec_set=dict)
        mock_closing = MagicMock()
        with patch('contextlib.closing', mock_closing):
            #with patch('shelve', mock_shelf):
            self.command()
        self.connection.assert_called_with(data=expected_data)
        return

    def test_shelf_objects(self):
        """
        Is shelf_objects a dict of shelf_key:previous-channels dict?
        """
        querier = MagicMock()
        command = SetChannel(connection=self.connection)
        command._querier = self.querier
        shelf_objects = command.shelf_objects
        self.assertEqual(command.shelf_key, shelf_objects.keys()[0])
        self.assertEqual(self.fake_channel,
                          shelf_objects[command.shelf_key])
        return
# end class TestSetChannel

class TestSetSideband(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock()
        return

    def test_set_sideband(self):
        """
        Does it set the sideband correctly?
        """
        command = SetSideband(connection=self.connection)
        command.direction = 'lower'
        expected_data = {'action':'Apply',
                        'wl_unit':'1',
                        'wl_nctrlsb':'lower'}
        command()
        self.connection.assert_called_with(data=expected_data)
        return