"""
Core data structure definitions and utility functions for namespace management in Cython.

This module defines essential data structures and functions that facilitate the dynamic manipulation
and interaction with namespaces within a system designed around pluggable namespaces. It is intended
to be compiled with Cython to improve performance for attribute access and namespace operations.

Classes:
    - NamespaceDict: An enhanced dictionary allowing attribute-style access and automatic conversion
        of nested dictionaries to NamespaceDict instances for recursive attribute-style access.
    - Namespace: A flexible and dynamic namespace class supporting hierarchical organization of attributes
        and dynamic loading, with capabilities to traverse and manipulate nested namespaces effectively.

Functions:
    - get_alias: Retrieves a Namespace instance from a collection based on a given name or alias.
    - update: Provides a recursive or non-recursive dictionary update functionality with support for merging lists.

These classes and functions are foundational for creating a structured and dynamic namespace system, enabling
highly modular and maintainable code architecture.

Compiled with Cython, this module optimizes attribute access and manipulation, making it well-suited for
environments where performance is critical.
"""

from collections.abc import Mapping
from types import SimpleNamespace
from collections.abc import Iterable


class NamespaceDict(dict[str, object]):
    """
    A custom dictionary class that allows accessing its items as attributes.

    This class extends the standard Python dictionary to provide a way to access and set dictionary
    keys using attribute notation. If a key maps to another dictionary, that dictionary is automatically
    converted into a `NamespaceDict`, allowing recursive attribute-style access.

    Attributes:
        Inherits all attributes from the built-in `dict` class.

    Examples:
        >>> ns = NamespaceDict({'key1': 'value1', 'nested': {'key2': 'value2'}})
        >>> ns.key1
        'value1'
        >>> ns.nested.key2
        'value2'
    """

    def __setattr__(self, name, value):
        return self.__setitem__(name, value)

    def __getattr__(self, key: str):
        try:
            val = self[key]
            if isinstance(val, dict) and not isinstance(val, NamespaceDict):
                val = NamespaceDict(val)
            return val
        except KeyError:
            return super().__getattribute__(key)


class Namespace(SimpleNamespace):
    """
    A dynamic and structured namespace object that allows hierarchical organization of attributes and modules.

    This class provides a flexible structure for namespaces with advanced attribute and item access capabilities, supporting dynamic loading and traversal through operators.

    Attributes:
        _active (bool): Indicates if the namespace is active or not.
        __name__ (str): The name of the current namespace.
        __ (Namespace): Reference to the parent namespace.
        _root (Namespace): Reference to the root namespace.
        _alias (set): A set of aliases associated with this namespace.
        _nest (dict): A dictionary containing nested namespaces.

    Methods:
        _add_child: Adds a new child namespace.
        __getitem__: Retrieves a namespace by traversing through nested namespaces based on dot notation.
        __iadd__: Adds a child namespace or a tuple describing the namespace and its paths.
        __div__, __gt__, __floordiv__, __lt__: Operators to traverse through namespaces.
        __iter__: Iterates over the nested namespaces.
        __len__: Returns the count of nested namespaces.
        __bool__: Returns True if the namespace is active, otherwise False.

    Usage:
        Create a root namespace and dynamically add or access nested namespaces using operators and methods.
    """

    _active = True

    def __init__(
        self,
        name: str,
        parent: "Namespace" = None,
        root: "Namespace" = None,
        *args,
        **kwargs,
    ):
        """
        Initializes a new instance of Namespace.

        Args:
            name (str): The name of the namespace.
            parent (Namespace, optional): The parent namespace. Defaults to None.
            root (Namespace, optional): The root namespace. Defaults to None.
        """
        super().__init__(*args, **kwargs)
        self.__name__ = name
        self.__ = parent
        self._root = root
        # Aliases for this namespace
        self._alias = set()
        # Namespaces underneath this namespace
        self._nest = {}

    @property
    def _(self):
        """
        Provides access to the root namespace.

        Returns:
            Namespace: The root namespace.
        """
        return self._root

    def __getattr__(self, name: str):
        """
        Dynamically accesses children or module attributes.

        Args:
            name (str): The attribute name to access.

        Returns:
            Any: The attribute value or nested namespace.

        Raises:
            AttributeError: If the attribute or namespace is not found.
        """
        item = get_alias(name, self._nest)
        if item:
            return item

        # Finally, fall back on the default attribute access
        return self.__getattribute__(name)

    def __getitem__(self, name: str):
        """
        Retrieves a namespace by traversing through nested namespaces based on dot notation.

        Args:
            name (str): The namespace path using dot notation.

        Returns:
            Namespace: The retrieved namespace.
        """
        finder = self
        for part in name.split("."):
            finder = getattr(finder, part)
        return finder

    def __iadd__(self, other: str | tuple):
        """
        Adds a child namespace using the += operator.

        Args:
            other (str | tuple): The name of the child namespace or a tuple with additional parameters.

        Returns:
            Namespace: The modified namespace with the added child.
        """
        if isinstance(other, str):
            self._add_child(other)
        elif isinstance(other, Iterable):
            self._add_child(*other)
        return self

    def __div__(self, name: str):
        """
        Traverse the namespace using the '/' operator.

        Args:
            name (str): The name of the child namespace to access.

        Returns:
            Namespace: The accessed namespace.
        """
        return self[name]

    def __gt__(self, name: str):
        """
        Traverse the namespace using the '>' operator.

        Args:
            name (str): The name of the child namespace to access.

        Returns:
            Namespace: The accessed namespace.
        """
        return self[name]

    def __floordiv__(self, name: str):
        """
        Traverse the parent of the namespace using the '//' operator.

        Args:
            name (str): The name of the child namespace to access through the parent.

        Returns:
            Namespace: The parent namespace of the accessed child.
        """
        return self.__[name]

    def __lt__(self, name: str):
        """
        Traverse the parent of the namespace using the '<' operator.

        Args:
            name (str): The name of the child namespace to access through the parent.

        Returns:
            Namespace: The parent namespace of the accessed child.
        """
        return self.__[name]

    def __iter__(self):
        """
        Iterate over the nested namespaces.

        Yields:
            Namespace: Each nested namespace.
        """
        for name, item in self._nest.items():
            if getattr(item, "_active", True):
                yield name

    def __len__(self):
        """
        Returns the number of nested namespaces.

        Returns:
            int: The count of nested namespaces.
        """
        return len(self._nest)

    def __bool__(self):
        """
        Returns True if the namespace is active, otherwise False.

        Returns:
            bool: The active state of the namespace.
        """
        return self._active

    def _add_child(self, name: str, cls=None):
        """
        Adds a new child to the namespace.

        Args:
            name (str): The name of the child namespace.
            cls (type, optional): The class to use for the child namespace. Defaults to Namespace.

        Returns:
            Namespace: The newly added child namespace.
        """
        if cls is None:
            cls = Namespace
        current = self
        parts = name.split(".")
        for part in parts:
            if part not in current._nest:
                current._nest[part] = cls(part, root=self._, parent=self)

            current = current._nest[part]

        return current

    @property
    def __ref__(self) -> str:
        """
        Constructs a reference string that traverses from the root to the current node.

        Returns:
            str: The reference string representing the path from the root to this node.
        """
        parts = []
        finder = self
        # Traverse up until we reach the root
        while finder.__ is not None:
            # Add the root name
            parts.append(finder.__name__)
            finder = finder.__

        # Reverse parts to start from the root
        return ".".join(reversed(parts))

    def __repr__(self):
        """
        Provides a string representation of the namespace.

        Returns:
            str: The string representation of the namespace.
        """
        return f"{self.__class__.__name__.split('.')[-1]}({self.__ref__})"


