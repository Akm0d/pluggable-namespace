"""
tests.unit.rend.test_toml
~~~~~~~~~~~~~~

Unit tests for the toml renderer
"""
import pytest


async def test_toml(hub):
    """
    test rend.toml.render renders correctly
    """
    data = """
    # I promise this is toml data
    title = 'toml test'
    [owner]
    name = 'toml owner'
    """

    ret = await hub.rend.toml.render(data)
    assert ret["title"] == "toml test"
    assert ret["owner"]["name"] == "toml owner"


async def test_toml_bytes(hub):
    """
    test rend.toml.render renders correctly with bytes data
    """
    data = b"""
    # I promise this is toml data
    title = 'toml test'
    [owner]
    name = 'toml owner'
    """

    ret = await hub.rend.toml.render(data)
    assert ret["title"] == "toml test"
    assert ret["owner"]["name"] == "toml owner"


async def test_toml_decode_error(hub):
    """
    test rend.toml.render when there is a decode error
    """
    data = """
    # I promise this is toml data
    title = 'toml test'
    [owner
    name = 'toml owner'
    """

    with pytest.raises(hub.exc.rend.RenderError) as exc:
        await hub.rend.toml.render(data)
    assert exc.value.args[0] == "Toml render error: Key group not on a line by itself. on line: 4 column: 1"
