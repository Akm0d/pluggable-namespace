# pylint: disable=expression-not-assigned
import pytest

# Import pns


@pytest.mark.asyncio
async def test_async_simple_contracts(hub):
    await hub.pop.sub.add(locations=["test.pns.coro"], name="coro")
    ret = await hub.coro.test.simple()
    assert ret is True
    assert hub.PRE
    assert hub.POST
