import asyncio

import aiomonitor

import pns.hub


async def amain():
    loop = asyncio.get_running_loop()

    async with pns.hub.Hub(cli="cli") as hub:
        watch_subs = hub.OPT.cli.watch
        await hub.log.debug("Initialized the hub")

        hold = asyncio.create_task(hub._holder())
        if watch_subs:
            watch = asyncio.create_task(hub.cli.watch.start())

        if "legacy" in hub.cli:
            await hub.cli.legacy.patch(loop=loop)

        for ref in hub.OPT.cli.init:
            coro = hub[ref]()
            if asyncio.iscoroutine(coro):
                await coro

        try:
            # Start the hub cli
            coro = hub.cli.init.run()
            if hub.OPT.cli.monitor:
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

            # Send a stop signal to the holder
            await hub._tasks.put(pns.hub.SHUTDOWN_SIGNAL)
            await hub.lib.asyncio.sleep(0)

            if watch_subs:
                # Cancel the inotify watcher
                watch.cancel()
                try:
                    await watch
                except asyncio.CancelledError:
                    ...

            # Wait for the holder to shut down
            await hold

            # Clean up async generators
            await loop.shutdown_asyncgens()


def main():
    """
    A synchronous main function is required for the "hub" script to work properly
    """
    asyncio.run(amain())


if __name__ == "__main__":
    """
    This is invoked with "python3 -m hub" is called.
    """
    main()
