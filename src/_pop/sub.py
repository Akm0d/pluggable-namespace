"""
Control and add subsystems to the running daemon hub
"""

import pns.hub
import pns.data


async def add(
    hub: pns.hub.Hub,
    dyne_name: str = None,
    *,
    subname: str = None,
    sub: pns.hub.Sub = None,
    locations: list[str] = (),
    contract_locations: list[str] = (),
):
    """
    Add a new subsystem to the hub
    :param hub: The redistributed pns central hub
    :param dyne_name: The dynamic name to use to look up paths to find plugins -- linked to conf.yaml
    :param subname: The name that the sub is going to take on the hub. Defaults to the dyne name
    :param sub: The sub to use as the root to add to
    :param locations: Load additional directories
    :param contract_locations: Load additional contract paths
    """
    static = pns.dir.walk(locations)
    if not subname:
        if dyne_name:
            subname = dyne_name
        elif static:
            subname = static[0].stem

    root: pns.hub.Sub = sub if sub is not None else hub

    # The dynamic namespace is already on the hub
    if dyne_name in root._nest:
        return

    if dyne_name:
        static += hub._dynamic.dyne[dyne_name].paths

    new_sub = await root.add_sub(subname, locations=static)
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
            subname=name,
            sub=sub,
            locations=sub_dirs,
        )
        if recurse:
            if isinstance(getattr(sub, name), pns.hub.Sub):
                await hub.pop.sub.load_subdirs(getattr(sub, name), recurse=recurse)
