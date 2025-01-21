"""
Module management functionalities for dynamically loading and populating modules within a pluggable namespace system.

This module facilitates the dynamic loading, preparation, and integration of Python modules into a plugin-oriented architecture.
It includes functions to load modules from specified paths, populate them with metadata, functions, classes, and variables,
and apply any necessary transformations or contracts. The functionality provided by this module is essential for systems
that rely on dynamic extension and customization through external modules or plugins.

Key Components:
- LoadedMod: A class that represents a dynamically loaded module, equipped with functionalities to populate itself with various
    attributes from the actual Python module.
- load: Function to load a module into sys.modules based on its Python path.
- prep: Function to prepare a loaded module with necessary transformations and to evaluate its eligibility via virtual conditions.
- populate: Function to populate a loaded module with its components while applying any necessary aliases or transformations.
- load_from_path: Function to load a module from a specific filesystem path.
"""

import pathlib
import sys
import asyncio
import inspect
import pns.contract
import pns.data
import os.path
from types import ModuleType

import importlib.util
import importlib.machinery

VIRTUAL = "__virtual__"
VIRTUAL_NAME = "__virtualname__"
CONFIG = "conf.yaml"
FUNC_ALIAS = "__func_alias__"
OMIT_FUNC = False
OMIT_CLASS = False
OMIT_VARS = False
OMIT_START = ("_",)
OMIT_END = ()


