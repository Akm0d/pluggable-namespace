async def _hub(hub):
    await hub.pns.sub.add(pypath=["tests.pns.integration.contracted.mods"])
    return hub


async def test_two_hubs(hub):
    h = await _hub(hub)

    # we should be able to call a function with two hubs as parameters
    await h.mods.contracted_access.two_hubs(h)
