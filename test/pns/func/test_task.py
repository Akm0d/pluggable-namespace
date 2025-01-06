import pytest


async def test_auto(hub):
    await hub.pns.task.auto(hub.lib.asyncio.sleep(0))


async def test_sync_auto_traceback(hub):
    with pytest.raises(hub.pns.test.TestError):
        await hub._auto(hub.pns.test["raise"]())


async def test_auto_traceback(hub):
    with pytest.raises(hub.pns.test.TestError):
        task = await hub.pns.task.auto(hub.pns.test["raise"]())
        await task
