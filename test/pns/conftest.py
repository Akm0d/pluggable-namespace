import sys
from unittest import mock

import pathlib
import pytest

import pns.shim


@pytest.fixture(name="hub")
async def minimal_hub():
    hub = await pns.shim.loaded_hub(
        # Let each test manually add their structure
        load_all_dynes=False,
        load_all_subdirs=False,
        # recurse_subdirs=False,
        logs=False,
        load_config=False,
    )
    yield hub


@pytest.fixture(autouse=True)
async def tpath():
    tpath_dir = pathlib.Path(__file__).parent / "tpath"

    assert tpath_dir.exists()

    new_path = [str(tpath_dir)] + sys.path

    with mock.patch("sys.path", new_path):
        yield
