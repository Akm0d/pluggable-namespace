async def test_mod_clash(hub):
    await hub.pop.sub.add(dyne_name="dyn")
    # The "dyn" sub contains two files that both define a "clash" function
    assert await hub.dyn.mod.clash() == 1


async def test_mod_merge(hub):
    await hub.pop.sub.add(dyne_name="dyn")
    # The unique functions from each mod should make it onto the same mod
    assert await hub.dyn.mod.merge1()
    assert await hub.dyn.mod.merge2()

    # These functions come from virtuals
    assert await hub.dyn.mod.merge3()
    assert await hub.dyn.mod.merge4()
