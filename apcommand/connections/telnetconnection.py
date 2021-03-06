
#python Libraries
from StringIO import StringIO
import os.path
import telnetlib
import time

# this package
from apcommand.baseclass import BaseClass
from apcommand.commands import changeprompt

# connections
from apcommand.commons.readoutput import ValidatingOutput
from nonlocalconnection import NonLocalConnection, NonLocalConnectionBuilder
from localconnection import OutputError


NEWLINE = '\n'
SPACER = '{0} {1}'
UNKNOWN = "Unknown command: "
EMPTY_STRING = EOF = ''
PLUGIN_NAME = 'telnet'


class OutputFile(ValidatingOutput):
    """
    A class to handle the ssh output files

    This traps socket timeouts.
    """
    def __init__(self, *args, **kwargs):
        super(OutputFile, self).__init__(*args, **kwargs)
        return

    def readline(self, timeout=10):
        """
        :param:

         - `timeout`: The length of time to wait for output

        :return: line from readline, EOF or None (in event of timeout)
        """
        if not self.empty:
            try:
                line = self.lines.readline()
                if line == EOF:
                    self.end_of_file = True
                self.validate(line)
                return line
            except socket.timeout:
                self.logger.debug("socket.timeout")
                return SPACE
        return EOF
# end class OutputFile


class TelnetAdapter(BaseClass):
    """
    A TelnetAdapter Adapts the telnetlib.Telnet to this libraries interfaces.
    """
    def __init__(self, host, prompt="#", login='root', password=None, port=23, timeout=2, end_of_line='\r\n',
                 login_prompt="login:"):
        """
        :param:

         - `host`: The address of the telnet server
         - `prompt`: The prompt used on the device
         - `port`: The port of the telnet server
         - `login`: The login (if needed)
         - `timeout`: The timeout for blocking methods
         - `end_of_line`: The end of line string used by the device.
         - `login_prompt`: The prompt to look for when starting a connection.
         - `password`: if given tries to login
        """
        super(TelnetAdapter, self).__init__()
        self.host = host
        self.password = password
        self.prompt = prompt
        self.login = login
        self.port = port
        self.timeout = timeout
        self.end_of_line = end_of_line
        self._client = None
        self.login_prompt = login_prompt
        return

    @property
    def client(self):
        """
        Tries to login before returning.

        :rtype: telnetlib.Telnet
        :return: The telnet client
        """
        if self._client is None:
            self._client = telnetlib.Telnet(host=self.host, port=self.port,timeout=self.timeout)
            possibilities = [self.prompt, self.login_prompt]
            output = self._client.expect(possibilities, timeout=self.timeout)
            if output[0] == 1:
                self._client.write(self.login + NEWLINE)
                if self.password is not None:
                    output = self._client.read_until("Password: ", timeout=self.timeout)
                    self._client.write(self.password + NEWLINE)
        return self._client

    def exec_command(self, command, timeout=10):
        """
        The main interface.

        Since I'm hiding the client from users, this will do a read_very_eager before continuing.
        The read is intended to try and flush the output

        :param:

         - `command`: The command to execute on the device
         - `timeout`: The readline timeout

        :return: TelnetOutput with the this object's as client
        """
        self.client.timeout = timeout
        self.logger.debug("In queue: " + self.client.read_very_eager())
        self.logger.debug("Sending the command: " + command)
        self.writeline(command)
        return TelnetOutput(client=self.client, prompt=self.prompt,
                            timeout=self.timeout, end_of_line=self.end_of_line)
                           
    
    def writeline(self, message=""):
        """
        :param:

         - `message`: A message to send to the device.
        """
        self.client.write(message.rstrip(NEWLINE) + NEWLINE)
        return
    
    def __del__(self):
        self.client.close()
        return
# end class TelnetAdapter


MATCH_INDEX = 0
MATCHING_STRING = 2


