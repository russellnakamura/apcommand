
wl_unit = """<select name="wl_unit" onchange="submit();">
<option selected value="0">(00:90:4C:09:11:03)</option>
<option value="1">(00:90:4C:13:11:03)</option>
</select>"""
print wl_unit


class SoupError(RuntimeError):
    """
    Raise if something is detected at run-time.
    """


# python standard library
import re

# third-party
import bs4

# this package
from apcommand.baseclass import BaseClass


NAME = 'name'
VALUE = 'value'
ZERO = '0'
ONE = '1'
VALUE_ZERO = {VALUE:ZERO}
VALUE_ONE = {VALUE:ONE}
WIRELESS_INTERFACE = 'wl_unit'
INTERFACE = 'wl_radio'
COUNTRY = 'wl_country_code'
CHANNEL = 'wl_channel'
BANDWIDTH = 'wl_nbw_cap'
SELECTED_EXPRESSION = r'selected\svalue=.*>(?P<{0}>.*)<'
BANDWIDTH_EXPRESSION = SELECTED_EXPRESSION.format(BANDWIDTH)
SIDEBAND = 'wl_nctrlsb'
SIDEBAND_EXPRESSION = SELECTED_EXPRESSION.format(SIDEBAND)


class BroadcomRadioSoup(BaseClass):
    """
    A holder of BeautifulSoup
    """
    def __init__(self, html=None):
        """
        Broadcom soup constructor

        :param:

         - `html`: a file-object or string to pass to BeautifulSoup
        """
        super(BroadcomRadioSoup, self).__init__()
        self._html = None
        self.html = html
        self._soup = None

        # the sub-trees and text
        self._wireless_interface = None
        self._mac_24_ghz = None
        self._mac_5_ghz = None
        self._country = None
        self._interface_24_state = None
        self._interface_5_state = None
        self._channel = None
        self._bandwidth = None
        self._sideband = None
        return

    @property
    def html(self):
        """
        The html for soup        
        """
        return self._html

    @html.setter
    def html(self, new_html):
        """
        sets the html, resets the soup
        """
        self._html = new_html
        self._soup = None
        return

    @property
    def soup(self):
        """
        A beautiful soup object created from self.html

        :return: BeautifulSoup with self.html loaded
        :raise: SoupError if something went wrong
        """
        if self._soup is None:
            try:
                self._soup = bs4.BeautifulSoup(self.html)
            except TypeError as error:
                self.logger.error(error)
                raise SoupError("unable to create soup from {0}".format(self.html))
        return self._soup

    @property
    def wireless_interface(self):
        """
        The `wl_unit` sub-tree
        """
        return self.soup.find(attrs={NAME:WIRELESS_INTERFACE})

    def get_value_one(self, tag):
        """
        Gets the value='1' tag from a tag (subtree) 

        :param:

         - `tag`: bs4.element.Tag with value='1' tag in it

        :return: tag with value='1' in it
        """
        return tag.find(attrs=VALUE_ONE)

    def get_value_zero(self, tag):
        """
        Gets the first value='0' tag from a tag (subtree) 

        :param:

         - `tag`: bs4.element.Tag with value='0' tag in it

        :return: bs4.element.Tag child of original tag 
        """
        return tag.find(attrs=VALUE_ZERO)

    @property
    def mac_24_ghz(self):
        """
        The 2.4 GHz MAC address text from the wl_unit

        :return: (<MAC ADDRESS>)
        """
        return self.get_value_zero(self.wireless_interface).text

    @property
    def mac_5_ghz(self):
        """
        The 5 GHz MAC address text from the wl_unit tag

        :return: (<5 GHz MAC Address>)
        """
        return self.get_value_one(self.wireless_interface).text

    @property
    def country(self):
        """
        Gets the current country setting

        :return: Country Code (e.g. 'US')
        """
        return self.soup.find(attrs={NAME:COUNTRY}).option[VALUE]

    @property
    def interface_24_state(self):
        """
        Get the state of the 2.4 Ghz radio (enabled or disabled)

        :return: 'Enabled' or 'Disabled'
        """
        return self.soup.find(attrs={NAME:INTERFACE}).find(attrs=VALUE_ONE).text

    @property
    def interface_5_state(self):
        """
        Get the state of the 5 Ghz radio (enabled or disabled)

        :return: 'Enabled' or 'Disabled'
        """
        return self.soup.find(attrs={NAME:INTERFACE}).find(attrs=VALUE_ZERO).text

    @property
    def channel(self):
        """
        Gets the channel for the currently selected interface
        """
        return self.soup.find(attrs={NAME:CHANNEL}).option[VALUE]

    @property
    def bandwidth(self):
        """
        The bandwidth setting (for both bands)
        """
        for line in self.soup.find(attrs={NAME:BANDWIDTH}):
            match = re.search(BANDWIDTH_EXPRESSION, str(line))
            if match:
                return match.group(BANDWIDTH)

    @property
    def sideband(self):
        """
        Gets the sideband (only for 40GHz)

        :return: 'Upper', 'Lower', or None
        """
        for line in self.soup.find(attrs={NAME:SIDEBAND}):
            match = re.search(SIDEBAND_EXPRESSION, str(line))
            if match:
                return match.group(SIDEBAND).rstrip()
        


