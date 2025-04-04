import pytest


async def test_sub_alias(hub):
    await hub.pop.sub.add(locations=["test.pns.alias"])
    assert await hub.alias.init.ping() is True
    assert await hub.red.init.ping() is True
    assert await hub.blue.init.ping() is True
    assert await hub.green.init.ping() is True


async def test_basic(hub):
    await hub.pop.sub.add(locations=["test.pns.mods"])
    await hub.mods.test.ping()
    assert await hub.mods.test.ping() == {}
    assert await hub.mods.test.demo() is False
    assert await hub.mods.test.ping() == await hub.mods.foo.bar()


async def test_subdirs(hub):
    await hub.pop.sub.add(locations=["test.pns.sdirs"])
    await hub.pop.sub.load_subdirs(hub.sdirs)
    assert await hub.sdirs.test.ping()
    assert await hub.sdirs.l11.test.ping()
    assert await hub.sdirs.l12.test.ping()
    assert await hub.sdirs.l13.test.ping()


async def test_subdirs_recurse(hub):
    await hub.pop.sub.add(locations=["test.pns.sdirs"])
    await hub.pop.sub.load_subdirs(hub.sdirs, recurse=True)
    assert await hub.sdirs.test.ping()
    assert await hub.sdirs.l11.test.ping()
    assert await hub.sdirs.l11.l2.test.ping()
    assert await hub.sdirs.l12.l2.test.ping()
    assert await hub.sdirs.l13.l2.test.ping()


async def test_getattr(hub):
    await hub.pop.sub.add(locations=["test.pns.mods"])
    await hub.mods.test.ping()
    assert await hub["mods.test.ping"]() == {}
    assert await hub.mods.test["demo"]() is False
    assert await hub.mods.test.ping() == await hub["mods.foo.bar"]()


async def test_nest(hub):
    """
    Test the ability to nest the subs in a deeper namespace
    """
    await hub.pop.sub.add(locations=["test.pns.mods"])
    await hub.pop.sub.add(locations=["test.pns.mods.nest"], sub=hub.mods)
    assert await hub.mods.nest.basic.ret_true()


async def test_func_attrs(hub):
    await hub.pop.sub.add(locations=["test.pns.mods"])
    assert "bar" in hub.mods.test.attr.func.__dict__
    assert hub.mods.test.attr.func.bar is True
    assert hub.mods.test.attr.func.func is not hub.mods.test.attr.func


async def test_module_level_direct_call(hub):
    await hub.pop.sub.add(locations=["test.pns.mods"])
    with pytest.raises(Exception):
        await hub.mods.test.module_level_non_aliased_ping_call()
    assert await hub.mods.test.module_level_non_aliased_ping_call_fw_hub() == {}


async def test_contract(hub):
    await hub.pop.sub.add(
        locations=["test.pns.mods"], contract_locations=["test.pns.contract"]
    )
    with hub.lib.pytest.raises(ValueError):
        await hub.mods.test.ping(4)


async def test_inline_contract(hub):
    await hub.pop.sub.add(locations=["test.pns.cmods"])
    assert await hub.cmods.ctest.cping()
    assert hub.CPING


async def test_no_contract(hub):
    await hub.pop.sub.add(locations=["test.pns.mods"])
    with pytest.raises(TypeError):
        await hub.mods.test.ping(4)


async def test_contract_manipulate(hub):
    await hub.pop.sub.add(
        locations=["test.pns.mods"], contract_locations=["test.pns.contract"]
    )
    assert "override" in await hub.mods.all.list()
    assert "post called" in await hub.mods.all.list()
    assert "post" in await hub.mods.all.dict()


async def test_private_function_cross_access(hub):
    hub.opts = "OPTS!"
    await hub.pop.sub.add(locations=["test.pns.mods"])
    # Let's make sure that the private function is not accessible through the sub
    with pytest.raises(AttributeError):
        await hub.mods.priv._private() == "OPTS!"

    # Let's confirm that the private function has access to the cross
    # objects
    assert await hub.mods.priv.public() == "OPTS!"


