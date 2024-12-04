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
    code_dir = pathlib.Path(__file__).parent.parent.absolute()
    assert code_dir.exists()

    tests_dir = code_dir / "tests"
    tpath_dir = tests_dir / "tpath"
    assert tpath_dir.exists()

    new_path = [str(code_dir), str(tests_dir), str(tpath_dir)]

    for p in sys.path:
        if p not in new_path:
            new_path.append(p)

    with mock.patch("sys.path", new_path):
        yield
