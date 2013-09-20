
# python standard library
import time


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
CHANNELS_24GHZ = [str(channel) for channel in xrange(1,12)]
SSID = 'wl_ssid'


# a decorator to set the page to 'radio.asp'
def radio_page(method):
    """
    Decorator: sets connection.path to radio.asp before, sleeps after
    """
    def _method(self, *args, **kwargs):
        self.logger.debug("Setting connection.path to '{0}'".format(RADIO_PAGE))
        self.connection.path = RADIO_PAGE
        outcome = method(self, *args, **kwargs)
        return outcome
    return _method

# a decorator to set the page to 'ssid.asp'
def ssid_page(method):
    """
    Decorator: sets connection.path to ssid.page before, sleeps after
    """
    def _method(self, *args, **kwargs):
        self.logger.debug("Setting connection.path to {0}".format(SSID_PAGE))
        self.connection.path = SSID_PAGE
        outcome = method(self, *args, **kwargs)
        return outcome
    return _method
