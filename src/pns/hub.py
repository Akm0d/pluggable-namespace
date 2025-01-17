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
        root: "Hub" = None,
        contract_locations: list[str] = (),
        **kwargs,
    ):
        """
        Initializes a Sub instance.

        Args:
            name (str): The name of the Sub component.
            parent (data.Namespace): The parent namespace of this Sub.
            root (Hub): The root Hub instance that this Sub is part of.
        """
        super().__init__(name=name, root=root, **kwargs)
        self._contract_dir = pns.dir.walk(contract_locations)
        self._contract_dir.extend(pns.dir.inline(self._dir, CONTRACTS_DIR))
        self.contract = None

    async def add_sub(self, name: str, **kwargs):
        """
        Adds a sub-component or module to this Sub.

        Args:
            name (str): The name of the sub-component to add.
        """
        if name in self._nest:
            return
        # If the current sub is not active, then don't waste time adding more subs
        if not self._active:
            return

        current = self
        parts = name.split(".")
        # Iterate over all parts except the last one
        for part in parts[:-1]:
            if part not in current._nest:
                current = current._add_child(part, cls=Sub)

        # Only in the last iteration, use locations
        last_part = parts[-1]

        sub = Sub(last_part, root=self._root or self, parent=self, **kwargs)
        await sub.load_contracts()

        current._nest[last_part] = sub

        return sub

    async def load_contracts(self):
        if not self._contract_dir:
            return

        if self.contract:
            return

        contract_sub = Sub(
            name=CONTRACTS_DIR,
            parent=self,
            root=self._root,
            locations=self._contract_dir,
        )
        await contract_sub._load_all(merge=False)
        self.contract = contract_sub


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
    _loop = None

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
        hub._loop = hub.lib.asyncio.get_event_loop()
        # Make sure the logging functions are available as early as possible
        # NOTE This is how to add a dyne
        await hub.add_sub(name="log", locations=hub._dynamic.dyne.log.paths)
        await hub.log._load_mod("init")
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
