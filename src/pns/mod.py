import pathlib
import sys
import asyncio
import inspect
import pns.contract
import pns.hub
from types import ModuleType

import importlib.util
import importlib.machinery

# TODO, let the core hub have everything so we don't need imports even in PNS code -- even put these functions on the hub

VIRTUAL = "__virtual__"
CONFIG = "conf.yaml"
FUNC_ALIAS = "__func_alias__"

class LoadedMod(pns.hub.Namespace):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._var = {}
        self._func = {}
        self._class = {}
        self._nest = self._attrs

    @property
    def _attrs(self):
        return {**self._class, **self._var, **self._func}
        

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


async def prep(hub, sub: pns.hub.Sub, name: str, mod: ModuleType) -> LoadedMod:
    # Execute the __virtual__ function if present
    if hasattr(mod, VIRTUAL):
        virtual = pns.contract.Contracted(
            hub,
            contracts=[],
            func=getattr(mod, VIRTUAL),
            ref=f"{sub.__ref__}.{name}",
            parent=mod,
            name=VIRTUAL,
        )
        ret = virtual()
        if asyncio.iscoroutine(ret):
            ret = await ret

        if ret is False or (len(ret) > 1 and ret[0] is False):
            raise NotImplementedError(f"{sub.__ref__}.{name} virtual failed: {ret[1]}")

    loaded = LoadedMod(name=name, parent=sub, root=hub)
    return await populate(loaded, mod)

async def populate(loaded, mod: ModuleType):
    """
    Add functions, classes, and variables to the hub considering function aliases
    """
    # TODO have an "implicit_alias" for functions that end in "_" and shadow builtins
    
    # Retrieve function aliases if any
    __func_alias__ = getattr(mod, FUNC_ALIAS, {})
    if inspect.isfunction(__func_alias__):
        __func_alias__ = __func_alias__(loaded._)

    # Iterate over all attributes in the module
    for attr in getattr(mod, "__load__", dir(mod)):
        # Avoid omitted names
        if attr.startswith(loaded._omit_start) or attr.endswith(loaded._omit_end):
            continue

        orig_name = attr
        # Get the function alias if available
        name = __func_alias__.get(attr, attr)
        obj = getattr(mod, orig_name)

        if inspect.isfunction(obj):
            # TODO save dunder methods in the module and attach them to the loadedmod object
            if loaded._omit_func:
                continue
            # It's a function, potentially make it async
            if not asyncio.iscoroutinefunction(obj):
                # Convert to async if not already
                func = pns.loop.make_async(obj)
            else:
                func = obj

            contracted_func = pns.contract.create_contracted(
                hub=loaded._,
                contracts=loaded.contracts,
                func=func,
                ref=loaded.__ref__,
                name=name,
                parent=loaded,
                implicit_hub=("hub" in func.__code__.co_varnames),
            )

            loaded._func[name] = contracted_func
        elif inspect.isclass(obj):
            # It's a class
            if loaded._omit_class:
                continue
            loaded._class[name] = obj
        else:
            if loaded._omit_vars:
                continue
            # It's a variable
            loaded._var[name] = obj
    return loaded

def load_from_path(modname: str, path: str, ext:str = ".py"):
    """
    Attempt to load the Python module named `modname` from the specified `path`.
    
    :param modname: The name of the module to load.
    :param path: The directory path to use as the anchor point to resolve the module.
    :return: The loaded module if successful, or None if not found.
    """
    # Convert the given path to a Path object and resolve the module file path
    module_path = pathlib.Path(path) / (modname.replace('.', '/') + ext)
    
    if not module_path.is_file():
        return None

    # Using the absolute path for the module
    spec = importlib.util.spec_from_file_location(modname, module_path.resolve())
    if spec is None:
        return None

    # Check if module already exists in sys.modules
    if modname in sys.modules:
        return sys.modules[modname]

    # Load the module
    module = importlib.util.module_from_spec(spec)
    try:
        sys.modules[modname] = module
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
    
    
    
