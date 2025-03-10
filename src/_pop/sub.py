"""
Module for managing and dynamically loading subsystems within the Plugin Oriented Programming (POP) hub.

This module provides functionality to add new subsystems, reload existing ones, and manage dynamic
subdirectory loading. It is designed to enhance modularity and flexibility in applications using the
POP framework by allowing runtime additions and updates to the hub's subsystems. This capability
supports dynamic development environments and simplifies updates in long-running applications.
"""

import pns.hub
import pns.data
import pathlib


async def add(
    hub: pns.hub.Hub,
    name: str = None,
    *,
    sub: pns.hub.Sub = None,
    locations: list[pathlib.Path] = (),
    contract_locations: list[pathlib.Path] = (),
):
    """
    Adds a new subsystem to the hub or extends an existing subsystem with additional directories.

    This function dynamically loads a subsystem into the hub's namespace, optionally including additional
    directories and contract paths for extended functionality.

    Parameters:
        hub (pns.hub.Hub): The central hub instance to which the subsystem is added.
        name (str, optional): The name of the subsystem. If not specified, the name is derived from the first
            directory's stem in the provided locations list.
        sub (pns.hub.Sub, optional): The root subsystem under which the new subsystem is added. Defaults to the main hub.
        locations (list[pathlib.Path]): A list of directory paths where the subsystem's resources are located.
        contract_locations (list[pathlib.Path]): A list of directory paths containing contracts for the subsystem.

    Returns:
        None: This function does not return a value but modifies the hub instance by adding or extending subsystems.
    """
    static = pns.dir.walk(locations)
    if not name:
        name = static[0].stem

    root: pns.hub.Sub = sub if sub is not None else hub

    # The dynamic namespace is already on the hub
    if name in root._nest:
        return

    # Extend the paths with dynamic paths if the name matches
    if name in hub._dynamic.dyne:
        static += hub._dynamic.dyne[name].paths

    new_sub = await root.add_sub(
        name, locations=static, contract_locations=contract_locations
    )
    await new_sub._load_all(hard_fail=True)


SPECIAL = ["contracts", "rcontracts"]
OMIT_START = ["_", "."]


async def load_subdirs(hub: pns.hub.Hub, sub: pns.hub.Sub, *, recurse: bool = False):
    """
    Loads all subdirectories found under the specified sub into a lower namespace on the hub.

    This function recursively or non-recursively loads all accessible subdirectories as
    separate subs under the given subsystem, enhancing the modular structure.

    Parameters:
        hub (pns.hub.Hub): The central hub where the subsystems are managed.
        sub (pns.hub.Sub): The subsystem under which subdirectories will be loaded.
        recurse (bool, optional): If true, recursively load subdirectories as nested subs.

    Returns:
        None: This function does not return a value but modifies the hub instance by loading subdirectories.
    """
    if not sub._active:
        return
    roots = hub.lib.collections.defaultdict(list)
    for dir_ in sub._dir:
        if not dir_.exists():
            continue
        for fn in dir_.iterdir():
            if fn.name[0] in OMIT_START:
                continue
            if fn.name in SPECIAL:
                continue
            full = dir_ / fn
            if not full.is_dir():
                continue
            roots[fn.name].append(str(full))
    for name, sub_dirs in roots.items():
        await hub.pop.sub.add(
            name=name,
            sub=sub,
            locations=sub_dirs,
        )
        if recurse:
            if isinstance(getattr(sub, name), pns.hub.Sub):
                await hub.pop.sub.load_subdirs(getattr(sub, name), recurse=recurse)


async def reload(hub: pns.hub.Hub, name: str) -> bool:
    """
    Reloads a specified subsystem by name, allowing updates to its configuration and contents.

    This function is useful for updating subsystems dynamically during runtime without restarting
    the application.

    Parameters:
        hub (pns.hub.Hub): The central hub where the subsystem is managed.
        name (str): The name of the subsystem to reload.

    Returns:
        bool: True if the subsystem was successfully reloaded, False if there was an error.
    """
    try:
        locations = hub._nest[name]._dir
        contract_locations = hub._nest[name]._contract_dir
    except KeyError as e:
        return False

    hub._nest.pop(name)
    await hub.pop.sub.add(
        name=name, locations=locations, contract_locations=contract_locations
    )
    return True
