import asyncio
import sys
import pns.dir
import pns.data
import pns.ref

from ._debug import DEBUG_PNS_GETATTR

if DEBUG_PNS_GETATTR:
    from pns._hub import Namespace
else:
    from pns._chub import Namespace # type: ignore



class Sub(Namespace):
    """
    Represents a sub-component or module that can be dynamically added to a Hub.

    Each Sub can contain its own sub-components, allowing a hierarchical structure similar
    to a namespace or module path in a software architecture.

    Attributes:
        hub: Reference to the root Hub instance.
        contracts: A list of contract definitions associated with this Sub.
    """


    def __init__(self, name: str, parent: Namespace, root: "Hub"):
        """
        Initializes a Sub instance.

        Args:
            name (str): The name of the Sub component.
            parent (data.Namespace): The parent namespace of this Sub.
            root (Hub): The root Hub instance that this Sub is part of.
        """
        super().__init__(name, parent=parent, root=root)
        self.hub = root or parent


    async def add_sub(self, name: str, recurse: bool = True, **kwargs):
        """
        Adds a sub-component or module to this Sub.

        Args:
            name (str): The name of the sub-component to add.
            module_ref (str, optional): The module reference to load. Defaults to None.
            recurse (bool): If True, recursively loads submodules. Defaults to True.
        """
        if name in self._nest:
            return
        if not self._virtual:
            # TODO also call the sub's init.__virtual__ function and act based on the result
            return

        sub = self._add_child(name=name, **kwargs)

        # Propagate the parent's recursive contracts
        sub._rcontracts = self._rcontracts

        return sub

class Hub(Sub):
    """
    Represents the central hub of the modular system.

    Inherits from Sub, but designed to be the root and primary interface for interacting with
    the subsystem architecture.

    Attributes:
        _last_ref: The last reference accessed.
        _last_call: The last call made through the hub.
        _dynamic: A dynamic configuration or state connected to the directory structure.
    """

    _last_ref = None
    _last_call = None
    _dynamic = None

    def __init__(hub):
        """
        Initializes the hub, setting itself as its own root and setting up core namespaces.
        """
        super().__init__(name="hub", parent=hub, root=hub)
        hub.hub = hub
        # Add a place for sys modules to live
        hub += "lib"
        hub._dynamic = pns.dir.dynamic()
        hub.lib._nest = sys.modules

        # Make sure the logging functions are available as early as possible
        # NOTE This is how to add a dyne
        hub._add_child(name="log", static=hub._dynamic.dyne.log.paths)

    @classmethod
    async def new(cls):
        """
        Initialize a hub with async capabilities
        """
        hub = cls()
        # Load all the modules on hub.log
        await hub.log._load_all()
        await hub.log.debug("Initialized the hub")
        return hub

    @property
    def _(self):
        """
        Return the parent of the last contract.
        This allows modules to easily reference themselves with shorthand.
        i.e.

            hub._.current_module_attribute
        """
        if not self._last_ref:
            return self
        # Remove the entry from the call stack
        last_mod = self._last_ref.rsplit(".", maxsplit=1)[0]
        return pns.ref.last(self, last_mod)

    def __repr__(hub):
        return "Hub()"


class CMD(Sub):
    """
    A class representing a shell command execution interface that allows accessing
    shell commands through a namespace-like structure on a Hub object.
    """

    def __init__(self, hub: Hub, command: list[str] | str = None, parent=None):
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
        super().__init__(name="sh", parent=parent or hub, root=hub)

    def __getattr__(self, name):
        """
        Allows accessing additional command parts via attribute access.

        Args:
            name (str): The next part of the command to add.

        Returns:
            CMD: A new CMD instance with the extended command.
        """
        return CMD(self.hub, self.command + [name], parent=self)

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
        return self.hub.lib.shutil.which(self.command[0])

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
        proc = await asyncio.create_subprocess_exec(
            cmd,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
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
