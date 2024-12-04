async def start(hub):
    """
    Start a continuous process that watches for changes to dynamic dirs and reloads them on changes
    """
    if "aionotify" not in hub.lib._imports:
        return

    watcher = hub.lib.aionotify.Watcher()

    for dyne_name, data in hub._dynamic.dyne.items():
        for path in data["paths"]:
            await hub.log.debug(f"Adding watch on {path}")
            watcher.watch(
                alias=(dyne_name, str(path)),
                path=str(path),
                flags=hub.lib.aionotify.Flags.MODIFY | hub.lib.aionotify.Flags.CREATE | hub.lib.aionotify.Flags.DELETE,
            )

    await watcher.setup(loop=hub._loop)
    await hub.lib.asyncio.sleep(0)

    while True:
        try:
            event = await watcher.get_event()
            dyne_name, path = event.alias
            await hub.log.debug(f"Change detected in hub.{dyne_name}")
            mod_path = hub.lib.pathlib.Path(path) / event.name
            mod_name = mod_path.stem
            if mod_name.startswith("__") and mod_name.endswith("__"):
                continue

            sub = hub[dyne_name]
            # No matter what, the cache needs to be emptied
            await hub.log.trace(f"Clearing attribute cache for sub '{dyne_name}'")
            sub._clear()
            ops = hub.lib.aionotify.Flags.parse(event.flags)

            # This is a change to an existing mod
            if str(mod_path) in sub._vmap:
                mod_name = sub._vmap[str(mod_path)]
                bname = str(mod_path.with_suffix(""))

                # Remove the current mod
                old_mod = sub._loaded.pop(mod_name, None)
                if old_mod:
                    await hub.log.debug(f"Deleting loaded mod: {dyne_name}:{mod_name}")
                    hub.lib.sys.modules.pop(old_mod.__name__, None)
                    del old_mod

                # If this was a delete operation we're done
                if hub.lib.aionotify.Flags.DELETE in ops:
                    continue

                # Reload the mod
                await hub.log.debug(f"Reloading mod: {dyne_name}:{mod_name}")
                await sub._load_item("python", bname)
                continue

            # We are removing a sub
            if hub.lib.aionotify.Flags.ISDIR in ops:
                if hub.lib.aionotify.Flags.DELETE in ops:
                    await hub.log.debug(f"Removing sub {dyne_name}.{event.name}")
                    sub._subs.pop(event.name, None)
                    continue
                elif hub.lib.aionotify.Flags.CREATE in ops:
                    watcher.watch(
                        alias=(f"{dyne_name}.{mod_name}", str(mod_path)),
                        path=str(mod_path),
                        flags=hub.lib.aionotify.Flags.MODIFY
                        | hub.lib.aionotify.Flags.CREATE
                        | hub.lib.aionotify.Flags.DELETE,
                    )

            # This is a no-op, we already handled deletes, so the file should exist now
            if not mod_path.exists():
                await hub.log.trace(f"No-op on {dyne_name}:{event.name}")
                continue

            # Reload the whole sub
            await hub.log.debug(f"Reloading sub {dyne_name}")
            await sub._prepare()
            sub._loaded_all = False
            await sub._load_all()
            await hub.pop.sub.load_subdirs(sub, recurse=hub._recurse_subdirs)
        except Exception as e:
            await hub.log.error(f"Error reloading objects on sub '{dyne_name}': {e}")
