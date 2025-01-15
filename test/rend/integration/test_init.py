"""
tests.unit.rend.init
~~~~~~~~~~~~~~

Tests for unit.rend.init
"""

import os

import pytest


@pytest.mark.asyncio
async def test_rend_parse_jinja_exc(hub, FDIR):
    """
    test rend.init.parse when RendererException
    raised with jinja renderer
    """
    fn_ = os.path.join(FDIR, "test_exc.jinja2")
    with pytest.raises(hub.exc.rend.RenderError) as exc:
        await hub.rend.init.parse(fn_, "jinja")
    assert (
        exc.value.args[0] == "Jinja syntax error: Encountered unknown tag 'test_exc'."
    )


@pytest.mark.asyncio
async def test_rend_parse_yaml_exc(hub, FDIR):
    """
    test rend.init.parse when RendererException
    raised with yaml renderer
    """

    fn_ = os.path.join(FDIR, "test_exc.yaml.dontfix")
    with pytest.raises(hub.exc.rend.RenderError) as exc:
        await hub.rend.init.parse(fn_, "yaml")
    assert (
        exc.value.args[0]
        == "Yaml render error: while parsing a node on line: 0 column: 0 found undefined tag handle on line: 0 column: 0"
    )


@pytest.mark.asyncio
async def test_rend_parse_toml_exc(hub, FDIR):
    """
    test rend.init.parse when RendererException
    raised with toml renderer
    """

    fn_ = os.path.join(FDIR, "test_exc.toml")
    with pytest.raises(hub.exc.rend.RenderError) as exc:
        await hub.rend.init.parse(fn_, "toml")
    assert (
        exc.value.args[0]
        == "Toml render error: Empty value is invalid on line: 6 column: 1"
    )


async def test_empty_blocks(hub, FDIR):
    """
    Test that code blocks without any data don't get rendered
    """

    fn = os.path.join(FDIR, "empty.sls")
    data = await hub.rend.init.blocks(fn)
    for ref, block in data.items():
        assert block["bytes"]


async def test_blocks(hub, FDIR):
    """
    Test that the block seperation and rendering works
    """

    fn = os.path.join(FDIR, "test.sls")
    data = await hub.rend.init.blocks(fn)
    for ref, block in data.items():
        if ref == "raw":
            assert not block["bytes"]
            assert block["ln"] == 0
            continue
        if block["ln"] == 3:
            assert block["keys"] == {"require": "red"}
            assert block["bytes"] == b"red:\n  rum: 5\n"
        if block["ln"] == 6:
            assert block["pipe"] == [b"toml"]
        if ref != "raw" and block["ln"] == 0:
            assert block["keys"] == {"require": "cheese"}
            assert block["bytes"] == b"foo:\n  bar: baz\n"
        assert fn == block["fn"]


async def test_blocks_with_content(hub, FDIR):
    fn = os.path.join(FDIR, "test.sls")
    content = None
    with open(fn, "rb") as rfh:
        content = rfh.read()
    assert content is not None
    fake_fn = fn + "_fake"
    # We pass a fake file path to verify that, when content is available as an input, blocks() function should not read the file
    data = await hub.rend.init.blocks(fn=fake_fn, content=content)
    for ref, block in data.items():
        if ref == "raw":
            assert not block["bytes"]
            assert block["ln"] == 0
            continue
        if block["ln"] == 3:
            assert block["keys"] == {"require": "red"}
            assert block["bytes"] == b"red:\n  rum: 5\n"
        if block["ln"] == 6:
            assert block["pipe"] == [b"toml"]
        if ref != "raw" and block["ln"] == 0:
            assert block["keys"] == {"require": "cheese"}
            assert block["bytes"] == b"foo:\n  bar: baz\n"
        assert fake_fn == block["fn"]


async def test_blocks_nest(hub, FDIR):
    """
    Test that the block seperation and rendering works
    """

    fn = os.path.join(FDIR, "nest.sls")
    data = await hub.rend.init.blocks(fn)
    for ref, block in data.items():
        if ref == "raw":
            assert block["bytes"] == b"raw: True\n"
            assert block["ln"] == 0
            continue
        if block["ln"] == 3:
            assert block["keys"] == {"require": "red"}
            assert block["bytes"] == b"red:\n  rum: 5\n"
        if ref != "raw" and block["ln"] == 0:
            assert block["keys"] == {"require": "cheese"}
            assert block["bytes"] == b"foo:\n  bar: baz\n"


async def test_blocks_end(hub, FDIR):
    """
    Test that the block seperation and rendering works
    """

    fn = os.path.join(FDIR, "end.sls")
    data = await hub.rend.init.blocks(fn)
    for ref, block in data.items():
        if ref == "raw":
            assert not block["bytes"]
            assert block["ln"] == 0
            continue
        if block["ln"] == 3:
            assert block["keys"] == {"require": "red"}
            assert block["bytes"] == b"red:\n  rum: 5\n"
        if ref != "raw" and block["ln"] == 0:
            assert block["keys"] == {"require": "cheese"}
            assert block["bytes"] == b"foo:\n  bar: baz\n"


async def test_blocks_each(hub, FDIR):
    """
    Test that the block seperation and rendering works
    """

    fn = os.path.join(FDIR, "each_end.sls")
    data = await hub.rend.init.blocks(fn)
    for ref, block in data.items():
        if ref == "raw":
            assert not block["bytes"]
            assert block["ln"] == 0
            continue
        if block["ln"] == 3:
            assert block["keys"] == {"require": "red"}
            assert block["bytes"] == b"red:\n  rum: 5\n"
        if ref != "raw" and block["ln"] == 0:
            assert block["keys"] == {"require": "cheese"}
            assert block["bytes"] == b"foo:\n  bar: baz\n"


async def test_blocks_bad_end(hub, FDIR):
    """
    Test that the block seperation and rendering works
    """

    fn = os.path.join(FDIR, "bad_end.sls")
    with pytest.raises(hub.exc.rend.RenderError) as exc:
        await hub.rend.init.blocks(fn)
    assert exc.value.args[0] == "Unexpected End of file line 8"
