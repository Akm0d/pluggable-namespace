async def test_get(hub):
    assert await hub.pns.dyne.get() == hub._dynamic.dyne
