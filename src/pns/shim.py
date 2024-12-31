"""
A module that facilitates the creation of the hub
"""

import pns.hub
import pns.data


async def pop_hub():
    """
    Initializes a new hub with standard subs.
    Compatible with POP projects
    """
    # Set up the hub
    hub = pns.hub.Hub()

    # Add essential POP modules
    await hub.add_sub("pop", "pns.mods")

    return hub


async def loaded_hub(
    cli: str = "cli",
    *,
    load_all_dynes: bool = True,
    load_all_subdirs: bool = True,
    pop_mods: list[str] = None,
    logs: bool = True,
    load_config: bool = True,
    shell: bool = True,
):
    """
    Initializes a new hub with all discovered subs loaded.
    Compatible with cPOP projects.
    """
    # Set up the hub
    hub = pns.hub.Hub()

    # Add essential POP modules
    await hub.add_sub("pns", pypath=["pns.mods"])

    # Load the config
    await hub.add_sub("config", pypath=["pns.config"])
    if load_config:
        opt = await hub.config.init.load(cli=cli, **hub._dynamic.config)
        hub.OPT = pns.data.NamespaceDict(opt)

    # Setup the logger
    await hub.add_sub("log", "pns.log")
    if load_config and logs:
        await hub.log.init.setup(**hub.OPT.log.copy())

    # Add the ability to shell out from the hub
    if shell:
        hub._subs["sh"] = pns.hub.CMD(hub)

    if load_all_dynes:
        await load_all(hub, load_all_subdirs)

    return hub


async def load_all(hub, load_all_subdirs: bool):
    # Load all dynamic subs onto the hub
    for dyne in hub._dynamic.dyne:
        if dyne in hub._subs:
            continue
        await hub.pns.sub.add(dyne_name=dyne)
        if not load_all_subdirs:
            continue
        await hub.pns.sub.load_subdirs(hub._subs[dyne], recurse=True)


async def salt_loader():
    """
    Create a hub compatible with salt
    """