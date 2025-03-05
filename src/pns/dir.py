"""
Utilities for discovering and managing directories within a pluggable namespace system.

This module provides functionalities for locating and managing directories that are part of the dynamic
namespace system used in a plugin-oriented architecture. It includes functions to walk through directory
paths, dynamically discover configuration directories, and parse configuration files related to the namespace.

Key Functions:
    - walk: Retrieves a list of pathlib.Path objects representing valid directories from a list of locations.
    - dynamic: Discovers dynamically configured directories specified in 'pyproject.toml' across Python package imports.
    - inline: Finds specific subdirectories within a given list of directories.
    - parse_config: Parses a YAML configuration file to extract dynamic namespaces, configuration settings, and Python imports.

These utilities are essential for configuring and extending the functionality of dynamic namespaces, enabling
the system to adapt and configure itself based on directory and file-based configurations.
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
    Walk through a list of locations and convert them to pathlib.Path objects if they represent directories.

    This function attempts to resolve each location as either a directory on the filesystem or a Python package.
    If a location is a directory, it is directly added to the result set. If it is a Python import path, the function
    attempts to import it and access its __path__ attribute to include its directory.

    Parameters:
        locations (list[str]): A list of directory paths or Python import paths.

    Returns:
        list[pathlib.Path]: A list of resolved pathlib.Path objects for each valid directory or package directory.
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
    Dynamically discover and configure directories based on Python path entries and configuration files.

    This function scans directories listed in the Python path (`sys.path`) for configuration files
    (typically `config.yaml`) and directories linked via `.egg-link` files. It aims to build a comprehensive
    set of directories that are dynamically configured to participate in the application's namespace management.

    The function then reads and applies configurations from these discovered directories to set up dynamic namespaces,
    configurations, and imports as specified in their respective configuration files.

    Returns:
        pns.data.NamespaceDict: A nested NamespaceDict structure containing dynamically discovered configurations.
        This dictionary includes three main namespaces:
            - 'dyne': Dynamic directories with specific paths and settings derived from the configuration files.
            - 'config': General configurations loaded from the configuration files.

    Usage:
        This function is typically called at application startup to initialize and configure the dynamic
        aspects of the namespace system based on the current runtime environment and available configurations.

    Note:
        The function prioritizes `.egg-link` files to discover linked package directories, ensuring that any
        development or locally modified packages are included in the dynamic configuration. Regular directories
        within the Python path are also scanned for `config.yaml` files to load additional configurations.
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
    )

    # Iterate over namespaces in sys.path
    for dir_ in dirs:
        # Prefer msgpack configuration if available
        config_yaml = dir_ / "config.yaml"

        if not config_yaml:
            # No configuration found, continue with the next directory
            continue

        dynes, configs = parse_config(config_yaml)
        if dynes:
            pns.data.update(ret.dyne, dynes, merge_lists=True)
        if configs:
            pns.data.update(ret.config, configs, merge_lists=True)

    return ret


def inline(dirs: list[str], subdir: str) -> list[str]:
    """
    Search for a specific subdirectory within each directory in a list and return the paths where it exists.

    Parameters:
        dirs (list[str]): A list of directory paths to search within.
        subdir (str): The subdirectory to search for within each directory path.

    Returns:
        list[str]: A list of paths where the subdirectory exists within the given directory paths.
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
) -> tuple[dict[str, object], dict[str, object]]:
    """
    Parse a YAML configuration file and extract configurations for dynamic directories, general settings, and imports.

    Parameters:
        config_file (pathlib.Path): The path to the configuration file to parse.

    Returns:
        tuple: A tuple containing three elements:
            - A dictionary of dynamic namespace configurations.
            - A NamespaceDict of general configurations.
    """
    dyne = defaultdict(lambda: pns.data.NamespaceDict(paths=set()))
    config = pns.data.NamespaceDict(
        config=pns.data.NamespaceDict(),
        cli_config=pns.data.NamespaceDict(),
        subcommands=pns.data.NamespaceDict(),
    )
    imports = pns.data.NamespaceDict()

    if not config_file.is_file():
        return dyne, config

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

    return dyne, config
