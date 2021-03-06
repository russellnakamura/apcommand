
#python Libraries
from StringIO import StringIO
import logging
import Queue
import threading
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import namedtuple

#third party
#from yapsy.IPlugin import IPlugin

# apcommand Libraries
from apcommand.baseclass import BaseClass
from apcommand.commons.errors import ConfigurationError
from localconnection import OutputError
import enumerations


SPACER = '{0} {1} '
UNKNOWN = "Unknown command: "
EMPTY_STRING = ''
EOF = EMPTY_STRING
DOT_JOIN = "{0}.{1}"
SPACE = ' '


class NonLocalConnection(BaseClass):
    """
    A non-local connection is the base for non-local connections

    """
    __metaclass__ = ABCMeta
    def __init__(self, hostname, username, password=None,
                 operating_system=enumerations.OperatingSystem.linux,
                 timeout=5, command_prefix='', lock=None,
                 path=None, library_path=None,
                 *args, **kwargs):
        """
        NonLocalConnection Constructor
        
        :param:
         - `hostname`: The IP Address or hostname
         - `username`: The login name
         - `password` : the user-password
         - `timeout`: a login-timeout
         - `command_prefix`: A prefix to prepend to commands (e.g. 'adb shell')
         - `lock` : A lock to acquire before calls
         - `operating_system`: the operating system
         - `path`: a path setting to add to the path (before :$PATH)
         - `library_path`: a setting for LD_LIBRARY_PATH
        """
        super(NonLocalConnection, self).__init__(*args, **kwargs)
        # logger is defined in BaseClass but declared here for child-classes
        self.hostname = hostname
        self.username = username
        self.password = password
        self.timeout = timeout
        
        self._logger = None
        self._command_prefix = None
        self.command_prefix = command_prefix
        self._lock = lock
        self._path = None
        self.path = path
        self._library_path = None
        self.library_path = library_path
        self._prefix = None
        self.operating_system = operating_system
        self._client = None
        self._port = None
        return

    @abstractproperty
    def client(self):
        """
        The client connected to the remote device's server

        :return: Connected client
        """
        return

    @abstractproperty
    def client(self):
        """
        The client connected to the remote device's server

        :return: Connected client
        """
        return

    @abstractproperty
    def port(self):
        """
        The port for the server (use this to set a default)
        """
        return
    
    @property
    def command_prefix(self):
        """
        A prefix given to every command (e.g. `adb shell`)

        :return: prefix with space as suffix
        """
        if self._command_prefix is None:
            self._command_prefix = EMPTY_STRING
        return self._command_prefix

    @command_prefix.setter
    def command_prefix(self, prefix):
        """
        Sets the command_prefix, ensuring there's a space after it, resets self._prefix

        :param:

         - `prefix`: a string to prepend to every command
        """
        if len(prefix):
            self._prefix = None
            self._command_prefix = prefix.strip() + SPACE
        return

    @property
    def library_path(self):
        """
        Additions to the LD_LIBRARY_PATH variable

        :rtype: String
        :return: the library path addition      
        """
        if self._library_path is None:
            self._library_path = EMPTY_STRING
        return self._library_path

    @library_path.setter
    def library_path(self, path):
        """
        Sets the library-path addition and resets the `prefix` attribute

        :param:

         - `path`: string with path to library on remote device
        """
        #print "library path: {}".format(path)
        self._prefix = None
        if path is not None:
            self._library_path = "export LD_LIBRARY_PATH={0}:$LD_LIBRARY_PATH;".format(path)
        else:
            self._library_path = path
        return        
    
    @property
    def path(self):
        """
        A path-variable addition

        :rtype: String
        :return: path-addition
        """
        if self._path is None:
            self._path = EMPTY_STRING
        return self._path

    @path.setter
    def path(self, path):
        """
        Sets the path-variable addition and resets the prefix attribute

        :param:

         - `path`: path-variable addition or None
        """
        self._prefix = None
        if path is not None:
            self._path = "PATH={0}:$PATH;".format(path)
        else:
            self._path = path
        return

    @property
    def prefix(self):
        """
        A prefix-string to add to the commands

        :rtype: String
        :return: prefix string
        """
        if self._prefix is None:
            self._prefix = self.path
            self._prefix += self.library_path
            self._prefix += self.command_prefix
        return self._prefix

    @property
    def lock(self):
        """
        This is a lock that users of this connection should use before calling in case others are also calling

         * this is primarily for threaded users
        
        :return: a re-entrant lock
        """
        if self._lock is None:
            self._lock = threading.RLock()
        return self._lock   

    def _procedure_call(self, command, arguments='', timeout=None):
        """
        By default it acts as a decorator, adding the path to the command and returning _main

        * but it isn't implemented as a decorator since _main is an abstract method
        """
        command = self.prefix + command
        return self._main(command, arguments, timeout)

    @abstractmethod
    def _main(self, command, arguments='', timeout=None):
        """
        The main execution method.
        
        :param:

         - `command`: the command string to execute
         - `arguments`: The arguments for the command
         - `timeout`: A timeout for the queue when doing a get

        :return: OutputError named tuple
        """
        return OutputError(StringIO(''),StringIO( "'{0} {1}' timed out".format(command, arguments)))

    def __getattr__(self, command):
        """
        The parameters are the same as _procedure_call()
        
        :param:

         - `command`: The command to call.

        :return: _procedure_call method called with passed-in args and kwargs
        """
        def procedure_call(*args, **kwargs):
            return self._procedure_call(command, *args, **kwargs)
        return procedure_call

    def __call__(self, command, arguments='', timeout=None):
        """
        A pass-through to the _main method to use when the dot-notation doesn't work

        :param:

         - `command`: the command string to execute
         - `arguments`: The arguments for the command
         - `timeout`: A timeout for the queue when doing a get

        :return: OutputError named tuple
        """
        return self._procedure_call(command=command, 
                                    arguments=arguments, timeout=timeout)        

    def __str__(self):
        return "{0}".format(self.__class__.__name__)
