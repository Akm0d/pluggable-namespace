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

class LoadedMod(pns.hub.Namespace):
    def __init__(self, mod: ModuleType, **kwargs):
        super().__init__(**kwargs)
        self._var = {}
        self._func = {}
        self._class = {}
        
        # Sort attributes from the module
        self._populate(mod)
        
        self._nest = self._attrs

    def _populate(self, mod: ModuleType):
        # Iterate over all attributes in the module
        for name, obj in mod.__dict__.items():
            # TODO save dunder methods in the module and attach them to the loadedmod object
            if name[0] in self._omit_start or name[-1] in self._omit_end:
                continue
            if inspect.isfunction(obj) and not self._omit_func:
                if asyncio.iscoroutinefunction(obj):
                    func = obj
                else:
                    func = pns.loop.make_async(obj)
                
                self._func[name] = pns.contract.create_contracted(
                    self._,
                    contracts=self.__.contracts,
                    func=func,
                    ref=self.__ref__,
                    parent=self.__,
                    name=func.__name__,
                    # Add the root hub to the function call if "hub" is an argument to the function
                    implicit_hub=func.__code__.co_varnames
                    and (func.__code__.co_varnames[0] == "hub"),
                )
            elif inspect.isclass(obj) and not self._omit_class:
                self._class[name] = obj
            elif not self._omit_vars:
                # Consider remaining objects as variables
                self._var[name] = obj
        ...
        
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

    loaded = LoadedMod(mod, name=name, parent=sub, root=hub)
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
    
    
    
