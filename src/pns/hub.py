"""
Central management and dynamic module loading for pluggable-namespace applications.

This module provides core functionality for dynamically managing namespaces and modules
in a pluggable-namespace application architecture. By leveraging classes such as Hub and Sub,
it facilitates a structured approach to adding and managing sub-components and modules at runtime,
thereby enabling a flexible, scalable, and maintainable architecture.

Key components:
- Hub: Acts as the central node in the namespace hierarchy, functioning as a global 'self'
    variable that is the entry point to the application's modular system.
- Sub: Represents a sub-component or module within the Hub, capable of dynamically loading
    further sub-components or modules.

The module ensures that each component in the namespace can dynamically interact with others,
adhering to a design that promotes loose coupling and high cohesion. Compiled with Cython for
performance optimization, it includes conditional imports based on debug status to switch
between development and production-ready code paths.
"""

import contextvars
import sys

import pns.dir
import pns.data
import pns.contract
from ._debug import DEBUG_PNS_GETATTR

CONTRACTS_DIR = "contract"

if DEBUG_PNS_GETATTR:
    # Import the pure python version of DynamicNamespace
    from pns._hub import DynamicNamespace
else:
    # Import the cython-optimized version of DynamicNamespace
    from pns._chub import DynamicNamespace  # type: ignore


class Sub(DynamicNamespace):
    """
    Represents a sub-component or module that can be dynamically added to a Hub.
    Each Sub can contain its own sub-components, allowing a hierarchical structure similar
    to a namespace or module path in a software architecture.

    Attributes:
        hub (Hub): Reference to the root Hub instance, facilitating access to global state and utilities.
        contracts (list): A list of contract definitions associated with this Sub for managing interactions.
    """

    def __init__(
        self,
        name: str,
        root: "Hub" = None,
        contract_locations: list[str] = (),
        **kwargs,
    ):
        """
        Initializes a Sub instance with specified parameters.

        Args:
            name (str): The name of the Sub component.
            root (Hub, optional): The root Hub instance that this Sub is part of.
            contract_locations (list[str]): Directories to search for contract definitions.
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

        Returns:
            Sub: The newly added sub-component or None if the sub-component already exists.
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
        """
        Loads and initializes contract definitions for this Sub.
        """
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


_LAST_REF = contextvars.ContextVar("_last_ref", default=None)
_LAST_CALL = contextvars.ContextVar("_last_call", default=None)


class Hub(Sub):
    """
    Represents the central hub of the modular system. It is the root node of the dynamic namespace,
    providing a primary interface for interacting with the entire subsystem architecture.

    Attributes:
        _last_ref (str): The last reference accessed through the Hub, used for debugging and tracking.
        _last_call (str): The last call made through the Hub, used for operational monitoring.
        _dynamic (dict): A dynamic configuration or state connected to the directory structure.
    """

    _dynamic: dict = None
    _loop = None

    def __init__(hub):
        """
        Initializes the hub, setting itself as the root and setting up core namespaces.
        """
        super().__init__(name="hub", parent=None, root=None)
        # Add a place for sys modules to live
        hub += "lib"
        hub.lib._nest = sys.modules
        hub._dynamic = hub.lib.pns.dir.dynamic()

    @classmethod
    async def new(cls):
        """
        Asynchronously initializes a Hub with capabilities for dynamic module management.

        Returns:
            Hub: A newly initialized Hub instance with asynchronous capabilities.
        """
        hub = cls()
        hub._loop = hub.lib.asyncio.get_event_loop()
        # Make sure the logging functions are available as early as possible
        # NOTE This is how to add a dyne
        await hub.add_sub(name="log", locations=hub._dynamic.dyne.log.paths)
        await hub.log._load_mod("init")
        return hub

    @property
    def _last_ref(self):
        """
        Property to access the coroutine-local _last_ref value using the context variable.
        """
        return _LAST_REF.get()

    @_last_ref.setter
    def _last_ref(self, value):
        """
        Property setter to update the coroutine-local _last_ref value using the context variable.
        """
        _LAST_REF.set(value)

    @property
    def _last_call(self):
        """
        Property to access the coroutine-local _last_call value using the context variable.
        """
        return _LAST_CALL.get()

    @_last_call.setter
    def _last_call(self, value):
        """
        Property setter to update the coroutine-local _last_call value using the context variable.
        """
        _LAST_CALL.set(value)

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
        """
        Represents the Hub as a string for debugging and logging purposes.

        Returns:
            str: A simple string representation of the Hub.
        """
        return "Hub()"
