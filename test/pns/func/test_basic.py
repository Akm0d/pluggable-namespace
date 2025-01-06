# pylint: disable=expression-not-assigned
import pytest

# import pns.exc


async def test_sub_alias(hub):
    await hub.pns.sub.add(pypath=["tests.pns.alias"])
    assert await hub.alias.init.ping() is True
    assert await hub.red.init.ping() is True
    assert await hub.blue.init.ping() is True
    assert await hub.green.init.ping() is True


async def test_basic(hub):
    await hub.pns.sub.add(pypath=["tests.pns.mods"])
    await hub.mods.test.ping()
    assert await hub.mods.test.ping() == {}
    assert await hub.mods.test.demo() is False
    assert await hub.mods.test.ping() == await hub.mods.foo.bar()


async def test_subdirs(hub):
    await hub.pns.sub.add(pypath=["tests.pns.sdirs"])
    await hub.pns.sub.load_subdirs(hub.sdirs)
    assert await hub.sdirs.test.ping()
    assert await hub.sdirs.l11.test.ping()
    assert await hub.sdirs.l12.test.ping()
    assert await hub.sdirs.l13.test.ping()


async def test_subdirs_recurse(hub):
    await hub.pns.sub.add(pypath=["tests.pns.sdirs"])
    await hub.pns.sub.load_subdirs(hub.sdirs, recurse=True)
    assert await hub.sdirs.test.ping()
    assert await hub.sdirs.l11.test.ping()
    assert await hub.sdirs.l11.l2.test.ping()
    assert await hub.sdirs.l12.l2.test.ping()
    assert await hub.sdirs.l13.l2.test.ping()


async def test_getattr(hub):
    await hub.pns.sub.add(pypath=["tests.pns.mods"])
    await hub.mods.test.ping()
    assert await hub["mods.test.ping"]() == {}
    assert await hub.mods.test["demo"]() is False
    assert await hub.mods.test.ping() == await hub["mods.foo.bar"]()


async def test_nest(hub):
    """
    Test the ability to nest the subs in a deeper namespace
    """
    await hub.pns.sub.add(pypath=["tests.pns.mods"])
    await hub.pns.sub.add(pypath=["tests.pns.mods.nest"], sub=hub.mods)
    assert await hub.mods.nest.basic.ret_true()


async def test_func_attrs(hub):
    await hub.pns.sub.add(pypath=["tests.pns.mods"])
    assert "bar" in hub.mods.test.attr.__dict__
    assert hub.mods.test.attr.func.bar is True
    assert hub.mods.test.attr.func.func is not hub.mods.test.attr.func


async def test_module_level_direct_call(hub):
    await hub.pns.sub.add(pypath=["tests.pns.mods"])
    with pytest.raises(Exception):
        await hub.mods.test.module_level_non_aliased_ping_call()
    assert await hub.mods.test.module_level_non_aliased_ping_call_fw_hub() == {}


async def test_contract(hub):
    await hub.pns.sub.add(
        pypath=["tests.pns.mods"], contracts_pypath=["tests.pns.contracts"]
    )
    with pytest.raises(Exception):
        await hub.mods.test.ping(4)


async def test_inline_contract(hub):
    await hub.pns.sub.add(pypath=["tests.pns.cmods"])
    assert await hub.cmods.ctest.cping()
    assert hub.CPING


async def test_no_contract(hub):
    await hub.pns.sub.add(pypath=["tests.pns.mods"])
    with pytest.raises(TypeError):
        await hub.mods.test.ping(4)


async def test_contract_manipulate(hub):
    await hub.pns.sub.add(
        pypath=["tests.pns.mods"], contracts_pypath=["tests.pns.contracts"]
    )
    assert "override" in await hub.mods.all.list()
    assert "post called" in await hub.mods.all.list()
    assert "post" in await hub.mods.all.dict()


async def test_private_function_cross_access(hub):
    hub.opts = "OPTS!"
    await hub.pns.sub.add(pypath=["tests.pns.mods"])
    # Let's make sure that the private function is not accessible through the sub
    with pytest.raises(AttributeError):
        await hub.mods.priv._private() == "OPTS!"

    # Let's confirm that the private function has access to the cross
    # objects
    assert await hub.mods.priv.public() == "OPTS!"


