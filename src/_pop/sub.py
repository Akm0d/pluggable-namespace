"""
Control and add subsystems to the running daemon hub
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
    Add a new subsystem to the hub
    :param hub: The redistributed pns central hub
    :param name: The name that the sub is going to take on the hub.
    :param sub: The sub to use as the root to add to
    :param locations: Load additional directories
    :param contract_locations: Load additional contract paths
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
    await new_sub._load_all()


SPECIAL = ["contracts", "rcontracts"]
OMIT_START = ["_", "."]


async def load_subdirs(hub: pns.hub.Hub, sub: pns.hub.Sub, *, recurse: bool = False):
    """
    Given a sub, load all subdirectories found under the sub into a lower namespace
    :param hub: The redistributed pns central hub
    :param sub: The pns object that contains the loaded module data
    :param recurse: Recursively iterate over nested subs
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
    try:
        locations = hub._nest[name]._dir
        contract_locations = hub._nest[name]._contract_dir
    except KeyError as e:
        await hub.log.debug(f"{e.__class__.__name__}: Error reloading sub {name}: {e}")
        return False

    hub._nest.pop(name)
    await hub.pop.sub.add(
        name=name, locations=locations, contract_locations=contract_locations
    )
    return True
