from contextlib import asynccontextmanager


@asynccontextmanager
async def temp(hub, *args, delete: bool = True, **kwargs):
    """
    Async temporary file context manager.
    """
    async with hub.lib.aiofiles.tempfile.NamedTemporaryFile(
        delete=False, *args, **kwargs
    ) as fh:
        yield fh

    # Windows requires the file to be closed before it can be deleted
    if delete:
        await hub.lib.aiofiles.os.unlink(fh.name)
