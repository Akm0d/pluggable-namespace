"""
Utilities for resolving and traversing references within a hierarchical namespace system.

This module provides functions to resolve references to objects within a complex namespace represented by a hub.
These utilities are crucial for navigating through nested structures, allowing easy access to any object by its
"path" in the namespace hierarchy. Functions in this module support resolving references from string identifiers,
facilitating dynamic access to components across the system.

Functions:
    - last: Returns the last object in a reference chain, facilitating direct access to the desired endpoint.
    - path: Provides a list of all objects from the hub up to a specified reference, enabling traceability of the access path.
    - find: Parses a dot-separated reference string and retrieves the corresponding object from the hub, handling nested structures.

These functions are typically used in systems where components are dynamically managed and accessed through a centralized hub,
enabling flexible and maintainable access patterns across a pluggably-structured application.
"""


def last(hub, ref) -> object:
    """
    Retrieve the last object from a reference path within the hub.

    Parameters:
        hub (pns.hub.Hub): The central hub or root namespace.
        ref (str): A dot-separated string representing the path to the object.

    Returns:
        object: The last object referenced by `ref`.

    Example:
        >>> last(hub, "sub1.sub2.mod")
        >>> # Returns the 'mod' object from within the 'sub1.sub2' namespace
    """
    refs = path(hub, ref)
    return refs.pop()


def path(hub, ref) -> list[object]:
    """
    Generate a list of objects that form the path to a specific reference within the hub.

    Parameters:
        hub (pns.hub.Hub): The central hub or root namespace.
        ref (str): A dot-separated string that specifies the path through the hub.

    Returns:
        list[object]: A list containing each object along the path specified by `ref`.

    Example:
        >>> path(hub, "system.network.adapter")
        >>> # Returns a list: [hub, system, network, adapter]
    """
    ret = [hub]

    if isinstance(ref, str):
        ref = ref.split(".")

    root = hub
    for chunk in ref:
        root = getattr(root, chunk)
        ret.append(root)
    return ret


def find(hub, ref: str) -> object:
    """
    Take a string that represents an attribute nested underneath the hub.
    Parse the string and retrieve the object form the hub.

    Args:
        hub (pns.hub.Hub): The global namespace.
        ref (str): A string separated by "." with each part being a level deeper into objects on the hub.

    Returns:
        any: The object found on the hub
    """
    # Get the named reference from the hub
    finder = hub
    parts = ref.split(".")
    for p in parts:
        if not p:
            continue
        try:
            # Grab the next attribute in the reference
            finder = getattr(finder, p)
            continue
        except AttributeError:
            try:
                # It might be a dict-like object, try getitem
                finder = finder.__getitem__(p)
                continue
            except TypeError:
                # It might be an iterable, if the next part of the ref is a digit try to access the index
                if p.isdigit() and isinstance(finder, hub.lib.typing.Iterable):
                    finder = tuple(finder).__getitem__(int(p))
                    continue
            raise
    return finder
