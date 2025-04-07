"""
A module that facilitates the creation of pre-loaded hubs with various features and configurations.

This module is designed to streamline the initialization of hubs in the Plugin Oriented
Programming (POP) framework, specifically catering to scenarios where a hub needs to be equipped
with a set of predefined functionalities such as configuration management, dynamic module loading,
shell command execution capabilities, and more.

The provided functions support asynchronous creation of fully-configured hubs that are ready
to be used in POP-based applications, handling everything from setting up basic system
interactions to loading complex subsystems with custom configurations.
"""

import pns.hub
import pns.shell


async def pop_hub():
    """
    Initializes a new hub with standard subs that are essential for POP projects.

    This function creates a new hub instance, setting up basic namespaces and loading essential
    modules which are fundamental for operating within the POP framework.

    Returns:
        pns.hub.Hub: A new hub instance with essential namespaces and modules initialized.
    """
    # Set up the hub
    hub = await pns.hub.Hub.new()

    # Add essential POP modules
    await hub.add_sub("pop", locations=["_pop"])

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
    Initializes a new hub with a comprehensive setup including dynamic modules, configuration, and logging.

    This function builds upon `pop_hub` by adding more layers of functionality to the hub,
    such as configuration loading, logging, and the ability to execute shell commands directly
    from the hub.

    Parameters:
        cli (str): The command-line interface module name.
        load_all_dynes (bool): Flag to load all dynamic modules.
        load_all_subdirs (bool): Flag to load all subdirectories for each dyne.
        pop_mods (list[str]): List of POP module locations to be loaded initially.
        logs (bool): Enables logging setup.
        load_config (bool): Enables configuration loading from specified paths.
        shell (bool): Enables the ability to execute shell commands from the hub.

    Returns:
        pns.hub.Hub: A fully loaded hub instance ready for use in cPOP projects.
    """
    # Set up the hub
    hub = await pns.hub.Hub.new()

    # Add essential POP modules
    await hub.add_sub("pop", locations=pop_mods)
    await hub.pop._load_all()

    # Load the config
    await hub.add_sub(name="config", locations=hub._dynamic.dyne.config.paths)
    await hub.config._load_all()

    if load_config:
        opt = await hub.config.init.load(cli=cli, **hub._dynamic.config)
        hub.OPT = opt
    else:
        hub.OPT = {}

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
    """
    Load all dynamic subs onto the hub.

    This function is designed to extend the functionality of the hub by loading all
    dynamic modules specified in the hub's configuration. It handles the loading of
    both top-level dyne modules and, optionally, their subdirectories.

    Parameters:
        hub (pns.hub.Hub): The hub instance to which the dynamic modules are to be loaded.
        load_all_subdirs (bool): If True, loads all subdirectories for each dyne module.

    Note:
        This function does not return a value; it modifies the hub instance in place.
    """
    for dyne in hub._dynamic.dyne:
        if dyne in hub._nest:
            continue
        await hub.add_sub(name=dyne, locations=hub._dynamic.dyne[dyne].paths)
        await hub[dyne]._load_all()
        if not load_all_subdirs:
            continue
        await hub.pop.sub.load_subdirs(hub._nest[dyne], recurse=True)
