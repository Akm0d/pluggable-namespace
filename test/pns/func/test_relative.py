"""
Test relative paths like _ and __
"""


async def test_hub_parent(hub):
    assert hub.__ is None


async def test_sub_parent_hub(hub):
    assert hub.pop.__ is hub


async def test_sub_parent_sub(hub):
    await hub.pop.sub.add(locations=["test.pns.mods"])
    await hub.pop.sub.add(locations=["test.pns.mods.nest"], sub=hub.mods)
    assert hub.mods.nest.__ is hub.mods


async def test_mod_parent(hub):
    assert hub.pop.sub.__ is hub.pop


async def test_contracted_parent(hub):
    assert hub.pop.sub.add.__ is hub.pop.sub


async def test_current_mod(hub):
    await hub.pop.sub.add(locations=["test.pns.mods"])
    await hub.mods.dunder.func()
