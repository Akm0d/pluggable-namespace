import asyncio
import pns.shim
import sys

try:
    import aiomonitor

    HAS_AIOMONITOR = True
except ImportError:
    HAS_AIOMONITOR = False


async def amain():
    loop = asyncio.get_running_loop()

    hub = await pns.shim.loaded_hub(cli="cli")
    await hub.log.debug("Initialized the hub")

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
