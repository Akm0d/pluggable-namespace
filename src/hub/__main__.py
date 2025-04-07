import asyncio
import pns.shim
import sys

try:
    import aiomonitor

    HAS_AIOMONITOR = True
except ImportError:
    HAS_AIOMONITOR = False

INITIAL_CLI = "cli"


async def amain():
    loop = asyncio.get_running_loop()

    hub = await pns.shim.loaded_hub(cli=INITIAL_CLI)
    await hub.log.debug("Initialized the hub")

    # Add local python scripts to the hub
    new_dirs = set()
    for f in hub.OPT.cli.file:
        path = hub.lib.pathlib.Path(f).absolute()
        new_dirs.add(path.parent)
        await hub._load_mod(path.stem, dirs=[path.parent], merge=True, ext=path.suffix)

    if new_dirs:
        # Reload the cli with the new directories
        hub._dynamic = hub.lib.pns.dir.dynamic(new_dirs)
        opt = await hub.config.init.load(cli=INITIAL_CLI, **hub._dynamic.config)
        hub.OPT = opt

    for ref in hub.OPT.cli.init:
        coro = hub[ref]()
        if asyncio.iscoroutine(coro):
            await coro

    try:
        # Start the hub cli
        coro = hub.cli.init.run()
        if HAS_AIOMONITOR and hub.OPT.cli.monitor:
            with aiomonitor.start_monitor(loop=loop, locals={"hub": hub}):
                await coro
        else:
            await coro
    except KeyboardInterrupt:
        await hub.log.error("Caught keyboard interrupt.  Cancelling...")
    except SystemExit:
        ...
    finally:
        await hub.log.debug("Cleaning up")
        # Let logging wrap up
        await hub.log.init.close()

        # Clean up async generators
        await loop.shutdown_asyncgens()


def main():
    """
    A synchronous main function is required for the "hub" script to work properly
    """

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(amain())


if __name__ == "__main__":
    """
    This is invoked with "python3 -m hub" is called.
    """
    main()
