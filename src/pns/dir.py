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


def walk(pypath: list[str] = None, static: list[str] = None) -> list[pathlib.Path]:
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
        except:
            msg = "Unsupported file format"
            raise ValueError(msg)

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
