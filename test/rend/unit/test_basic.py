import os

import pytest


@pytest.mark.asyncio
async def test_yaml(hub, FDIR):
    fn = os.path.join(FDIR, "test.yml")
    ret = await hub.rend.init.parse(fn, "yaml")
    assert ret == {"test": {"foo": "bar"}}


@pytest.mark.asyncio
async def test_ordered_yaml(hub, FDIR):
    fn = os.path.join(FDIR, "order.yml")
    ret = await hub.rend.init.parse(fn, "yaml")
    assert list(ret.keys()) == ["first", "second", "third", "forth", "fifth"]
    assert list(ret["first"].keys()) == [1, 2, 3, 7, 4]


@pytest.mark.asyncio
async def test_toml(hub, FDIR):
    fn = os.path.join(FDIR, "test.toml")
    ret = await hub.rend.init.parse(fn, "toml")
    assert ret == {"test": {"foo": "bar"}}


@pytest.mark.asyncio
async def test_shebang(hub, FDIR):
    fn = os.path.join(FDIR, "shebang.yml")
    ret = await hub.rend.init.parse(
        fn, "toml"
    )  # Pass in bad pipe so we use the one in the file
    assert ret == {"test": {"foo": "bar"}}
