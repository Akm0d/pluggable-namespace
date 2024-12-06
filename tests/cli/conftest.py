import shutil
import sys
import tempfile
from unittest import mock
import pns.hub

import pathlib
import pytest
import yaml


@pytest.fixture(name="hub")
async def testing_hub():
    yield await pns.hub.new(logs=True)


@pytest.fixture(autouse=True)
async def tpath():
    tpath_dir = pathlib.Path(__file__).parent / "tpath"

    assert tpath_dir.exists()

    new_path = [str(tpath_dir)] + sys.path

    with mock.patch("sys.path", new_path):
        yield


@pytest.fixture(autouse=True)
async def temp_mod_dir():
    """
    A location added to the hub that contains modules we can create, delete, and modify
    """
    mod_dir = pathlib.Path(tempfile.mkdtemp())
    ext_dir = mod_dir / "ext"

    # Load python files under the "src" directory under "hub.plugin"
    config = {"dyne": {"plugin": ["src"]}}
    config_file = ext_dir / "config.yaml"

    # Ensure that the plugin dir exists
    plugin_dir = ext_dir / "src"
    plugin_dir.mkdir(parents=True, exist_ok=True)

    with config_file.open("w+") as fh:
        fh.write(yaml.safe_dump(config))

    new_path = [str(mod_dir)]
    for p in sys.path:
        if p not in new_path:
            new_path.append(p)

    with mock.patch("sys.path", new_path):
        yield plugin_dir

    shutil.rmtree(ext_dir)
