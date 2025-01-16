from pathlib import Path

current_dir = Path(globals()["__file__"]).parent


async def test_masked_contracts(hub):
    await hub.pop.sub.add(
        locations=["test.pns.regression.contract_masking.sub"],
        contract_locations=[
            current_dir / "contract1",
            current_dir / "contract2",
        ],
    )
    val = await hub.sub.test.func()
    assert len(val) == 2
    assert val == ["contract2", "contract1"]


async def test_masked_recursive_contracts(hub):
    await hub.pop.sub.add(
        locations=["test.pns.regression.contract_masking.sub"],
        recursive_contract_locations=[
            current_dir / "contract1",
            current_dir / "contract2",
        ],
    )
    val = await hub.sub.test.func()
    assert len(val) == 2
    assert val == ["contract2", "contract1"]
