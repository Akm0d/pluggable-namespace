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

# TODO create an "internal" dyne that we can use to extend the loadedmod with features dynamically
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._var = {}
        self._func = {}
        self._class = {}

    @property
    def _nest(self):
        return {**self._class, **self._var, **self._func}

    @_nest.setter
    def _nest(self, value): ...


def load(path: str):
    """Load a module by name and file path into sys.modules."""
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


async def prep(
    hub, sub: pns.hub.Sub, name: str, mod: ModuleType, contracts: list[str]
) -> LoadedMod:
    loaded = LoadedMod(name=name, parent=sub, root=hub)
    if hasattr(mod, VIRTUAL_NAME):
        loaded._alias.add(getattr(mod, VIRTUAL_NAME))

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

    return await populate(loaded, mod, contracts)


async def populate(loaded, mod: ModuleType, contracts: list[str]):
    """
    Add functions, classes, and variables to the hub considering function aliases
    """
    # TODO have an "implicit_alias" for functions that end in "_" and shadow builtins

    # Retrieve function aliases if any
    __func_alias__ = getattr(mod, FUNC_ALIAS, {})
    if inspect.isfunction(__func_alias__):
        __func_alias__ = __func_alias__(loaded._)
        if asyncio.iscoroutine(__func_alias__):
            __func_alias__ = await __func_alias__

    # Iterate over all attributes in the module
    for attr in getattr(mod, "__load__", dir(mod)):
        # Avoid omitted names
        if attr.startswith(OMIT_START) or attr.endswith(OMIT_END):
            continue

        orig_name = attr
        # Get the function alias if available
        name = __func_alias__.get(attr, attr)
        obj = getattr(mod, orig_name)

        if inspect.isfunction(obj):
            # TODO save dunder methods in the module and attach them to the loadedmod object
            if OMIT_FUNC:
                continue
            # It's a function, potentially make it async
            if not asyncio.iscoroutinefunction(obj):
                # Convert to async if not already
                func = pns.loop.make_async(obj)
            else:
                func = obj

            contracted_func = pns.contract.Contracted(
                func=func,
                name=name,
                parent=loaded,
                root=loaded._,
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

    return loaded


def load_from_path(modname: str, path: pathlib.Path, ext: str = ".py"):
    """
    Attempt to load the Python module named `modname` from the specified `path`.
    :param modname: The name of the module to load.
    :param path: The directory path to use as the anchor point to resolve the module.
    :return: The loaded module if successful, or None if not found.
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
