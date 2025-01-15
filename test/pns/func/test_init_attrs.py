async def test_init_attrs_on_parent(hub):
    """
    A sub containing an "init.py" should be able to call the functions in the init.py directly
    """
    await hub.pop.sub.add(locations=["test.pns.mods.subinit"])
    assert hub.subinit.init.inited is hub.subinit.inited