class TelnetOutput(BaseClass):
    """
    The TelnetOutput converts the telnet output to a file-like object
    """
    def __init__(self, client, prompt="#", end_of_line='\r\n',timeout=10):
        """
        TelnetOutput constructor
        
        :param:

         - `client` : a connected telnet client
         - `prompt`: The current prompt on the client
         - `end_of_line`: Then end of line character
         - `timeout`: The readline timeout
        """
        super(TelnetOutput, self).__init__()
        self.client = client
        self.prompt = prompt
        self.end_of_line = end_of_line
        self.timeout = timeout
        self.endings = [end_of_line, prompt]
        self.line_ending_index = 0
        self.finished = False
        return

    def readline(self, timeout=None):
        """
        Gets a single line of output from the output
        
        :param:

         - `timeout`: The readline timeout
         
        :return: The next line of text
        """
        if timeout is None:
            timeout = self.timeout

        output = self.client.expect(self.endings, timeout)
        if self.finished:
            return EOF
        elif output[MATCH_INDEX] == self.line_ending_index:
            return output[MATCHING_STRING]
        else:
            # matched the prompt, this output is finished
            self.logger.debug("Stopping on : " + output[MATCHING_STRING])
            self.finished = True
        return EOF

    def next(self):
        """
        Generator of lines
        
        :yield: the next line
        """
        while not self.finished:
            yield self.readline()
        return

    def readlines(self):
        """
        Converts output to a list of lines
        
        :return: A list of lines
        """
        lines = []
        line = None
        while line != EOF:
            line = self.readline()
            lines.append(line)
        return lines

    def read(self):
        """
        Converts output to a string

        :return: String of output        
        """
        return EMPTY_STRING.join(self.readlines())

    def __iter__(self):
        """
        Iterator over output (this is an alias of next())
        """
        return self.next()
# end TelnetOutput


class TelnetConnection(NonLocalConnection):
    """
    A TelnetConnection executes commands over a Telnet Connection

    """
    def __init__(self, port=None, prompt="#", end_of_line='\r\n',
                 mangle_prompt=True, login_wait=1,
                 *args, **kwargs):
        """
        TelnetConnection constructor
        
        :param:

         - `hostname`: The IP Address or hostname
         - `port`: The telnet port 
         - `username`: The login name
         - `prompt`: The prompt to expect
         - `timeout`: The readline timeout
         - `end_of_line`: The string indicating the end of a line.
         - `mangle_prompt`: If True, change the prompt
         - `login_wait`: time to wait after logging in
        """
        super(TelnetConnection, self).__init__(*args, **kwargs)
        self._port = port
        self.port = port
        self.prompt = prompt
        self.end_of_line = end_of_line
        self.mangle_prompt = mangle_prompt
        self.login_wait = login_wait
        return

    @property
    def port(self):
        """
        The port for the telnet server

        :rtype: Integer
        :return: port number
        """
        if self._port is None:
            self._port = 23
        return self._port

    @port.setter
    def port(self, port):
        """
        Sets the port for the telnet server

        :param:

         - `port`: integer port number
        """
        self._port = port
        return
    
    @property
    def client(self):
        """
        :return: TelnetAdapter for the telnet connection
        """
        if self._client is None:
            self._client = TelnetAdapter(host=self.hostname, 
                                         login=self.username, port=self.port,
                                         timeout=self.timeout,
                                         end_of_line=self.end_of_line,
                                         password=self.password,
                                         prompt=self.prompt)
            if self.mangle_prompt:
                changer = changeprompt.ChangePrompt(adapter=self._client)
                self.logger.debug(changer.run())
            self.logger.debug('Sleeping for {0} seconds to let the login complete'.format(self.login_wait))
            time.sleep(self.login_wait)
        return self._client
    
    def _main(self, command, arguments="",
                        timeout=10):
        """
        Despite its name, this isn't intended to be run.
        The . notation is the expected interface.
        
        runs the SimpleClient exec_command and puts lines of output on the Queue

        :param:

         - `command`: The shell command.
         - `arguments`: A string of command arguments.
         - `timeout`: readline timeout

        :postcondition: OutputError with output and error file-like objects
        """
        self.logger.debug("calling 'client.exec_command({0})'".format(command))
        stdout = self.client.exec_command(SPACER.format(command, arguments),
                                          timeout=timeout)
        self.logger.debug("Completed 'client.exec_command({0})'".format(command))       

        stderr = StringIO("")

        return OutputError(OutputFile(stdout, self.validate), stderr)

    exec_command = _main

    def validate(self, line):
        return
# end TelnetConnection


