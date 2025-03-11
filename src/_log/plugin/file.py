async def process(hub, msg: str):
    """
    Asynchronously append a log message to a file.
    """
    path = hub.lib.aiopath.Path(hub.OPT.log.log_file).expanduser()
    if not await path.parent.exists():
        await path.parent.mkdir(parents=True, exist_ok=True)
    await path.touch(exist_ok=True)

    async with path.open("a") as f:
        await f.write(msg)
