"""
This is a Cython-compiled module providing dynamic namespace management and module loading.

This module, designed for integration with Cython, facilitates seamless and efficient
stepping into and out of namespaces without the need to directly manipulate the internals
of pluggable namespaces. It provides a DynamicNamespace class that supports on-demand
loading of modules from specified directory locations, ensuring that the addition and
management of new modules are both flexible and performant.

The primary functionality of this module revolves around extending and utilizing the capabilities
of the pns.data.Namespace to create a more dynamic namespace system where modules can be loaded
or accessed dynamically based on runtime requirements. This allows developers to expand their
application's functionality dynamically with minimal setup and without restarting the application.

Components of _hub.py are designed to be directly imported into hub.py, facilitating a structured
and organized approach to namespace and module management in larger applications. By compiling
this module with Cython, the performance is enhanced, particularly in environments where dynamic
access patterns and high-efficiency module management are critical.

Key Features:
- Dynamic loading and caching of modules to enhance performance and flexibility.
- Direct integration into the hub system for easy access and management of namespaces.
- Cython compilation to improve the execution speed and reduce runtime overhead.

This module is particularly useful in applications requiring a high degree of modularity
and dynamic adaptability, making it ideal for large-scale projects where performance
and maintainability are paramount.
"""

import asyncio
import pns.data
import pns.loop
import pkgutil

# Constants for special attributes
INIT = "__init__"
SUB_ALIAS = "__sub_alias__"


class DynamicNamespace(pns.data.Namespace):
    """
    A namespace that dynamically loads and manages modules from specified directory locations.

    This class extends `pns.data.Namespace` to add functionality for dynamic module loading.
    Modules can be loaded on-demand when they are first accessed. This allows for a flexible
    and extensible system where modules can be added without restarting the application.

    Attributes:
        _dir (iterator): An iterator over directories to search for modules.
        _mod (dict): A dictionary to store loaded modules.

    Methods:
        __init__: Initializes a new DynamicNamespace instance.
        __getattr__: Provides attribute access, loading modules dynamically if necessary.
        _load_all: Asynchronously loads all modules from the directories.
        _load_mod: Asynchronously loads a specific module from the directories.
        __iter__: Allows iteration over all nested namespaces and modules.
    """

    def __init__(self, locations: list[str] = (), *args, **kwargs):
        """
        Initializes the DynamicNamespace with specified locations.

        Args:
            locations (list[str]): A list of directory paths where modules are located.
        """
        super().__init__(*args, **kwargs)
        self._dir = pns.dir.walk(locations)
        self._mod = {}

    def __getattr__(self, name: str):
        """
        Provides dynamic attribute access, attempting to load the module if it's not already loaded.

        Args:
            name (str): The name of the attribute or module to access.

        Returns:
            object: The attribute or module if found.

        Raises:
            AttributeError: If the module cannot be dynamically loaded or does not exist.
        """
        try:
            return super().__getattr__(name)
        except AttributeError:
            item = pns.data.get_alias(name, self._mod)

            # If attribute not found, attempt to load the module dynamically
            if not item:
                pns.loop.run(self._load_mod(name))
                item = pns.data.get_alias(name, self._mod)

            if item:
                return item

            raise

    async def _load_all(self, *, merge: bool = True, hard_fail: bool = False):
        """
        Asynchronously loads all modules from the specified directories.

        Args:
            merge (bool): If True, merge duplicate modules, otherwise keep them separate.
        """
        for d in self._dir:
            for _, name, _ in pkgutil.iter_modules([d]):
                # When loading ALL modules, be forgiving
                try:
                    await self._load_mod(name, [d], merge=merge)
                except Exception as e:
                    if hard_fail:
                        raise e

    async def _load_mod(
        self,
        name: str,
        dirs: list[str] = None,
        *,
        merge: bool = False,
        ext: str = ".py",
    ):
        """
        Asynchronously loads a module by name from specified directories.

        Args:
            name (str): The name of the module to load.
            dirs (list[str], optional): Specific directories to search for the module. Defaults to all directories.
            merge (bool): Determines if modules with the same name should be merged.

        Raises:
            AttributeError: If the module cannot be found in the specified paths.
        """
        if not dirs:
            dirs = self._dir

        for path in dirs:
            mod = pns.mod.load_from_path(name, path, ext=ext)
            if not mod:
                raise AttributeError(f"Module '{name}' not found in {path}")

            try:
                loaded_mod = await pns.mod.prep(self._, self, name, mod)
            except NotImplementedError:
                continue

            # Account for a name change with a virtualname
            name = loaded_mod.__name__
            if name not in self._mod:
                self._mod[name] = loaded_mod
            elif merge:
                # Merge the two modules
                old_mod = self._mod.pop(name)
                loaded_mod._var.update(old_mod._var)
                loaded_mod._func.update(old_mod._func)
                loaded_mod._class.update(old_mod._class)
                self._mod[name] = loaded_mod
            else:
                # Add the second module
                loaded_mod._alias.add(name)
                self._mod[str(path)] = loaded_mod

            if hasattr(mod, SUB_ALIAS):
                self._alias.update(getattr(mod, SUB_ALIAS))

            # Execute the __init__ function if present
            if hasattr(mod, INIT):
                func = getattr(mod, INIT)
                if asyncio.iscoroutinefunction(func):
                    init = pns.contract.Contracted(
                        name=INIT, func=func, parent=loaded_mod, root=self._
                    )
                    await init()

    def __iter__(self):
        """
        Allows iteration over all nested namespaces and loaded modules.

        Yields:
            object: Active loaded modules.
        """
        for name, item in self._mod.items():
            if getattr(item, "_active", True):
                yield name
        for name, item in self._nest.items():
            if getattr(item, "_active", True):
                yield name
