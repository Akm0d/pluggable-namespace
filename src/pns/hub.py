import sys

import pns.dir
import pns.data
import pns.contract
from ._debug import DEBUG_PNS_GETATTR

CONTRACTS_DIR = "contract"

if DEBUG_PNS_GETATTR:
    from pns._hub import DynamicNamespace
else:
    from pns._chub import DynamicNamespace  # type: ignore


class Sub(DynamicNamespace):
    """
    Represents a sub-component or module that can be dynamically added to a Hub.

    Each Sub can contain its own sub-components, allowing a hierarchical structure similar
    to a namespace or module path in a software architecture.

    Attributes:
        hub: Reference to the root Hub instance.
        contracts: A list of contract definitions associated with this Sub.
    """

    def __init__(
        self,
        name: str,
        parent: "Sub",
        root: "Hub",
        locations: list[str] = (),
        contract_locations: list[str] = (),
    ):
        """
        Initializes a Sub instance.

        Args:
            name (str): The name of the Sub component.
            parent (data.Namespace): The parent namespace of this Sub.
            root (Hub): The root Hub instance that this Sub is part of.
        """
        super().__init__(name, parent=parent, root=root)
        # Modules loaded onto this namespace
        self._dir = pns.dir.walk(locations)
        # Find contracts within the dirs
        self._contract_dir = pns.dir.walk(contract_locations)
        self._contract_dir.extend(pns.dir.inline(self._dir, CONTRACTS_DIR))

    @property
    def contract(self):
        return self._contract_dir

    async def add_sub(self, name: str, locations: list[str] = ()):
        """
        Adds a sub-component or module to this Sub.

        Args:
            name (str): The name of the sub-component to add.
        """
        if name in self._nest:
            return
        if not self._active:
            # TODO also call the sub's init.__virtual__ function and act based on the result
            return

        current = self
        parts = name.split(".")
        # Iterate over all parts except the last one
        for part in parts[:-1]:
            if part not in current._nest:
                current = current._add_child(part, cls=Sub)

        # Only in the last iteration, use locations
        last_part = parts[-1]
        sub = Sub(last_part, root=self._root or self, parent=self, locations=locations)

        current._nest[last_part] = sub

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

    _last_ref: str = None
    _last_call: str = None
    _dynamic: dict = None

    def __init__(hub):
        """
        Initializes the hub, setting itself as its own root and setting up core namespaces.
        """
        super().__init__(name="hub", parent=None, root=None)
        # Add a place for sys modules to live
        hub += "lib"
        hub.lib._nest = sys.modules
        hub._dynamic = hub.lib.pns.dir.dynamic()

    @classmethod
    async def new(cls):
        """
        Initialize a hub with async capabilities
        """
        hub = cls()
        # Make sure the logging functions are available as early as possible
        # NOTE This is how to add a dyne
        await hub.add_sub(name="log", locations=hub._dynamic.dyne.log.paths)
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
        return self.lib.pns.ref.last(self, last_mod)

    def __repr__(hub):
        return "Hub()"
