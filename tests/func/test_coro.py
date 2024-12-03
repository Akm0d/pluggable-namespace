# pylint: disable=expression-not-assigned
import pytest

# Import pns


@pytest.mark.asyncio
async def test_async_simple_contracts(hub):
    await hub.pns.sub.add(pypath=["tests.coro"], subname="coro")
    ret = await hub.coro.test.simple()
    assert ret is True
    assert hub.PRE
    assert hub.POST