async def test_private_function_cross_access_with_contracts(hub):
    hub.opts = "OPTS!"
    await hub.pns.sub.add(
        pypath=["tests.pns.mods"], contracts_pypath=["tests.pns.contracts"]
    )
    # Let's make sure that the private function is not accessible through the sub
    with pytest.raises(AttributeError):
        await hub.mods.priv._private() == "OPTS!"

    # Let's confirm that the private function has access to the cross objects
    assert await hub.mods.priv.public() == "OPTS!"


async def test_cross_in_virtual(hub):
    hub.opts = "OPTS!"
    await hub.pns.sub.add(
        pypath=["tests.pns.mods"], contracts_pypath=["tests.pns.contracts"]
    )
    assert await hub.mods.virt.present() is True


async def test_non_module_functions_are_not_loaded(hub):
    await hub.pns.sub.add(pypath=["tests.pns.mods"])
    await hub.mods._load_all()
    assert "scan" not in dir(hub.mods.test)
    await hub.mods.test.call_scan() is True

    """
    Verify that the assigned module name inside of the python sys.modules
    is unique
    """
    await hub.pns.sub.add(dyne_name="dyne1")
    mname = await hub.dyne3.init.mod_name()
    assert not mname.startswith(".")


async def test_dyne(hub):
    await hub.pns.sub.add(dyne_name="dyne1")
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
    await hub.pns.sub.add(dyne_name="dyne4")
    await hub.pns.sub.load_subdirs(hub.dyne4)
    assert "nest" in hub.dyne4._subs
    assert "nest" not in hub.dyne4._loaded


async def test_dyne_nest(hub):
    await hub.pns.sub.add(dyne_name="dn1")
    await hub.pns.sub.load_subdirs(hub.dn1, recurse=True)
    assert await hub.dn1.nest.dn1.ping()
    assert await hub.dn1.nest.dn2.ping()
    assert await hub.dn1.nest.dn3.ping()
    assert await hub.dn1.nest.next.test.ping()
    assert await hub.dn1.nest.next.last.test.ping()


async def test_existing_dyne(hub):
    await hub.pns.sub.add(dyne_name="dn1")
    await hub.pns.sub.load_subdirs(hub.dn1, recurse=True)
    assert "nest" in hub.dn1._subs
    assert "nest" not in hub.dn1._loaded
    # Add the same dyne again without recursing it and verify that the recursive elements are still there
    await hub.pns.sub.add(dyne_name="dn1")
    assert "nest" in hub.dn1._subs
    assert "nest" not in hub.dn1._loaded


async def test_dyne_extend(hub):
    await hub.pns.sub.add(dyne_name="dn1")
    await hub.pns.sub.load_subdirs(hub.dn1, recurse=True)
    assert await hub.dn1.nest.over.in_dn1()
    assert await hub.dn1.nest.over.in_dn2()
    assert await hub.dn1.nest.over.in_dn3()


async def test_dyne_overwrite(hub):
    await hub.pns.sub.add(dyne_name="dn1")
    await hub.pns.sub.load_subdirs(hub.dn1, recurse=True)
    # Assure that the first instance of a function does not get overwritten
    assert await hub.dn1.nest.over.source() == "dn1"


async def test_contract_signatures(hub):
    hub.LOAD_PASS = True
    hub.LOAD_FAIL = False
    # These functions should load no problem
    await hub.pns.sub.add(pypath=["tests.pns.mods.contract_sig"])


async def test_contract_signature_fail(hub):
    hub.LOAD_PASS = False
    hub.LOAD_FAIL = True
    # These functions should load with sig failures
    with pytest.raises(pns.exc.ContractSigException) as e:
        await hub.pns.sub.add(pypath=["tests.pns.mods.contract_sig"])
    errs = e.value.args[0].splitlines()

    assert "Signature Errors" in errs[0]

    filtered_errs = set({e for e in errs[1:-1] if "Enforcing signature" not in e})
    assert filtered_errs == {
        "args: **kwargs are not permitted as a parameter",
        "kwargs: *args are not permitted as a parameter",
    }


async def test_reload(hub):
    await hub.pns.sub.add(dyne_name="dn1")
    assert await hub.pns.sub.reload("dn1")


async def test_reload_fail(hub):
    assert not await hub.pns.sub.reload("nonexistant")