class TelnetConnectionBuilder(NonLocalConnectionBuilder):
    """
    Implements a builder for the TelnetConnection
    """
    def __init__(self, *args, **kwargs):
        """
        TelnetConnectionBuilder Constructor

        :param:

         - `parameters`: namedtuple of parameters to build the connection
        """
        super(TelnetConnectionBuilder, self).__init__(*args, **kwargs)
        return

    @property
    def port(self):
        """
        Port for the Telnet-server

        :return: the ConnectionParameters.port value
        """
        if self._port is None:
            self._port = self.parameters.port
        return self._port
    
    @property
    def operating_system(self):
        """
        :return: parameters.operating_system
        """
        if self._operating_system is None:
            try:
                self._operating_system = self.parameters.operating_system
            except AttributeError as error:
                self.logger.debug(error)
                self.logger.warning("Operating System not found in: {0}".format(self.parameters))
        return self._operating_system

    @property
    def library_path(self):
        """
        :return: LD_LIBRARY_PATH value(s) or None
        """
        if self._library_path is None:
            try:
                self._library_path = ":".join(self.parameters.library_path.split())
            except AttributeError as error:
                self.logger.debug(error)
        return self._library_path

    @property
    def path(self):
        """
        :return: additions to the PATH
        """
        if self._path is None:
            try:
                self._path = ":".join(self.parameters.path.split())
            except AttributeError as error:
                self.logger.debug(error)
        return self._path
    
    @property
    def hostname(self):
        """
        The hostname parameter extracted from the parameters
        
        :rtype: StringType
        :return: The hostname (I.P.) to connect to
        :raise: ConfigurationError if not set
        """
        if self._hostname is None:
            try:
                self._hostname = self.parameters.hostname
            except AttributeError as error:
                self.logger.debug(error)
                try:
                    self._hostname = self.parameters.address
                except AttributeError as error:
                    self.logger.debug(error)
                    message = "`hostname` is a required parameter for the TelnetConnection"
                    raise errors.ConfigurationError(message)
        return self._hostname

    @property
    def username(self):
        """
        :rtype: StringType
        :return: user login name
        :raise: ConfigurationError if not found
        """
        if self._username is None:
            try:
                self._username = self.parameters.username
            except AttributeError as error:
                self.logger.debug(error)
                try:
                    self._username = self.parameters.login
                except AttributeError as error:
                    self.logger.debug(error)
                    raise errors.ConfigurationError("`username` is a required parameter for the TELNETConnection")                
        return self._username

    @property
    def password(self):
        """
        :return: the password for the connection (sets to None if not given in the parameters)
        """
        if self._password is None:
            try:
                self._password = self.parameters.password
            except AttributeError as error:
                self.logger.debug(error)
                self._password = None
        return self._password
    
    @property
    def product(self):
        """
        Implements the builder.product attribute
        
        :return: a Telnetconnection
        """
        if self._product is None:
            self.logger.debug("Creating the telnet connection.")
            self._product = TelnetConnection(hostname=self.hostname,
                                                           username=self.username,
                                                           password=self.password,
                                                           port=self.port,
                                                           path=self.path,
                                                           library_path=self.library_path,
                                                           operating_system=self.operating_system)
        return self._product
# end class TelnetConnectionBuilder


# python standard library
import unittest
from types import StringType


from nonlocalconnection import ConnectionParameters


class TestTelnetConnectionBuilder(unittest.TestCase):
    pass


if __name__ == "__main__":
    import time
    import sys
#    import curses.ascii
#    arguments = "-l"
    sc = TelnetConnection(hostname="10.10.10.21",
                          username='root',
                          password='5up')
#    sc.client.writeline(curses.ascii.crtl("c"))
    output = sc.iwconfig('ath0')
    time.sleep(1)
    for x in output.output:
        sys.stdout.write(x)

    output, error = sc.ifconfig('ath0')
    for line in output:
        sys.stdout.write(line)

#    output = sc.iwconfig('ath0')
#
#    for x in output.output:
#        print x
        
#
#    from time import sleep
#    sleep(0.1)
#    print "Testing ping"
#    output = sc.ping(arguments="-c 10 192.168.10.1", timeout=1)
#    for x in output.output:
#        print x
#
#    sleep(0.1)
#    print "Testing iperf"
#    output = sc.iperf('-i 1 -c 192.168.10.51')
#    for line in output.output:
#        print line
#
#    sleep(0.1)
#    print "Checking iperf version"
#    output = sc.iperf('-v')
#
#    print output.output.read()
#    print output.error.read()
#
#    ta = TelnetAdapter(host="192.168.10.172")
#    for line in ta.exec_command("iperf -c 192.168.10.51 -i 1"):
#        print line
