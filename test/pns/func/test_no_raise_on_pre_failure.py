import pytest


@pytest.fixture(scope="function")
async def hub(hub):
    await hub.pop.sub.add(name="cn")
    return hub


async def test_pre_fail_sync(hub):
    with pytest.raises(
        Exception, match="Pre contract 'pre_func1' failed for function 'func1'"
    ):
        await hub.cn.test.func1()


async def test_pre_fail_sync_with_message(hub):
    with pytest.raises(Exception, match="custom message"):
        await hub.cn.test.func2()


async def test_pre_fail_async(hub):
    with pytest.raises(
        Exception, match="Pre contract 'pre_afunc1' failed for function 'afunc1'"
    ):
        await hub.cn.test.afunc1()


async def test_pre_fail_async_with_message(hub):
    with pytest.raises(Exception, match="custom message"):
        await hub.cn.test.afunc2()


async def test_pre_fail_agen(hub):
    with pytest.raises(
        Exception, match="Pre contract 'pre_agen1' failed for function 'agen1'"
    ):
        async for _ in hub.cn.test.agen1():
            ...


async def test_pre_fail_agen_with_message(hub):
    with pytest.raises(Exception, match="custom message"):
        async for _ in hub.cn.test.agen2():
            ...
