async def __virtual__(hub):
    try:
        import pop.hub  # noqa

        return True
    except ImportError as e:
        return False, str(e)


LOG_NAMES = ("trace", "debug", "info", "warning", "error")


async def patch(hub, loop):
    """
    Add constructs from OG pop hub to a pns hub
    """
    await hub.log.debug("Adding a pop hub to the pns hub under hub.legacy")
    hub.legacy = hub.lib.pns.hub.Hub()
    hub.legacy.pop.loop.CURRENT_LOOP = loop

    await hub.log.debug("Loading all dynes under legacy hub")
    for dyne in hub.legacy._dynamic:
        hub.legacy.pop.sub.add(dyne_name=dyne)
        hub.legacy.pop.sub.load_subdirs(hub.legacy[dyne], recurse=True)

    # Patch the legacy hub's logger with trace logging for pns-config's noisy logger
    for name in LOG_NAMES:
        setattr(hub.legacy.log, name, lambda *a, **kw: hub._auto(hub.log.trace(*a, **kw)))

    # Populate the legacy hub's OPT
    dyne_names = list(hub.legacy._dynamic.keys())

    config_dynes = hub.legacy.config.dirs.find_configs(dyne_names)
    hub.legacy.pop.config.load(list(config_dynes.keys()), "pop_config", dyne_names, parse_cli=False, logs=False)

    # Patch the legacy hub's logger with pns's logger
    for name in LOG_NAMES:
        setattr(
            hub.legacy.log,
            name,
            lambda *a, __name=name, **kw: hub._auto(hub.log[__name](*a, **kw)),
        )

    # Add the legacy hub's subs to the search path of the main hub
    hub += hub.legacy._subs

    # Extend subs from both pop versions
    await hub.log.debug("Extending pns hub attrs with pop hub attrs")
    for sub in hub._subs:
        if sub in hub.legacy._subs:
            hub._subs[sub] += hub.legacy._subs[sub]._subs
            hub._subs[sub] += hub.legacy._subs[sub]._loaded

    await hub.lib.asyncio.sleep(0)
