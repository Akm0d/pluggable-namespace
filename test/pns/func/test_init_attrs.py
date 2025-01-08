async def test_init_attrs_on_parent(hub):
    """
    A sub containing an "init.py" should be able to call the functions in the init.py directly
    """
    await hub.pop.sub.add(pypath=["test.pnsmods.subinit"])
    assert hub.subinit.init.inited is hub.subinit.inited
