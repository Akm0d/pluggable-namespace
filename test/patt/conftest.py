import pathlib
import sys
from unittest import mock

import pytest

import pns.shim


@pytest.fixture(name="hub")
async def integration_hub():
    hub = await pns.shim.loaded_hub(load_config=False)
    yield hub


@pytest.fixture(autouse=True)
async def tpath():
    tpath_dir = pathlib.Path(__file__).parent / "tpath"

    assert tpath_dir.exists()

    new_path = [str(tpath_dir)] + sys.path

    with mock.patch("sys.path", new_path):
        yield
