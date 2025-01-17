import pns.hub


class CMD(pns.hub.Sub):
    """
    A class representing a shell command execution interface that allows accessing
    shell commands through a namespace-like structure on a Hub object.
    """

    def __init__(self, hub: pns.hub.Hub, command: list[str] | str = None, parent=None):
        """
        Initialize the CMD interface.

        Args:
            hub: The hub to which this CMD interface is attached.
            command (list[str] or str, optional): The initial command or command parts.
        """
        if not command:
            command = []
        if isinstance(command, str):
            command = [command]
        self.command = command
        super().__init__(name="sh", parent=parent, root=hub)

    def __getattr__(self, name):
        """
        Allows accessing additional command parts via attribute access.

        Args:
            name (str): The next part of the command to add.

        Returns:
            CMD: A new CMD instance with the extended command.
        """
        return CMD(self._, self.command + [name], parent=self)

    def __getitem__(self, item):
        """
        Allows accessing additional command parts via item access.

        Args:
            item (str): The next part of the command to add.

        Returns:
            CMD: A new CMD instance with the extended command.
        """
        return getattr(self, item)

    def __bool__(self):
        """
        Determines if the command is available on the host system.

        Returns:
            bool: True if the command is available, False otherwise.
        """
        return bool(self.hub.lib.shutil.which(self.command[0]))

    def __str__(self):
        """
        Provides a string representing the path of the executable command.

        Returns:
            str: The path to the executable, or None if it's not available.
        """
        if self.command:
            return self.hub.lib.shutil.which(self.command[0])
        return self.__repr__()

    async def _execute_command(self, *args, **kwargs):
        """
        Executes the command asynchronously with provided arguments.

        Args:
            *args: Positional arguments for the command.
            **kwargs: Keyword arguments for the command.

        Returns:
            Process: An asyncio subprocess process object.
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
        Execute the command and return the standard output.

        Args:
            *args: Positional arguments for the command.
            **kwargs: Keyword arguments for the command.

        Returns:
            str: Standard output of the executed command.
        """
        return await self.stdout(*args, **kwargs)

    async def __aiter__(self):
        """
        Allows iteration over the lines of the command's standard output.

        Yields:
            str: A line of output from the command.
        """
        async for line in self.lines():
            yield line

    async def lines(self, *args, **kwargs):
        """
        Executes the command and yields each line of standard output.

        Args:
            *args: Positional arguments for the command.
            **kwargs: Keyword arguments for the command.

        Yields:
            str: A line of output from the command.
        """
        proc = await self._execute_command(*args, **kwargs)
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            yield line.decode("utf-8").strip()

    async def json(self, *args, **kwargs):
        """
        Executes the command and parses the standard output as JSON.

        Args:
            *args: Positional arguments for the command.
            **kwargs: Keyword arguments for the command.

        Returns:
            dict: Parsed JSON output.
        """
        stdout = await self.__call__(*args, **kwargs)
        return self.hub.lib.json.loads(stdout)

    async def stderr(self, *args, **kwargs):
        """
        Executes the command and returns the standard error output.

        Args:
            *args: Positional arguments for the command.
            **kwargs: Keyword arguments for the command.

        Returns:
            str: Standard error of the executed command.
        """
        proc = await self._execute_command(*args, **kwargs)
        _, stderr = await proc.communicate()
        return stderr.decode("utf-8")

    async def stdout(self, *args, **kwargs):
        """
        Executes the command and returns the standard output.

        Args:
            *args: Positional arguments for the command.
            **kwargs: Keyword arguments for the command.

        Returns:
            str: Standard output of the executed command.
        """
        proc = await self._execute_command(*args, **kwargs)
        stdout, _ = await proc.communicate()
        return stdout.decode("utf-8")
