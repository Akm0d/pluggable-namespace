"""
A module that facilitates the creation of the hub
"""

import pns.hub
import pns.data
import pns.shell


async def pop_hub():
    """
    Initializes a new hub with standard subs.
    Compatible with POP projects
    """
    # Set up the hub
    hub = await pns.hub.Hub.new()

    # Add essential POP modules
    await hub.add_sub("pop", pypath=["_pop"])

    return hub


async def loaded_hub(
    cli: str = "cli",
    *,
    load_all_dynes: bool = True,
    load_all_subdirs: bool = True,
    pop_mods: list[str] = ("_pop",),
    logs: bool = True,
    load_config: bool = True,
    shell: bool = True,
):
    """
    Initializes a new hub with all discovered subs loaded.
    Compatible with cPOP projects.
    """
    # Set up the hub
    hub = await pns.hub.Hub.new()

    # Add essential POP modules
    await hub.add_sub("pop", pypath=pop_mods)
    await hub.pop._load_all()

    # Load the config
    await hub.add_sub(name="config", static=hub._dynamic.dyne.config.paths)
    if load_config:
        await hub.config._load_all()
        opt = await hub.config.init.load(cli=cli, **hub._dynamic.config)
        hub.OPT = pns.data.NamespaceDict(opt)
    else:
        hub.OPT = pns.data.NamespaceDict()

    # Setup the logger
    if load_config and logs:
        await hub.log.init.setup(**hub.OPT.log.copy())

    # Add the ability to shell out from the hub
    if shell:
        hub._nest["sh"] = pns.shell.CMD(hub, parent=hub)

    if load_all_dynes:
        await load_all(hub, load_all_subdirs)

    return hub


async def load_all(hub, load_all_subdirs: bool):
    # Load all dynamic subs onto the hub
    for dyne in hub._dynamic.dyne:
        if dyne in hub._nest:
            continue
        await hub.add_sub(name=dyne, static=hub._dynamic.dyne[dyne].paths)
        await hub[dyne]._load_all()
        if not load_all_subdirs:
            continue
        continue
        await hub.pns.sub.load_subdirs(hub._nest[dyne], recurse=True)


async def salt_loader():
    """
    Create a hub compatible with salt
    """
    raise NotImplemented("TODO")