# end NonLocalConnection


class NonLocalConnectionBuilder(object):
    """
    A base-plugin class for non-local connections
    """
    def __init__(self):
        """
        NonLocalConnectionBuilder Constructor

        """
        self._hostname = None
        self._username = None
        self._password = None
        self._operating_system = None
        self._port = None
        self._path = None
        self._library_path = None

        self._parameters = None
        self._product = None
        self._logger = None
        return

    @property
    def parameters(self):
        """
        The parameters to build the connection

        :return: the parameters given to build the connection
        """
        if self._parameters is None:
            raise ConfigurationError("{0}: self.parameters need to be set".format(self.__class__))
        return self._parameters

    @parameters.setter
    def parameters(self, parameters):
        """
        Sets the parameters

        :param:

         - `parameters`: a named-tuple with parameters to build the connection
        """
        self._parameters = parameters
        return

    @property
    def logger(self):
        """
        A logger built for this class to use

        :rtype: logging.Logger
        :return: a logger registered to this class
        """
        if self._logger is None:
            self._logger = logging.getLogger(DOT_JOIN.format(self.__module__,
                                  self.__class__.__name__))
        return self._logger

    @property
    def product(self):
        """
        The built connection.
        """
        raise NotImplementedError("NonLocalConnectionBuilder.product: This needs to be implemented")
        return        


ConnectionParameters = namedtuple("ConnectionParameters", ["hostname","username",
                                                           "password", 'operating_system',
                                                           "path", 'library_path', 'port'])


# python standard library
import unittest
import random
import string
#third party
from mock import MagicMock
from nose.tools import raises


class BadChild(NonLocalConnection):
    def __init__(self, *args, **kwargs):
        return
# end bad Child

class GoodChild(NonLocalConnection):
    def _main(self, command, arguments='', timeout=None):
        return

    @property
    def port(self):
        return

    @property
    def client(self):
        return

MESSAGE = "Expected: {0}, Actual: {1}"    
    
class TestNonLocalConnection(unittest.TestCase):
    def setUp(self):
        self.connection = GoodChild(hostname='local', username='bub')
        self.command = 'ummagumma'
        return
    
    @raises(TypeError)
    def test_main(self):
        """
        Does it raise an error if the main method isn't implemented?
        """
        connection  = BadChild(hostname='local', username='bob')
        return

    def prefix_check(self, expected):
        """
        Checks that connection.prefix + command equals the expected
        """
        actual = self.connection.prefix + self.command
        self.assertEqual(expected, actual,
                         msg="Expected: {0}, Actual: {1}".format(expected,
                                                                 actual))
        return
    
    def test_add_path(self):
        """
        If the path and/or library paths are set, does it add them to the command?
        """
        expected = self.command
        self.prefix_check(expected)

        self.connection.path = "ape"
        expected = "PATH=ape:$PATH;" + self.command        
        self.prefix_check(expected)

        self.connection.library_path = 'cow'
        expected = 'PATH=ape:$PATH;export LD_LIBRARY_PATH=cow:$LD_LIBRARY_PATH;' + self.command
        self.prefix_check(expected)
        self.connection.path = None
        expected = "export LD_LIBRARY_PATH=cow:$LD_LIBRARY_PATH;" + self.command
        self.prefix_check(expected)
        return

    def test_command_prefix(self):
        """
        If the command_prefix is set, does it add it to the command?
        """
        prefix = 'adb shell'
        expected = self.command
        self.prefix_check(expected)
        
        self.connection.command_prefix = prefix
        expected = prefix + SPACE + self.command
        self.prefix_check(expected)

        self.connection.path = "ape"
        expected = "PATH=ape:$PATH;" + prefix + SPACE + self.command        
        self.prefix_check(expected)

        self.connection.library_path = 'cow'
        
        expected = ('PATH=ape:$PATH;export LD_LIBRARY_PATH=cow:$LD_LIBRARY_PATH;' +
                    prefix + SPACE + self.command)
        self.prefix_check(expected)
        self.connection.path = None
        expected = ("export LD_LIBRARY_PATH=cow:$LD_LIBRARY_PATH;" +
                    prefix + SPACE + self.command)
        self.prefix_check(expected)
        return


    def test_getattr(self):
        """
        Does it add the path to the command then call _procedure_call()?
        """
        main = MagicMock()
        self.connection._main = main
        self.connection.path = 'ape'
        
        command = 'cow'
        arguments = '-a'
        timeout = 1
        self.connection.cow(arguments, timeout)
        main.assert_called_with('PATH=ape:$PATH;' + command, arguments, timeout)        

        return        


class TestNonLocalConnectionBuilder(unittest.TestCase):
    def setUp(self):       
        self.builder = NonLocalConnectionBuilder()
        return
    
    @raises(NotImplementedError)
    def test_product(self):
        """
        Does the product raise an error if not re-implemented?
        """
        parameters = MagicMock()
        builder = NonLocalConnectionBuilder()
        builder.parameters = parameters
        builder.product
        return

    def test_attributes(self):
        """
        Does the builder have the attributes promised by the API?
        """
        self.assertIsInstance(self.builder.logger, logging.Logger)
        with self.assertRaises(NotImplementedError):
            self.builder.product
        self.assertIsNone(self.builder._parameters)
        with self.assertRaises(ConfigurationError):
            self.builder.parameters
        return
