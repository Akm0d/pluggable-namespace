import pytest


async def test_verror_does_not_overload_loaded_mod(hub):
    """
    This tests will load 2 mods under the vname virtualname, however, one of them
    will explicitly not load. This makes sure load errors to not shadow good mod loads
    """
    await hub.pop.sub.add(
        locations=["test.pns.mods.same_vname"],
        name="mods",
    )
    assert await hub.mods.vname.func() == "wha? Yep!"


async def test_module_doesnt_exist(hub):
    await hub.pop.sub.add(locations=["test.pns.mods"])
    with pytest.raises(AttributeError, match=".* has no attribute 'doesntexist'"):
        await hub.mods.doesntexist
