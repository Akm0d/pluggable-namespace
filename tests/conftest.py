import sys
from unittest import mock

import pathlib
import pytest

import pns


@pytest.fixture
async def hub():
    async with pns.Hub(
        # Let each test manually add their structure
        load_all_dynes=False,
        load_all_subdirs=False,
        recurse_subdirs=False,
        logs=False,
        load_config=False,
    ) as hub:
        yield hub


@pytest.fixture(autouse=True)
async def tpath():
    tpath_dir = pathlib.Path(__file__).parent / "tpath"
    assert tpath_dir.exists()

    new_path = [str(tpath_dir)] + sys.path

    with mock.patch("sys.path", new_path):
        yield