# python standard library
import unittest
import random
choose = random.choice

# third-party
from mock import MagicMock, patch


class TestBroadcomRadioSoup(unittest.TestCase):
    def setUp(self):
        # if you put a file open outside of the class imports will crash
        # unless you happen to be running the code in this folder
        self.radio_html = open('radio_asp.html').read()
        self.soup = BroadcomRadioSoup(self.radio_html)
        self.soup_5 = BroadcomRadioSoup(open('radio_5_asp.html').read())
        return

    def test_constructor(self):
        """
        Does it the constructor set the right parameters
        """
        self.assertEqual(self.radio_html, self.soup.html)
        return

    def test_soup(self):
        """
        Does BeautfulSoup get passed the html attribute?
        """
        soup = MagicMock()
        with patch('bs4.BeautifulSoup', soup):
            self.soup.soup
        soup.assert_called_with(self.soup.html)

        # now get rid of the html
        self.soup.html = None
        
        # beautiful soup takes html at construction, changing html should reset soup
        self.assertIsNone(self.soup._soup)

        # if the html isn't set, how will you make soup?
        with self.assertRaises(SoupError):
            self.soup.soup
        return

    def test_interface(self):
        """
        Does it get the wireless interface?
        """
        # wl_unit is defined in the explanatory text
        self.assertEqual(wl_unit, str(self.soup.wireless_interface))
        return

    def test_get_band(self):
        """
        Does it get the band option from a tag?
        """
        band_24 = '<option selected value="0">(00:90:4C:09:11:03)</option>'
        band_5 = '<option value="1">(00:90:4C:13:11:03)</option>'

        tag = self.soup.wireless_interface
        outcome = self.soup.get_value_zero(tag)
        self.assertEqual(str(outcome), band_24)

        self.assertEqual(str(self.soup.get_value_one(tag)), band_5)
        return

    def test_mac_address(self):
        """
        Does it get the 2.4 GHz and 5 GHz MAC Addresses?
        """
        band_24 = '(00:90:4C:09:11:03)'
        band_5 = '(00:90:4C:13:11:03)'
        self.assertEqual(self.soup.mac_24_ghz, band_24 )
        self.assertEqual(self.soup.mac_5_ghz, band_5)
        return

    def test_country_code(self):
        """
        Does it extract the current country?
        """
        self.assertEqual(self.soup.country, 'US')
        return

    def test_radio_state(self):
        """
        Does it correctly get the state of the radio?
        """
        self.assertEqual(self.soup.interface_24_state, 'Enabled')
        self.assertEqual(self.soup.interface_5_state, 'Disabled')
        return

    def test_channel(self):
        """
        Does it get the current channel?
        """
        # unlike other parts of the page this only lists the channel for the current interface
        self.assertEqual(self.soup.channel, '36')
        return

    def test_bandwidth(self):
        """
        Does it get the bandwidth?
        """
        # the Broadcom sets values for both bands
        # you need to pair this outcome with the current interface to get
        # current bandwidth
        self.assertEqual(self.soup.bandwidth, "20MHz in 2.4G Band and 40MHz in 5G Band")
        return

    def test_sideband(self):
        """
        Does it get the right sideband (5GHz only)?
        """
        self.assertIsNone(self.soup.sideband)
        self.assertEqual(self.soup_5.sideband, 'Lower')
