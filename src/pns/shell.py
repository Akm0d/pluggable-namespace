"""
This module introduces the CMD class, an extension of the pns.hub.Sub,
designed to facilitate executing shell commands directly from a hub namespace.
It dynamically creates methods corresponding to shell commands,
allowing users to execute these commands as methods of the CMD instance.

I.e.:
    await hub.sh.ls()
    await hub.sh.grep('pattern')


Features:
- Dynamic command execution: Allows calling any shell command as an attribute of the CMD instance.
- Output handling: Methods to handle different outputs such as plain text, JSON, or error output.
- Asynchronous execution: All commands are executed asynchronously, utilizing asyncio to manage subprocesses.

The CMD class integrates deeply with the system's hub, making it easy to execute and manage shell commands from any part of the application using the namespace-oriented architecture.
"""

import pns.hub
from collections.abc import AsyncGenerator


class CMD(pns.hub.Sub):
    """
    A class that facilitates the execution of shell commands from the hub namespace.

    The CMD class dynamically generates methods corresponding to shell commands, allowing these commands to be called as if they were regular methods.
    It supports passing arguments and handling output in various formats.

    Attributes:
        command (list[str]): The base command represented as a list of strings, ready to be executed.

    Initialization Parameters:
        hub (pns.hub.Hub): The global hub instance representing the root namespace.
        command (list[str] | str, optional): The initial command or list of command segments. Defaults to an empty list.
        parent (pns.hub.Sub, optional): The parent sub-namespace.
    """

    def __init__(self, hub: pns.hub.Hub, command: list[str] | str = None, parent=None):
        """
        Initializes a CMD instance that allows for executing shell commands dynamically from the hub.

        This constructor prepares a CMD object to be accessible under the 'sh' namespace within the hub.
        It sets up the initial state to handle dynamic access to command execution. Commands can be
        executed by calling them as methods of this instance (e.g., hub.sh.ls()). If specific command
        segments are provided during initialization, they form the base command that can be extended
        dynamically through attribute access.

        Parameters:
            hub (pns.hub.Hub): The global hub instance representing the root namespace. This is where
                the CMD instance will be integrated, allowing access to system commands via the hub.
            command (list[str] | str, optional): The base command or an initial segment of the command.
                If a string is provided, it is converted into a list. If nothing is provided, it initializes
                to an empty list which will wait for dynamic method access to specify commands.
            parent (pns.hub.Sub, optional): The parent namespace under which this CMD instance is nested.
                Typically, this will be the hub itself when integrating the CMD as 'hub.sh'.

        Examples:
            To create an instance without any initial commands, which will be specified later dynamically:
            >>> hub._nest["sh"] = CMD(hub, parent=hub)

            To execute a command directly:
            >>> await hub.sh.ls('-la')  # Executes 'ls -la' in the shell and returns the output.
        """
        if not command:
            command = []
        if isinstance(command, str):
            command = [command]
        self.command = command
        super().__init__(name="sh", parent=parent, root=hub)

    def __getattr__(self, name):
        """
        Dynamically handles attribute access to support calling any shell command as a method.

        Parameters:
            name (str): The name of the command or subcommand to access.

        Returns:
            CMD: A new CMD instance with the command appended to the existing command list.
        """
        return CMD(self._, self.command + [name], parent=self)

    def __getitem__(self, item):
        """
        Allows for dictionary-like access to methods corresponding to shell commands.

        Parameters:
            item (str): The command or subcommand to access as if accessing a dictionary.

        Returns:
            CMD: The corresponding CMD instance for the command.
        """
        return getattr(self, item)

    def __bool__(self):
        """
        Evaluate the truthiness of this CMD instance, which checks if the command is executable.

        Returns:
            bool: True if the command can be found and executed on the system; otherwise, False.
        """
        if self.command:
            return bool(self.hub.lib.shutil.which(self.command[0]))
        return True

    def __str__(self):
        """
        Provides a human-readable representation of the CMD instance, primarily showing the executable path of the command.

        Returns:
            str: The full path to the command if it exists, otherwise a string representation of the CMD object.
        """
        if self.command:
            return self.hub.lib.shutil.which(self.command[0])
        return self.__repr__()

    async def _execute_command(self, *args, **kwargs):
        """
        Execute the shell command associated with this CMD instance asynchronously, handling both stdout and stderr.

        Parameters:
            args (tuple): Positional arguments passed to the command.
            kwargs (dict): Keyword arguments that will be forwarded to `asyncio.create_subprocess_exec`.

        Returns:
            asyncio.subprocess.Process: The process object representing the running command.

        Raises:
            OSError: If there is an issue starting the command.
        """
        cmd = self.command[0]
        proc = await self._.lib.asyncio.create_subprocess_exec(
            cmd,
            *args,
            stdout=self._.lib.asyncio.subprocess.PIPE,
            stderr=self._.lib.asyncio.subprocess.PIPE,
            **kwargs,
        )
        return proc

    async def __call__(self, *args, **kwargs):
        """
        Executes the configured command with any additional arguments and keyword arguments.

        Parameters:
            args (tuple): Arguments to pass to the command.
            kwargs (dict): Keyword arguments to control subprocess execution and handle its output.

        Returns:
            str: The standard output from the command execution.
        """
        return await self.stdout(*args, **kwargs)

    async def __aiter__(self) -> AsyncGenerator[str]:
        """
        Allows iterating over the lines of the command's output as if iterating over a file object.

        Yields:
            str: Each line of output from the command execution.
        """
        async for line in self.lines():
            yield line

    async def lines(self, *args, **kwargs) -> AsyncGenerator[str]:
        """
        Asynchronously yields lines from the standard output of the command.

        Parameters:
            args (tuple): Additional arguments for the command.
            kwargs (dict): Options for subprocess execution.

        Yields:
            str: Each line from the command's standard output, decoded and stripped of trailing newlines.
        """
        proc = await self._execute_command(*args, **kwargs)
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            yield line.decode("utf-8").strip()

    async def json(self, *args, **kwargs) -> object:
        """
        Execute the command and parse its output as JSON.

        Parameters:
            args (tuple): Arguments to pass to the command.
            kwargs (dict): Options to pass to the subprocess execution.

        Returns:
            any: The JSON-decoded output of the command.
        """
        stdout = await self.__call__(*args, **kwargs)
        return self.hub.lib.json.loads(stdout)

    async def stderr(self, *args, **kwargs) -> str:
        """
        Retrieves the standard error output of the command.

        Parameters:
            args (tuple): Arguments for the command.
            kwargs (dict): Options for the subprocess execution.

        Returns:
            str: The standard error output from the command, decoded.
        """
        proc = await self._execute_command(*args, **kwargs)
        _, stderr = await proc.communicate()
        return stderr.decode("utf-8")

    async def stdout(self, *args, **kwargs) -> str:
        """
        Retrieves the standard output of the command.

        Parameters:
            args (tuple): Arguments for the command.
            kwargs (dict): Options for the subprocess execution.

        Returns:
            str: The standard output from the command, decoded.
        """
        proc = await self._execute_command(*args, **kwargs)
        stdout, _ = await proc.communicate()
        return stdout.decode("utf-8")