def get_alias(name: str, collection: dict[str, object]) -> Namespace:
    """
    Search for a Namespace object in a collection that matches a given name or its alias.

    The function iterates over a dictionary of objects, returning the Namespace instance
    corresponding to the given name if it matches directly, or any alias associated with
    the Namespace if it's active. If a matching, active Namespace is not found, returns None.

    Args:
        name (str): The name or alias to search for within the collection.
        collection (dict[str, object]): A dictionary containing string keys and Namespace objects.

    Returns:
        Namespace: The Namespace object if found, otherwise None.
    """
    for check, ns in collection.items():
        if name == check:
            if isinstance(ns, Namespace):
                if not ns._active:
                    continue
            return ns
        elif not isinstance(ns, Namespace):
            continue
        if name in ns._alias and ns._active:
            return ns


def update(dest: dict, upd: dict, *, recursive: bool = True, merge_lists: bool = False):
    """
    Update a dictionary recursively or non-recursively with another dictionary's entries.

    This function extends the behavior of the standard dict.update() method by allowing
    deep updates where nested dictionaries are also updated rather than being replaced.
    It also supports optional merging of list values instead of replacing them.

    Args:
        dest (dict): The destination dictionary to update.
        upd (dict): The dictionary with updates to apply.
        recursive (bool): If True, performs a deep update; if False, performs a shallow update.
        merge_lists (bool): If True, merges list objects instead of replacing them during a recursive update.

    Returns:
        dict: The updated destination dictionary.

    Examples:
        >>> dest = {'key1': {'subkey1': 'val1'}}
        >>> upd = {'key1': {'subkey1': 'new_val', 'subkey2': 'val2'}}
        >>> update(dest, upd)
        {'key1': {'subkey1': 'new_val', 'subkey2': 'val2'}}
    """
    keys = set(list(upd.keys()) + list(dest.keys()))
    NONE = object()

    if recursive:
        for key in keys:
            val = upd.get(key, NONE)
            dest_subkey = dest.get(key, NONE)
            if isinstance(dest_subkey, Mapping) and isinstance(val, Mapping):
                ret = update(dest_subkey, val, merge_lists=merge_lists)
                dest[key] = ret
            elif (
                isinstance(dest_subkey, list) and isinstance(val, list) and merge_lists
            ):
                merged = dest_subkey[:]
                merged.extend(x for x in val if x not in merged)
                dest[key] = merged
            elif val is not NONE:
                dest[key] = val
            elif dest is NONE:
                dest[key] = None
    else:
        for key in keys:
            dest[key] = upd[key]

    return dest
