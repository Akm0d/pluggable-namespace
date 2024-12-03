from pathlib import Path

current_dir = Path(globals()["__file__"]).parent


async def test_masked_contracts(hub):
    await hub.pns.sub.add(
        pypath=["tests.regression.contract_masking.sub"],
        contracts_static=[
            current_dir / "contract1",
            current_dir / "contract2",
        ],
    )
    val = await hub.sub.test.func()
    assert len(val) == 2
    assert val == ["contract2", "contract1"]


async def test_masked_recursive_contracts(hub):
    await hub.pns.sub.add(
        pypath=["tests.regression.contract_masking.sub"],
        recursive_contracts_static=[
            current_dir / "contract1",
            current_dir / "contract2",
        ],
    )
    val = await hub.sub.test.func()
    assert len(val) == 2
    assert val == ["contract2", "contract1"]
