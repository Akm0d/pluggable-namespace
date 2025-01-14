from pathlib import Path

current_dir = Path(globals()["__file__"]).parent


async def test_repeated_recursive_contracts(hub):
    # A scenario similar to this could occur when recursive contracts
    # were defined on a parent Sub, and a different set of recursive contracts
    # including some of the same contracts were defined on a child Sub.
    await hub.pop.sub.add(
        locations=["test.pnsregression.contract_masking.sub"],
        recursive_contract_locations=[
            current_dir / "contract1",
            current_dir / "contract2",
            current_dir / "contract2",
        ],
    )
    val = await hub.sub.test.func()
    assert len(val) == 2
    assert val == ["contract2", "contract1"]
