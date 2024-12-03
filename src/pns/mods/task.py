"""
This plugin is used to track pns enabled background task capabilities
"""

from collections.abc import Callable, Coroutine


async def __init__(hub):
    hub.pns.task.KEEP_ALIVE = True
    hub.pns.task.aio_alive = {}


async def auto(hub, coro: Coroutine, cb_coro=None):
    """
    Start a task that will be automatically awaited

    coro: An unscheduled coroutine object to run
    cb_coro: An unscheduled coroutine to run when the main coroutine completes
    """
    task = hub._auto(coro, cb_coro)
    await hub.lib.asyncio.sleep(0)
    return task


async def wait(hub):
    """
    When running without a long-running loop, (hub.aio.loop.run instead of hub.aio.loop.start)
    you need to call this function to clean up any auto tasks that have been created in the
    background.
    This function can be called from anywhere, it will just wait for all auto tasks to
    complete
    """
    while not hub._tasks.empty():
        complete = await hub._tasks.get()
        await complete["task"]
        if complete["cb"]:
            await hub.pns.task.auto(complete["cb"])


async def keep_alive(hub, precision: int, func: Callable, **kwargs):
    """
    Make sure that the named function stays alive, if the resulting coroutine dies, restart the function.
    The operation is run in a separate auto task

    :param precision: The number in seconds to sleep between checks
    :param func: The async function reference to restart if it dies
    :param **kwargs: The keyword arguments to send to the function to start and keep alive
    """

    async def _keep_alive():
        f_id = hub.lib.uuid.uuid4().hex
        if f_id not in hub.pns.task.aio_alive:
            hub.pns.task.aio_alive[f_id] = {"task": None}
        while hub.pns.task.KEEP_ALIVE:
            start = False
            if hub.pns.task.aio_alive[f_id]["task"] is None:
                start = True
            elif hub.pns.task.aio_alive[f_id]["task"].done():
                await hub.pns.task.aio_alive[f_id]["task"]
                start = True
            if start:
                hub.pns.task.aio_alive[f_id]["task"] = await hub.pns.task.auto(func(**kwargs))
            await hub.lib.asyncio.sleep(precision)

    await hub.pns.task.auto(_keep_alive())


async def cancel(hub):
    """
    Cancel all running tasks
    """
    tasks = []
    hub.pns.task.KEEP_ALIVE = False
    for t in hub.lib.asyncio.all_tasks():
        if t == hub.lib.asyncio.current_task():
            continue
        t.cancel()
        tasks.append(t)
    try:
        await hub.lib.asyncio.gather(*tasks)
    except hub.lib.asyncio.CancelledError:
        ...


async def gather(hub):
    """
    Gather all tasks that have not yet been awaited
    """
    hub.pns.task.KEEP_ALIVE = False
    pending = [t for t in hub.lib.asyncio.all_tasks() if t != hub.lib.asyncio.current_task()]
    if pending:
        await hub.log.debug(f"Gathering {len(pending)} tasks")
        await hub.lib.asyncio.gather(*pending, return_exceptions=True)


async def sigint(hub, signal: int):
    """
    Passthrough sigint that can be overridden with a call contract
    """
    await hub.log.debug("Caught sigint, cleaning up")
    raise KeyboardInterrupt


async def sigterm(hub, signal: int):
    """
    Passthrough sigterm that can be overridden with a call contract
    """
    await hub.log.debug("Caught sigterm, cleaning up")
    hub.lib.sys.exit(0)
