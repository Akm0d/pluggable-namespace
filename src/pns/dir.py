"""
Find directories
"""

import importlib.resources
import os
import pathlib
import sys
from collections import defaultdict

import yaml

import pns.data


def walk(locations: list[str]) -> list[pathlib.Path]:
    """
    Given a list of locations, return a list of directory paths.
    Each location can be:
        - A filesystem directory (we'll add it directly).
        - A Python import path (we'll import and grab its __path__).
    Anything else (or unimportable) is ignored.
    """
    ret = set()

    for location in locations:
        path_candidate = pathlib.Path(location)

        if path_candidate.is_dir():
            # It's an actual directory on the filesystem
            ret.add(path_candidate)
        else:
            # Not an existing directory, assume it's a Python module/package
            try:
                mod = importlib.import_module(location)
                # Many packages store their base directories in __path__
                for m_path in mod.__path__:
                    ret.add(pathlib.Path(m_path))
            except (ModuleNotFoundError, AttributeError):
                # Either doesn't exist as a module or doesn't have __path__
                pass

    return sorted(ret)


def dynamic():
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
    ret = pns.data.NamespaceDict(
        dyne=pns.data.NamespaceDict(),
        config=pns.data.NamespaceDict(),
        imports__=pns.data.NamespaceDict(),
    )

    # Iterate over namespaces in sys.path
    for dir_ in dirs:
        # Prefer msgpack configuration if available
        config_yaml = dir_ / "config.yaml"

        if not config_yaml:
            # No configuration found, continue with the next directory
            continue

        dynes, configs, imports = parse_config(config_yaml)
        if dynes:
            pns.data.update(ret.dyne, dynes, merge_lists=True)
        if configs:
            pns.data.update(ret.config, configs, merge_lists=True)
        if imports:
            pns.data.update(ret.imports__, imports)

    return ret


def inline(dirs: list[str], subdir: str) -> list[str]:
    """
    Look for the named subdir in the list of dirs
    :param dirs: The names of configured dynamic dirs
    :param subdir: The name of the subdir to check for in the list of dynamic dirs
    :return An extended list of dirs that includes the found subdirs
    """
    ret = []
    for dir_ in dirs:
        check = os.path.join(dir_, subdir)
        if check in ret:
            continue
        if os.path.isdir(check):
            ret.append(check)
    return ret


def parse_config(
    config_file: pathlib.Path,
) -> tuple[dict[str, object], dict[str, object], set[str]]:
    dyne = defaultdict(lambda: pns.data.NamespaceDict(paths=set()))
    config = pns.data.NamespaceDict(
        config=pns.data.NamespaceDict(),
        cli_config=pns.data.NamespaceDict(),
        subcommands=pns.data.NamespaceDict(),
    )
    imports = pns.data.NamespaceDict()

    if not config_file.is_file():
        return dyne, config, imports

    with config_file.open("rb") as f:
        file_contents = f.read()
        try:
            pop_config = yaml.safe_load(file_contents) or {}
        except Exception as e:
            msg = "Unsupported file format"
            raise ValueError(msg) from e

    # Gather dynamic namespace paths for this import
    for name, paths in pop_config.get("dyne", {}).items():
        for path in paths:
            ref = config_file.parent / path.replace(".", os.sep)
            dyne[name]["paths"].add(ref)

    # Get config sections
    for section in ["config", "cli_config", "subcommands"]:
        section_data = pop_config.get(section)
        if not isinstance(section_data, dict):
            continue
        for namespace, data in section_data.items():
            if data is None:
                continue
            config[section].setdefault(namespace, pns.data.NamespaceDict()).update(data)

    # Handle python imports
    for imp in pop_config.get("import", []):
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
