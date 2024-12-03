"""
Find directories
"""

import importlib.resources
import os
import pathlib
import sys
from collections import defaultdict
from collections.abc import Iterable

import msgpack
import yaml

import cpns.data


async def dir_list(pypath: list[str] = None, static: list[str] = None) -> list[pathlib.Path]:
    """
    Return the directories to look for modules in, pypath specifies files
    relative to an installed python package, static is for static dirs
    :param pypath: One or many python paths which will be imported
    :param static: Directories that can be explicitly passed
    """
    ret = set()
    if pypath:
        for path in pypath:
            try:
                mod = importlib.import_module(path)
            except ModuleNotFoundError:
                continue
            for m_path in mod.__path__:
                # If we are inside of an executable the path will be different
                ret.add(pathlib.Path(m_path))
    if static:
        ret.update(pathlib.Path(dir_) for dir_ in static)
    return sorted(ret)


async def inline_dirs(dirs: Iterable[str], subdir: str) -> list[pathlib.Path]:
    """
    Look for the named subdir in the list of dirs
    :param dirs: The names of configured dynamic dirs
    :param subdir: The name of the subdir to check for in the list of dynamic dirs
    :return An extended list of dirs that includes the found subdirs
    """
    ret = set()
    for dir_ in dirs:
        check = pathlib.Path(dir_) / subdir
        if check.is_dir():
            ret.add(check)
    return sorted(ret)


async def dynamic_dirs():
    """
    Iterate over the available python package imports and look for configured
    dynamic dirs in pyproject.toml
    """
    dirs = set()
    if os.getcwd() not in sys.path:
        sys.path.append(os.getcwd())
    for dir_ in sys.path:
        if not dir_:
            continue
        path = pathlib.Path(dir_)
        if not path.is_dir():
            continue
        for sub in path.iterdir():
            full = path / sub
            if str(sub).endswith(".egg-link"):
                with full.open() as rfh:
                    dirs.add(pathlib.Path((rfh.read()).strip()))
            elif full.is_dir():
                dirs.add(full)

    # Set up the _dynamic return
    ret = cpns.data.NamespaceDict(
        dyne=cpns.data.NamespaceDict(),
        config=cpns.data.NamespaceDict(),
        imports__=cpns.data.NamespaceDict(),
    )

    # Iterate over namespaces in sys.path
    for dir_ in dirs:
        # Prefer msgpack configuration if available
        config_msgpack = dir_ / "config.msgpack"
        config_yaml = dir_ / "config.yaml"

        config_file = config_msgpack if config_msgpack.is_file() else None
        if not config_file and config_yaml.is_file():
            config_file = config_yaml

        if not config_file:
            # No configuration found, continue with the next directory
            continue

        dynes, configs, imports = await parse_config(config_file)
        if dynes:
            cpns.data.update(ret.dyne, dynes, merge_lists=True)
        if configs:
            cpns.data.update(ret.config, configs, merge_lists=True)
        if imports:
            cpns.data.update(ret.imports__, imports)

    return ret


async def parse_config(
    config_file: pathlib.Path,
) -> tuple[dict[str, object], dict[str, object], set[str]]:
    dyne = defaultdict(lambda: cpns.data.NamespaceDict(paths=set()))
    config = cpns.data.NamespaceDict(
        config=cpns.data.NamespaceDict(),
        cli_config=cpns.data.NamespaceDict(),
        subcommands=cpns.data.NamespaceDict(),
    )
    imports = cpns.data.NamespaceDict()

    if not config_file.is_file():
        return dyne, config, imports

    with config_file.open("rb") as f:
        file_contents = f.read()
        if config_file.suffix in (".yaml", ".yml"):
            pns_config = yaml.safe_load(file_contents) or {}
        elif config_file.suffix == ".msgpack":
            pns_config = msgpack.unpackb(file_contents) or {}
        else:
            msg = "Unsupported file format"
            raise ValueError(msg)

    # Gather dynamic namespace paths for this import
    for name, paths in pns_config.get("dyne", {}).items():
        for path in paths:
            ref = config_file.parent / path.replace(".", os.sep)
            dyne[name]["paths"].add(ref)

    # Get config sections
    for section in ["config", "cli_config", "subcommands"]:
        section_data = pns_config.get(section)
        if not isinstance(section_data, dict):
            continue
        for namespace, data in section_data.items():
            if data is None:
                continue
            config[section].setdefault(namespace, cpns.data.NamespaceDict()).update(data)

    # Handle python imports
    for imp in pns_config.get("import", []):
        base = imp.split(".", 1)[0]
        if base not in imports:
            try:
                imports[base] = importlib.import_module(base)
            except ModuleNotFoundError:
                ...
        if "." in imp:
            try:
                importlib.import_module(imp)
            except ModuleNotFoundError:
                ...

    for name in dyne:
        dyne[name]["paths"] = sorted(dyne[name]["paths"])

    return dyne, config, imports
