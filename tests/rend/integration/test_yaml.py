"""
tests.unit.rend.test_yaml
~~~~~~~~~~~~~~

Unit tests for the yaml renderer
"""
from collections.abc import Mapping

import pytest


@pytest.mark.parametrize("data", [b"test: one", "test: one"])
async def test_yaml(hub, data):
    """
    test rend.yaml.render renders correctly
    """

    ret = await hub.rend.yaml.render(data)
    assert isinstance(ret, dict)
    assert ret["test"] == "one"


class CustomDict(dict):
    pass


class CustomMapping(Mapping):
    def __init__(self, d=None):
        self._data = d or {}

    def __getitem__(self, k):
        return self._data[k]

    def __iter__(self):
        return (k for k in self._data.keys())

    def __len__(self):
        return len(self._data)


@pytest.mark.parametrize("DictLike", [CustomDict, CustomMapping])
async def test_yaml_custom_dict_like(hub, DictLike):
    data = {"k": "v"}

    ret = await hub.output.yaml.display(DictLike(data))
    assert ret == "k: v\n"


async def test_yaml_scanner_exc(hub):
    """
    test rend.yaml.render when there is a scanner error
    """

    with pytest.raises(hub.exc.rend.RenderError) as exc:
        await hub.rend.yaml.render("test:\none")
    assert (
        exc.value.args[0] == "Yaml render error: while scanning a simple key "
        "on line: 1 column: 0 could not find expected ':' on line: 2 column: 0"
    )


async def test_yaml_parser_exc(hub):
    """
    test rend.yaml.render when there is a parser error
    """

    with pytest.raises(hub.exc.rend.RenderError) as exc:
        await hub.rend.yaml.render("- !-!str just a string")
    assert (
        exc.value.args[0] == "Yaml render error: while parsing a node "
        "on line: 0 column: 2 found undefined tag handle on line: 0 column: 2"
    )


async def test_yaml_constructor_exc(hub):
    """
    test rend.yaml.render when there is a contructor error
    """

    with pytest.raises(hub.exc.rend.RenderError) as exc:
        await hub.rend.yaml.render("- !!!str just a string:one")
    assert (
        exc.value.args[0] == "Yaml render error: could not determine a "
        "constructor for the tag 'tag:yaml.org,2002:!str' on line: 0 column: 2"
    )


async def test_duplicate_keys(hub):
    data = """foo: bar
foo: bar
    """

    with pytest.raises(hub.exc.rend.RenderError) as exc:
        await hub.rend.yaml.render(data)
    assert (
        exc.value.args[0] == "Yaml render error: while constructing a mapping "
        "on line: 0 column: 0 found conflicting ID 'foo' on line: 1 column: 0"
    )


async def test_no_colon(hub):
    data = """foo1: bar
foo2
    """

    with pytest.raises(hub.exc.rend.RenderError) as exc:
        await hub.rend.yaml.render(data)
    assert (
        exc.value.args[0] == "Yaml render error: while scanning a simple key "
        "on line: 1 column: 0 could not find expected ':' on line: 2 column: 4"
    )
