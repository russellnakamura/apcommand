
# this package
from apcommand.baseclass import BaseClass
import apcommand.accesspoints.atheros 


class SubCommand(BaseClass):
    """
    A holder of sub-commands
    """
    def __init__(self):
        """
        SubCommand Constructor
        """
        super(SubCommand, self).__init__()
        return

    def access_point(self, args):
        '''
        The Access point controller
        '''
        # assume that the accesspoint class has valuable defaults
        # only pass in parameters that have been set by the arguments
        apargs = ('hostname', 'username', 'password')
        apvalues = (getattr(args, arg) for arg in apargs if getattr(args, arg) is not None)
        apkeys = (arg for arg in apargs if getattr(args, arg) is not None)
        apkwargs = dict(zip(apkeys, apvalues))
        ap = apcommand.accesspoints.atheros.AtherosAR5KAP(**apkwargs)
        return ap

    def up(self, args):
        """
        The AP up sub-command
        """
        ap = self.access_point(args)
        try:
            ap.up()
        except Exception as error:
            self.logger.error(error)
        return


# python standard library
import unittest
# third-party
from mock import MagicMock, patch


class TestSubCommand(unittest.TestCase):
    def setUp(self):
        self.logger = MagicMock()
        self.sub_command = SubCommand()
        self.sub_command._logger = self.logger
        return

    def test_args(self):
        """
        Does the correct set of arguments get passed to the ap
        """
        args = MagicMock()
        args.hostname = 'mike'
        args.username = 'bob'
        args.password = 'me'
        ap = MagicMock()
        with patch('apcommand.accesspoints.atheros', ap):
            # 000
            access_point = self.sub_command.access_point(args)
            ap.AtherosAR5KAP.assert_called_with(hostname=args.hostname,
                                                username=args.username,
                                                password=args.password)
            args.password = None
            # 001
            access_point = self.sub_command.access_point(args)
            ap.AtherosAR5KAP.assert_called_with(hostname=args.hostname,
                                                username=args.username)
            args.username = None
            # 011
            access_point = self.sub_command.access_point(args)
            ap.AtherosAR5KAP.assert_called_with(hostname=args.hostname)
            
            args.password = 'cow'
            # 010
            access_point = self.sub_command.access_point(args)
            ap.AtherosAR5KAP.assert_called_with(hostname=args.hostname,
                                                password=args.password)
            args.hostname=None
            # 110
            access_point = self.sub_command.access_point(args)
            ap.AtherosAR5KAP.assert_called_with(password=args.password)
            args.password = None
            # 111
            access_point = self.sub_command.access_point(args)
            ap.AtherosAR5KAP.assert_called_with()            
        return
        

    def test_up(self):
        """
        Does it have the up-method and will it catch exception?
        """
        args = MagicMock()
        self.assertTrue(hasattr(self.sub_command, 'up'))
        ap_up = MagicMock()
        ap_instance = MagicMock()
        ap_up.AtherosAR5KAP.return_value = ap_instance
        error_message = "this is an error"
        ap_instance.up.side_effect = Exception(error_message)
        with patch('apcommand.accesspoints.atheros', ap_up):
            self.sub_command.up(args)
            ap_instance.up.assert_called_with()
            self.logger.error.assert_called_with(ap_instance.up.side_effect)
        return