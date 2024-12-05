import pathlib
import sys
from unittest import mock

import pns.hub
import pytest


@pytest.fixture(name="hub")
async def integration_hub():
    async with pns.hub.Hub() as hub:
        hub._auto(hub._holder())
        yield hub
        await hub.pns.task.cancel()

@pytest.fixture(autouse=True)
async def tpath():
    tpath_dir = pathlib.Path(__file__).parent / "tpath"
    assert tpath_dir.exists()

    new_path = [str(tpath_dir)] + sys.path

    with mock.patch("sys.path", new_path):
        yield
