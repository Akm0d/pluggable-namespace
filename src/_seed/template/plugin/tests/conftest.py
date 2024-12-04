import pathlib
import sys
from unittest import mock

import cpop.hub
import pytest


@pytest.fixture(name="hub")
async def integration_hub():
    async with cpop.hub.Hub() as hub:
        hub._auto(hub._holder())
        yield hub
        await hub.pop.task.cancel()

@pytest.fixture(autouse=True)
async def tpath():
    tpath_dir = pathlib.Path(__file__).parent / "tpath"
    assert tpath_dir.exists()

    new_path = [str(tpath_dir)] + sys.path

    with mock.patch("sys.path", new_path):
        yield
