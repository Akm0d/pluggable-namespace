"""
tests.unit.rend.test_json
~~~~~~~~~~~~~~

Unit tests for the json renderer
"""
import pytest


async def test_json_string(hub):
    """
    test rend.json.render renders correctly when passed a string
    """
    data = '{"test1": "one"}'

    ret = await hub.rend.json.render(data)
    assert ret == {"test1": "one"}


@pytest.mark.asyncio
async def test_json_bytes(hub):
    """
    test rend.json.render renders correctly with bytes data
    """

    ret = await hub.rend.json.render(b'{"test1": "one"}')
    assert ret == {"test1": "one"}


@pytest.mark.asyncio
async def test_json_error(hub):
    """
    test rend.json.render when there is an error
    """

    with pytest.raises(hub.exc.rend.RenderError) as exc:
        await hub.rend.json.render('{"test1"}}')
    assert exc.value.args[0] == "Json render error: Expecting ':' delimiter on line: 1 column: 9"
