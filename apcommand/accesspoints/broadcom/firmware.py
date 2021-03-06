
# python standard library
import re

# third-party
from bs4 import BeautifulSoup

# this package
from apcommand.accesspoints.broadcom.parser import BroadcomBaseSoup
from apcommand.accesspoints.broadcom.commons import BroadcomPages
from apcommand.accesspoints.broadcom.querier import BroadcomBaseQuerier

EMPTY_STRING = ''
BOOTLOADER = 1
OS_VERSION = 3
WL_DRIVER = 5

class BroadcomFirmwareSoup(BroadcomBaseSoup):
    """
    A soup to get the firmware information
    """
    def __init__(self, *args, **kwargs):
        """
        BroadcomFirmwareSoup Constructor
        """
        super(BroadcomFirmwareSoup, self).__init__(*args, **kwargs)
        self._extractor_expression = None
        return

    def get_data(self, index):
        """
        Get the data of at table-data index
        """
        data = self.soup('form', attrs={'action': 'upgrade.cgi'})[0]('table')[0]('td')
        return self.extractor_expression.sub(EMPTY_STRING, str(data[index]))
    
    @property
    def extractor_expression(self):
        """
        A compiled regular expression to get the 'td' tags
        """
        if self._extractor_expression is None:
            self._extractor_expression = re.compile('\s*<[/]*td>')
        return self._extractor_expression

    @property
    def bootloader_version(self):
        """
        returns the bootloader version
        """
        return self.get_data(BOOTLOADER)

    @property
    def os_version(self):
        """
        Return the OS version
        """
        return self.get_data(OS_VERSION)

    @property
    def wl_driver_version(self):
        """
        return the WL Driver Version
        """
        return self.get_data(WL_DRIVER)
#

class BroadcomFirmwareQuerier(BroadcomBaseQuerier):
    """
    A querier for the firmware.asp page
    """
    def __init__(self, *args, **kwargs):
        super(BroadcomFirmwareQuerier, self).__init__(*args, **kwargs)
        return

    @property
    def asp_page(self):
        """
        firmware.asp
        """
        if self._asp_page is None:
            self._asp_page = BroadcomPages.firmware
        return self._asp_page

    @property
    def soup(self):
        """
        A BroadcomFirmwareSoup
        """
        if self._soup is None:
            self._soup = BroadcomFirmwareSoup()
        return self._soup

    @property
    def bootloader_version(self):
        self.set_soup()
        return self.soup.bootloader_version

    @property
    def os_version(self):
        self.set_soup()
        return self.soup.os_version

    @property
    def wl_driver_version(self):
        self.set_soup()
        return self.soup.wl_driver_version