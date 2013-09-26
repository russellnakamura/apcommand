
#python standard library
import argparse

# this package
import subcommands


class Arguments(object):
    """
    An adapter for the argparse.ArgumentParser
    """
    def __init__(self):
        """
        Arguments Constructor
        """
        self._parser = None
        self._arguments = None
        self._subparsers = None
        self._subcommands = None
        return

    @property
    def subcommands(self):        
        """
        The SubCommands object for the parser sub-commands
        """
        if self._subcommands is None:
            self._subcommands = subcommands.SubCommand()
        return self._subcommands

    @property
    def parser(self):
        """
        The argparse Argument Parser
        
        :return: ArgumentParser 
        """
        if self._parser is None:
            self._parser = argparse.ArgumentParser()
        return self._parser

    @property
    def arguments(self):
        """
        The namespace containing the command-line arguments
        
        :return: the parsed command-line arguments
        """
        if self._arguments is None:
            self.add_arguments()
            self.add_subparsers()
            self._arguments = self.parser.parse_args()
        return self._arguments

    @property
    def subparsers(self):
        """
        The subparsers for the parser

        :return: ArgumentParser subparsers
        """
        if self._subparsers is None:
            self._subparsers = self.parser.add_subparsers(title="Broadcom subcommands",
                                                          description="Available Sub-Commands",
                                                          help="Broadcom sub-commands")
        return self._subparsers

    def add_arguments(self):
        """
        Add the command-line arguments to the parser
        """
        # debugging
        self.parser.add_argument("--pudb",
                                 action='store_true',
                                 help="Run the `pudb` debugger (default=%(default)s).",
                                 default=False)
        self.parser.add_argument("--pdb",
                                 action='store_true',
                                 help="Run the `pdb` debugger (default=%(default)s).",
                                 default=False)
        # logging
        self.parser.add_argument('-s', '--silent',
                                 action='store_true',
                                 help="If True only emit error messages (default=%(default)s)",
                                 default=False)
        
        self.parser.add_argument('-d', '--debug',
                                 action='store_true',
                                 help='If True emit debug messages (default=%(default)s)',
                                 default=False)

        # connection
        self.parser.add_argument('--hostname',
                                 help="The hostname for the AP (leave unset for default).",
                                 default=None)
        self.parser.add_argument('--username',
                                 help='The user-login for the AP (leave unset for default)',
                                 default=None)
        self.parser.add_argument('--password',
                                help='The login password for the AP (Leave unset for default)',
                                default=None)
        self.parser.add_argument('--sleep',
                                 help='Seconds to sleep after web server call (default=%(default)s)',
                                 type=float,
                                 default=0.5)
        return

    def add_subparsers(self):
        """
        Add the subparsers to the parser
        """
        # query the interface status
        status = self.subparsers.add_parser('status',
                                            help='Get some information for an interface')
        status.add_argument('band',
                            help="the band of the interface to query (default=%(default)s) (use 'all' for all interfaces)",
                            default='all',
                            nargs="?")
        status.set_defaults(function=self.subcommands.status)

        # change the channel
        channel = self.subparsers.add_parser('channel',
                                             help='Change the AP channel')
        channel.add_argument('channel', help='Channel to set (none to get current channels)',
                             nargs='?', default=None)
        channel.add_argument('--undo', help="Undo the last channel change.",
                             action='store_true')
        channel.set_defaults(function=self.subcommands.channel)

        # disable an interface
        disable = self.subparsers.add_parser('disable',
                                             help='Disable a wireless interface.')
        disable.add_argument('band',
                             help=('Band (GHz) of the interface to disable'
                                   ' (2.4, 5 or both) default=%(default)s.'),
                                   default='both')        
        disable.set_defaults(function=self.subcommands.disable)
        
        # enable an interface
        enable = self.subparsers.add_parser('enable',
                                             help='Enable an interface.')
        enable.add_argument('band',
                            help='Band of interface to enable (2.4, 5 or both) default=%(default)s.',
                            default='both')
        enable.set_defaults(function=self.subcommands.enable)

        # change the ssid
        ssid = self.subparsers.add_parser('ssid',
                                          help='Change the SSID')
        ssid.add_argument('ssid',
                          help='The SSID to use', nargs='?',
                          default=None)
        ssid.add_argument('-b', '--band', help='2.4 or 5 (default=%(default)s)',
                          default=None)
        ssid.set_defaults(function=self.subcommands.ssid)

        return
# end class Arguments
