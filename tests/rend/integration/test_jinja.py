"""
tests.unit.rend.test_jinja
~~~~~~~~~~~~~~

Unit tests for the jinja renderer
"""
import os
import pathlib

import jinja2.exceptions
import pytest


@pytest.mark.asyncio
async def test_jinja(hub):
    """
    test rend.jinja.render renders correctly
    """

    ret = await hub.rend.jinja.render('{% set test = "itworked" %}{{ test }}')
    assert ret == "itworked"


@pytest.mark.asyncio
async def test_jinja_bytes(hub):
    """
    test rend.jinja.render renders correctly with bytes data
    """

    ret = await hub.rend.jinja.render(b'{% set test = "itworked" %}{{ test }}')
    assert ret == "itworked"


@pytest.mark.asyncio
async def test_jinja_undefined(hub):
    """
    test rend.jinja.render when there is an undefined error
    """

    with pytest.raises(hub.exc.rend.RenderError) as exc:
        await hub.rend.jinja.render("{{ hello.test }}")
    assert exc.value.args[0] == "Jinja variable: 'hello' is undefined"


@pytest.mark.asyncio
async def test_jinja_syntax(hub):
    """
    test rend.jinja.render when there is a syntax error
    """

    with pytest.raises(hub.exc.rend.RenderError) as exc:
        await hub.rend.jinja.render("{% test % }")
    assert exc.value.args[0] == "Jinja syntax error: Encountered unknown tag 'test'."


@pytest.mark.asyncio
async def test_jinja_file_include(hub, FDIR):
    """
    test rend.jinja.render renders correctly with an included file via jinja
    """
    # test include of raw yaml
    expected = "---\ntest:\n  foo: bar"
    fn = str(pathlib.PurePosixPath((FDIR / "test.yml").relative_to(os.getcwd())))
    ret = await hub.rend.jinja.render('{% include "' + fn + '" %}')
    assert ret.strip() == expected


@pytest.mark.asyncio
async def test_jinja_file_import(hub, FDIR):
    """
    test rend.jinja.render renders correctly with an imported variable via jinja
    """
    expected = "things"
    fn = str(pathlib.PurePosixPath((FDIR / "import.sls").relative_to(os.getcwd())))
    # test import of specific variable
    ret = await hub.rend.jinja.render('{% from "' + fn + '" import mytest %}{{ mytest }}')
    assert ret == expected
    # test import of all variables/macros
    ret = await hub.rend.jinja.render('{% import "' + fn + '" as awesome %}{{ awesome.mytest }}')
    assert ret == expected
    # test ability to break out of the path. this file exists, but fails due to presence of ".." in path
    fn = str(pathlib.PurePosixPath((FDIR / ".." / "files" / "import.sls").relative_to(os.getcwd())))
    with pytest.raises(jinja2.exceptions.TemplateNotFound) as exc:
        await hub.rend.jinja.render('{% from "' + fn + '" import mytest %}{{ mytest }}')
    assert exc.value.args[0] == fn


@pytest.mark.asyncio
async def test_jinja_base64_encode(hub):
    """
    test rend.jinja.render renders correctly for b64encode filter.
    """

    ret = await hub.rend.jinja.render('{% set test = "itworked" | b64encode %}{{ test }}')
    assert ret == "aXR3b3JrZWQ="


@pytest.mark.asyncio
async def test_jinja_base64_encode_when_input_is_none(hub):
    """
    test rend.jinja.render should return empty string if the input is None.
    """

    ret = await hub.rend.jinja.render("{% set test = None | b64encode %}{{ test }}")
    assert ret == ""


@pytest.mark.asyncio
async def test_jinja_base64_decode(hub):
    """
    test rend.jinja.render renders correctly for b64decode filter.
    """

    ret = await hub.rend.jinja.render('{% set test = "aXR3b3JrZWQ=" | b64decode %}{{ test }}')
    assert ret == "itworked"
