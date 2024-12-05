import pathlib
import sys
from unittest import mock

import pns.hub
import pytest


@pytest.fixture(name="hub")
async def testing_hub():
    async with pns.hub.Hub() as hub:
        yield hub


@pytest.fixture(autouse=True)
async def tpath():
    tpath_dir = pathlib.Path(__file__).parent / "tpath"

    assert tpath_dir.exists()

    new_path = [str(tpath_dir)] + sys.path

    with mock.patch("sys.path", new_path):
        yield


@pytest.fixture(scope="session")
def FDIR():
    return pathlib.Path(__file__).parent / "files"
