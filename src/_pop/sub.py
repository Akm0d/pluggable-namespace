"""
Control and add subsystems to the running daemon hub
"""

import pns.hub
import pns.data


async def add(
    hub: pns.hub.Hub,
    dyne_name: str = None,
    *,
    pypath: list[str] = (),
    subname: str = None,
    sub:pns.hub.Sub=None,
    static: list[str] = (),
    contracts_pypath: list[str] = (),
    contracts_static: list[str] = (),
    recursive_contracts_static: list[str] = (),
    python_import: str = None,
):
    """
    Add a new subsystem to the hub
    :param hub: The redistributed pns central hub
    :param dyne_name: The dynamic name to use to look up paths to find plugins -- linked to conf.yaml
    :param subname: The name that the sub is going to take on the hub. Defaults to the dyne name
    :param sub: The sub to use as the root to add to
    :param contracts_pypath: Load additional contract paths
    :param contracts_static: Load additional contract paths from a specific directory
    :param recursive_contracts_static: Load additional recursive contract paths from a specific directory
    :param python_import: Load a module from python onto the sub
    """
    if python_import:
        subname = subname if subname else python_import.split(".")[0]
    if pypath:
        subname = subname if subname else pypath[0].split(".")[-1]
    elif static:
        subname = subname if subname else hub.lib.os.path.basename(static)
    if dyne_name:
        subname = subname if subname else dyne_name
    root: pns.hub.Sub = sub if sub is not None else hub
    # The dynamic namespace is already on the hub
    if dyne_name in root._nest:
        return

    if python_import:
        new_sub = hub.lib.importlib.import_module(python_import)
        root._nest[subname] = new_sub
    elif dyne_name:
        new_sub =await hub.add_sub(name=subname, static=hub._dynamic.dyne[subname].paths)
        await new_sub._load_all()
    else:
        new_sub = await root.add_sub(subname, pypath=pypath, static=static)
        await new_sub._load_all()

    root._nest[subname]._contracts = (contracts_pypath or []) + (contracts_static or [])
    root._nest[subname]._rcontracts = recursive_contracts_static or []

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
            static=sub_dirs,
        )
        if recurse:
            if isinstance(getattr(sub, name), pns.hub.Sub):
                await hub.pop.sub.load_subdirs(getattr(sub, name), recurse=recurse)
