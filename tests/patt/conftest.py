import pathlib
import sys
from unittest import mock

import pytest

import pns.hub


@pytest.fixture(name="hub")
async def integration_hub():
    async with pns.hub.Hub() as hub:
        await hub.patt.sh.add_sub()
        yield hub


@pytest.fixture(autouse=True)
async def tpath():
    tpath_dir = pathlib.Path(__file__).parent / "tpath"

    assert tpath_dir.exists()

    new_path = [str(tpath_dir)] + sys.path

    with mock.patch("sys.path", new_path):
        yield
