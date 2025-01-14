"""
Test relative paths like _ and __
"""


async def test_hub_parent(hub):
    assert hub.__ is hub


async def test_sub_parent_hub(hub):
    assert hub.pns.__ is hub


async def test_sub_parent_sub(hub):
    await hub.pop.sub.add(locations=["test.pns.mods"])
    await hub.pop.sub.add(locations=["test.pnsmods.nest"], sub=hub.mods)
    assert hub.mods.nest.__ is hub.mods


async def test_mod_parent(hub):
    assert hub.pns.sub.__ is hub.pns


async def test_contracted_parent(hub):
    assert hub.pop.sub.add.__ is hub.pns.sub


async def test_current_mod(hub):
    await hub.pop.sub.add(locations=["test.pns.mods"])
    await hub.mods.dunder.func()
