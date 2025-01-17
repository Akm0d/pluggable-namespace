import pytest

import pns.ref


@pytest.fixture
async def hub(hub):
    await hub.pop.sub.add("test")
    await hub.pop.sub.add("subtest", sub=hub.test)
    hub.test.subtest.attr = "value"
    hub.test.subtest.dict_attr = {"key": "dict_value"}
    hub.test.subtest.list_attr = ["list_value"]
    return hub


async def test_last_str(hub):
    assert pns.ref.last(hub, "test.subtest.attr") == "value"


def test_path(hub):
    path = pns.ref.path(hub, "test.subtest.attr")
    assert path == [hub, hub.test, hub.test.subtest, "value"]


def test_find(hub):
    assert pns.ref.find(hub, "test.subtest.attr") == "value"
    assert pns.ref.find(hub, "test.subtest.dict_attr.key") == "dict_value"
    assert pns.ref.find(hub, "test.subtest.list_attr.0") == "list_value"
    with pytest.raises(AttributeError):
        pns.ref.find(hub, "test.subtest.nonexistent")