class LoadedMod(pns.data.Namespace):
    """
    Represents a dynamically loaded module within the namespace, encapsulating various module components.

    This class extends pns.data.Namespace to provide structured access to module attributes like variables, functions,
    and classes, categorizing them under respective dictionaries for easy access and manipulation.

    Attributes:
        _var (dict): Dictionary to hold module variables.
        _func (dict): Dictionary to hold module functions.
        _class (dict): Dictionary to hold module classes.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._var = {}
        self._func = {}
        self._class = {}

    @property
    def _nest(self):
        """Combines variables, functions, and classes into a single dictionary for unified access."""
        return {**self._class, **self._var, **self._func}

    @_nest.setter
    def _nest(self, value): ...


def load(path: str):
    """
    Load a module by its name and path into sys.modules, if not already loaded.

    Parameters:
        path (str): The module path or Python import path.

    Returns:
        ModuleType or None: The loaded module if successful; None if the module cannot be loaded.
    """
    ret = None
    if path in sys.modules:
        return sys.modules[path]

    builder = []
    for part in path.split("."):
        builder.append(part)
        try:
            ret = importlib.import_module(".".join(builder))
        except ModuleNotFoundError:
            ret = getattr(ret, part)

    return ret


async def prep(hub, sub: pns.hub.Sub, name: str, mod: ModuleType) -> LoadedMod:
    """
    Prepare a loaded module, applying virtual conditions and populating it with its components.

    Parameters:
        hub (pns.hub.Hub): The central hub of the system.
        sub (pns.hub.Sub): The sub-namespace that the module belongs to.
        name (str): The name of the module.
        mod (ModuleType): The Python module to prepare.

    Returns:
        LoadedMod: The prepared and populated module.

    Raises:
        NotImplementedError: If the virtual condition check fails and the module is deemed ineligible.
    """
    modname = getattr(mod, VIRTUAL_NAME, name)
    loaded = LoadedMod(name=modname, parent=sub, root=hub)

    # Execute the __virtual__ function if present
    if hasattr(mod, VIRTUAL):
        virtual = pns.contract.Contracted(
            name=VIRTUAL,
            func=getattr(mod, VIRTUAL),
            parent=loaded,
            root=hub,
        )
        ret = virtual()
        if asyncio.iscoroutine(ret):
            ret = await ret

        error = None
        if ret is True:
            ...
        elif ret is False:
            error = "Virtual returned False"
        elif isinstance(ret, str):
            error = ret
        elif len(ret) > 1 and ret[0] is False:
            error = ret[1]

        if error:
            del loaded
            raise NotImplementedError(f"{sub.__ref__}.{name} virtual failed: {error}")

    return await populate(loaded, mod)


# Alias builtin function names to their name + underscore
BUILTIN_ALIAS = {f"{k}_": k for k in __builtins__}


async def populate(loaded, mod: ModuleType, *, implicit_alias: bool = True):
    """
    Populate a LoadedMod instance with functions, classes, and variables from a given Python module,
    applying aliases and converting synchronous functions to asynchronous when appropriate.

    Parameters:
        loaded (LoadedMod): The LoadedMod instance to populate.
        mod (ModuleType): The module from which to load components.
        implicit_alias (bool): Indicates whether to automatically apply built-in function aliases.

    Returns:
        LoadedMod: The updated LoadedMod instance with newly added components.

    Details:
        - Function aliases are applied based on `__func_alias__` or automatic rules.
        - Functions are converted to asynchronous versions if they aren't already.
        - Classes and variables are directly added unless omitted by configuration.
        - Ensures that function signatures match any applicable contracts, throwing an error if they do not align.
    """
    # Retrieve function aliases if any
    __func_alias__ = getattr(mod, FUNC_ALIAS, {})
    if inspect.isfunction(__func_alias__):
        __func_alias__ = __func_alias__(loaded._)
        if asyncio.iscoroutine(__func_alias__):
            __func_alias__ = await __func_alias__

    if implicit_alias:
        pns.data.update(__func_alias__, BUILTIN_ALIAS)

    # Iterate over all attributes in the module
    for attr in getattr(mod, "__load__", mod.__dict__.keys()):
        # Avoid omitted names
        if attr.startswith(OMIT_START) or attr.endswith(OMIT_END):
            continue

        orig_name = attr
        # Get the function alias if available
        name = __func_alias__.get(attr, attr)
        obj = getattr(mod, orig_name)

        if inspect.isfunction(obj):
            if OMIT_FUNC:
                continue
            # It's a function, potentially make it async
            if not asyncio.iscoroutinefunction(obj):
                # Convert to async if not already
                func = pns.loop.make_async(obj)
            else:
                func = obj

            # Make sure the aliased func name gets in there
            matched_contracts = pns.contract.match(loaded, name)
            contracted_func = pns.contract.Contracted(
                func=func,
                name=name,
                parent=loaded,
                root=loaded._,
                contracts=matched_contracts,
            )

            loaded._func[name] = contracted_func
        elif inspect.isclass(obj):
            # It's a class
            if OMIT_CLASS:
                continue
            loaded._class[name] = obj
        else:
            if OMIT_VARS:
                continue
            # It's a variable
            loaded._var[name] = obj

    # Make sure that the signature of functions in the module match the contracts
    if __debug__:
        pns.contract.verify_sig(loaded)
    return loaded


def load_from_path(modname: str, path: pathlib.Path, ext: str = ".py") -> ModuleType:
    """
    Load a Python module from a specified file path, ensuring that it is registered in `sys.modules`.

    Parameters:
        modname (str): The name of the module to load.
        path (pathlib.Path): The directory path where the module file is expected to be.
        ext (str): The file extension of the module, default is ".py".

    Returns:
        ModuleType or None: The loaded module if successful, or None if the module cannot be found or loaded.

    Details:
        - The function attempts to resolve the full path of the module file from the given directory.
        - If the module is already loaded (present in `sys.modules`), it returns the existing module.
        - Otherwise, it loads the module using the `importlib` utilities and adds it to `sys.modules`.
    """
    # Convert the given path to a Path object and resolve the module file path
    module_path = path / (modname.replace(".", "/") + ext)

    if not module_path.is_file():
        return None

    # Using the absolute path for the module
    module_abs_path = module_path.resolve()
    # Create a unique module key with its full path
    module_key = (
        str(module_abs_path.parent).replace(os.path.sep, ".").lstrip(".")
        + "."
        + modname
    )

    # If this unique module path is already in sys.modules, return it
    if module_key in sys.modules:
        return sys.modules[module_key]

    # Generate the module spec
    spec = importlib.util.spec_from_file_location(modname, module_abs_path)
    if spec is None:
        return None

    # Load the module
    module = importlib.util.module_from_spec(spec)
    # Store the module in sys.modules with the unique key
    sys.modules[module_key] = module
    spec.loader.exec_module(module)
    return module