async def test_private_function_cross_access_with_contracts(hub):
    hub.opts = "OPTS!"
    await hub.pop.sub.add(
        locations=["test.pns.mods"], contract_locations=["test.pns.contracts"]
    )
    # Let's make sure that the private function is not accessible through the sub
    with pytest.raises(AttributeError):
        await hub.mods.priv._private() == "OPTS!"

    # Let's confirm that the private function has access to the cross objects
    assert await hub.mods.priv.public() == "OPTS!"


async def test_cross_in_virtual(hub):
    hub.opts = "OPTS!"
    await hub.pop.sub.add(
        locations=["test.pns.mods"], contract_locations=["test.pns.contract"]
    )
    assert await hub.mods.virt.present() is True


async def test_non_module_functions_are_not_loaded(hub):
    await hub.pop.sub.add(locations=["test.pns.mods"])
    await hub.mods._load_all()
    assert "scan" not in dir(hub.mods.test)

    # Verify that the assigned module name inside of the python sys.modules is unique
    await hub.pop.sub.add(name="dyne1")
    mname = await hub.dyne3.init.mod_name()
    assert not mname.startswith(".")


async def test_dyne(hub):
    await hub.pop.sub.add(name="dyne1")
    assert hub.dyne1.INIT
    assert hub.dyne2.INIT
    assert hub.dyne3.INIT
    assert await hub.dyne1.test.dyne_ping()
    assert await hub.dyne1.nest.nest_dyne_ping()
    assert await hub.dyne2.test.dyne_ping()
    assert await hub.dyne2.nest.nest_dyne_ping()
    assert await hub.dyne3.test.dyne_ping()
    assert await hub.dyne3.nest.nest_dyne_ping()


async def test_sub_virtual(hub):
    await hub.pop.sub.add(name="dyne4")
    await hub.pop.sub.load_subdirs(hub.dyne4)
    assert "nest" in hub.dyne4._nest
    assert "nest" not in hub.dyne4._mod


async def test_dyne_nest(hub):
    await hub.pop.sub.add(name="dn1")
    await hub.pop.sub.load_subdirs(hub.dn1, recurse=True)
    assert await hub.dn1.nest.dn1.ping()
    assert await hub.dn1.nest.dn2.ping()
    assert await hub.dn1.nest.dn3.ping()
    assert await hub.dn1.nest.next.test.ping()
    assert await hub.dn1.nest.next.last.test.ping()


async def test_existing_dyne(hub):
    await hub.pop.sub.add(name="dn1")
    await hub.pop.sub.load_subdirs(hub.dn1, recurse=True)
    assert "nest" in hub.dn1._nest
    assert "nest" not in hub.dn1._mod
    # Add the same dyne again without recursing it and verify that the recursive elements are still there
    await hub.pop.sub.add(name="dn1")
    assert "nest" in hub.dn1._nest
    assert "nest" not in hub.dn1._mod


async def test_dyne_extend(hub):
    await hub.pop.sub.add(name="dn1")
    await hub.pop.sub.load_subdirs(hub.dn1, recurse=True)
    assert await hub.dn1.nest.over.in_dn1()
    assert await hub.dn1.nest.over.in_dn2()
    assert await hub.dn1.nest.over.in_dn3()


async def test_dyne_overwrite(hub):
    await hub.pop.sub.add(name="dn1")
    await hub.pop.sub.load_subdirs(hub.dn1, recurse=True)
    # Assure that the first instance of a function does not get overwritten
    assert await hub.dn1.nest.over.source() == "dn1"


async def test_contract_signatures(hub):
    hub.LOAD_PASS = True
    hub.LOAD_FAIL = False
    # These functions should load no problem
    await hub.pop.sub.add(locations=["test.pns.mods.contract_sig"])


async def test_contract_signature_fail(hub):
    hub.LOAD_PASS = False
    hub.LOAD_FAIL = True
    # These functions should load with sig failures
    await hub.pop.sub.add(locations=["test.pns.mods.contract_sig"])
    assert hub.LOAD_PASS is False
    assert hub.LOAD_FAIL is True


async def test_reload(hub):
    await hub.pop.sub.add(name="dn1")
    assert await hub.pop.sub.reload("dn1")


async def test_reload_fail(hub):
    assert not await hub.pop.sub.reload("nonexistant")
