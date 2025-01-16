import pathlib
import sys
from unittest import mock

import pns.shim
import pytest


@pytest.fixture(name="hub")
async def integration_hub():
    with mock.patch("sys.argv", ["test"]):
        hub = await pns.shim.loaded_hub()
    yield hub


@pytest.fixture(autouse=True)
async def tpath():
    tpath_dir = pathlib.Path(__file__).parent / "tpath"

    assert tpath_dir.exists()

    new_path = [str(tpath_dir)] + sys.path

    with mock.patch("sys.path", new_path):
        yield
