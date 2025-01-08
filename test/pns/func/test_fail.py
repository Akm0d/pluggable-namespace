# pylint: disable=expression-not-assigned
# Import pytest
import pytest

# import pns.exc

# Import pns


async def _test_calling_load_error_raises_pns_error(hub):
    """
    In this test, pns will continue loading although, when trying to
    access a functions which should be accessible on the module, a
    PnsError is raised.
    """
    await hub.pns.sub.add(pypath=["test.pns.mods"], stop_on_failures=True)
    with pytest.raises(pns.exc.PnsError, match="Failed to load python module"):
        await hub.mods.bad_import.func()


async def test_verror_does_not_overload_loaded_mod(hub):
    """
    This tests will load 2 mods under the vname virtualname, however, one of them
    will explicitly not load. This makes sure load errors to not shadow good mod loads
    """
    await hub.pns.sub.add(
        pypath=["test.pnsmods.same_vname"],
        subname="mods",
    )
    assert await hub.mods.vname.func() == "wha? Yep!"


async def test_module_doesnt_exist(hub):
    await hub.pns.sub.add(pypath=["test.pns.mods"])
    with pytest.raises(AttributeError, match="'mods' has no attribute 'doesntexist'"):
        await hub.mods.doesntexist
