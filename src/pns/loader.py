"""
Load the files detected from the scanner
"""

import asyncio
import importlib.machinery
import importlib.util
import inspect
import os
import sys
import types
from collections.abc import Callable

import cpns.contract
import cpns.data

BASE_TYPES = (int, float, str, bytes, bool, type(None))


class LoadError(Exception):
    edict: dict = None
    traceback = None

    def __init__(self, msg, exception=None, traceback=None, verror=None):
        self.edict = {
            "msg": msg,
            "exception": exception,
            "verror": verror,
        }
        self.traceback = traceback


def load_mod(modname: str, form: str, path: str) -> "LoadedMod":
    """
    Load a single module
    :param modname: The name of the module to get from the loader
    :param form: The name of the loader module
    :param path: The package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    """
    this = sys.modules[__name__]
    return getattr(this, form)(modname, path)


def python(modname: str, path: str) -> "LoadedMod" or LoadError:
    """
    Attempt to load the named python modules
    :param modname: The name of the module to get from the loader
    :param path: The package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    """
    if modname in sys.modules:
        return sys.modules[modname]
    spec = importlib.util.spec_from_file_location(modname, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[modname] = module
    module.__file__ = path
    spec.loader.exec_module(module)
    return module


def _base_name(bname: str, mod: "LoadedMod") -> tuple[str, str]:
    """
    Find the basename and alias of a loader module
    :param bname: The base name of the mod's path
    :param mod: A loader module or a LoadError if the module didn't load
    """
    base_name = os.path.basename(bname)
    return base_name, getattr(mod, "__virtualname__", base_name)


async def _load_virtual(
    hub,
    mod: "LoadedMod" or LoadError,
    bname: str,
    vtype: str,
    ref: str,
) -> dict[str, object]:
    """
    Run the virtual function to name the module and check for all loader
    errors
    :param hub: The redistributed pns central hub
    :param virtual: Toggle whether or not to process __virtual__ functions
    :param mod: A loader module or a LoadError if the module didn't load
    :param bname: The base name of the mod's path
    :param vtype: The name of the virtual function to call on the module I.E. __virtual__ or __sub_virtual__
    """
    base_name, name = _base_name(bname, mod)

    if not hasattr(mod, vtype):
        # No __virtual__ processing is required.
        # Return the mod's name as the defined __virtualname__ if defined,
        # else, the base_name
        return {"name": name}

    try:
        virtual_func = cpns.contract.Contracted(
            hub,
            contracts=[],
            func=getattr(mod, vtype),
            ref=f"{ref}.{name}",
            parent=mod,
            name="__virtual__",
        )
        vret = await virtual_func()
    except Exception as e:
        vret = False, str(e)

    verror = vret
    if isinstance(vret, tuple):
        if len(vret) > 1:
            verror = vret[1]
        vret = vret[0]

    if vret:
        # No problems occurred, module is allowed to load
        # Return the mod's name as the defined __virtualname__ if defined,
        # else, the base_name
        return {"name": name}
    else:
        # __virtual__ explicitly disabled the loading of this module
        err = LoadError(f"Module {bname} returned virtual FALSE", verror=verror)
        # Return the load error with name as the base_name because another
        # module is still allowed to load under the same __virtualname__
        # but also return the vname information
        return {"name": base_name, "vname": name, "error": err}


async def load_virtual(hub, mod: "LoadedMod" or LoadError, bname: str, ref: str) -> dict[str, object]:
    """
    Run the __virtual__ function to name the module and check for all loader errors
    :param hub: The redistributed pns central hub
    :param virtual: Toggle whether or not to process __virtual__ functions
    :param mod: A loader module or a LoadError if the module didn't load
    :param bname: The base name of the mod's path
    """
    return await _load_virtual(hub, mod, bname, "__virtual__", ref)


async def load_sub_virtual(hub, mod: "LoadedMod" or LoadError, bname: str, ref: str) -> dict[str, object]:
    """
    Run the __sub_virtual__ function to name the module and check for all loader errors
    :param hub: The redistributed pns central hub
    :param virtual: Toggle whether or not to process __virtual__ functions
    :param mod: A loader module or a LoadError if the module didn't load
    :param bname: The base name of the mod's path
    """
    _, name = _base_name(bname, mod)
    if name != "init":
        return {"name": name}
    return await _load_virtual(hub, mod, bname, "__sub_virtual__", ref)


async def mod_init(sub, mod: "LoadedMod", mod_name: str):
    """
    Process module's __init__ function if defined
    :param sub: The pns object that contains the loaded module data
    :param mod: A loader modul
    :param mod_name: The name of the module to get from the loader
    """
    if "__init__" in dir(mod):
        init = cpns.contract.Contracted(
            sub._hub,
            contracts=[],
            func=mod.__init__,
            ref=f"{sub._ref}.{mod_name}",
            parent=mod,
            name="__init__",
        )
        await init()


def sub_alias(this_sub, mod: "LoadedMod", mod_name: str):
    """
    Check the sub alias settings and apply the alias names locally so they can be gathered into the
        higher level object on the hub
    :param this_sub: The pns object that contains the loaded module data
    :param mod: A loader module
    :param mod_name: The name of the module to get from the loader
    """
    if mod_name == "init":
        alias = getattr(mod, "__sub_alias__", None)
        if alias:
            this_sub._alias = alias


async def prep_loaded_mod(
    this_sub,
    mod: "LoadedMod",
    mod_name: str,
    contracts: list["cpns.contract.Wrapper"],
    recursive_contracts: list["cpns.contract.Wrapper"],
) -> "LoadedMod":
    ordered_contracts = contracts + recursive_contracts

    lmod = this_sub._loaded.get(mod_name, LoadedMod(mod_name, parent=this_sub))

    # getattr(hub, ref) should resolve to this module
    ref = f"{this_sub._ref}.{mod_name}"

    sub_alias(this_sub, mod, mod_name)
    func_alias_dict: dict[str, str | Callable | cpns.contract.Contracted] = {}

    __func_alias__: Callable | dict[str, str | Callable] = getattr(mod, "__func_alias__", {})
    if asyncio.iscoroutinefunction(__func_alias__):
        func_alias_dict.update(await __func_alias__(this_sub._hub))
    else:
        func_alias_dict.update(__func_alias__)

    for attr in getattr(mod, "__load__", dir(mod)):
        func_alias: str | Callable = func_alias_dict.get(attr, attr)
        func = getattr(mod, attr)
        name = func_alias if isinstance(func_alias, str) else attr

        if not this_sub._omit_vars and not (
            inspect.isfunction(func) or inspect.isclass(func) or type(func).__name__ == "cython_function_or_method"
        ):
            setattr(lmod, name, func)
            continue

        if attr.startswith(tuple(this_sub._omit_start)) or attr.endswith(tuple(this_sub._omit_end)):
            continue

        if inspect.isfunction(func) or inspect.isbuiltin(func) or type(func).__name__ == "cython_function_or_method":
            obj = cpns.contract.create_contracted(this_sub._hub, ordered_contracts, func, ref, name, parent=lmod)
            if not this_sub._omit_func and (not this_sub._pypath or func.__module__.startswith(mod.__name__)):
                lmod._funcs[name] = obj
        elif not this_sub._omit_class and inspect.isclass(func) and func.__module__.startswith(mod.__name__):
            lmod._classes[name] = func

    for attr, func_alias in func_alias_dict.items():
        if isinstance(func_alias, cpns.contract.Contracted):
            obj = func_alias
        elif isinstance(func_alias, Callable):
            obj = cpns.contract.create_contracted(
                this_sub._hub,
                ordered_contracts,
                func_alias,
                ref,
                attr,
                parent=lmod,
                implicit_hub=False,
            )
        else:
            continue
        lmod._funcs[attr] = obj

    return lmod


class LoadedMod(types.ModuleType, cpns.data.LoadedModGetAttr):
    """
    The LoadedMod class allows for the module loaded onto the sub to return
    custom sequencing, for instance it can be iterated over to return all
    functions
    """

    def __init__(self, name: str, parent: "cpns.hub.Sub"):
        super().__init__(name)
        _vars: dict[str, object] = {}
        funcs: dict[str, object] = {}
        classes: dict[str, object] = {}
        self._attrs = cpns.data.MultidictCache([funcs, classes, _vars], parent=parent)
        self._vars = _vars
        self._funcs = funcs
        self._classes = classes

    def __getitem__(self, item: str):
        return self._attrs[item]

    def __setattr__(self, item: str, value):
        if item.startswith("_"):
            object.__setattr__(self, item, value)
            return
        elif isinstance(value, types.FunctionType):
            self._funcs[item] = value
        elif isinstance(value, type):
            self._classes[item] = value
        else:
            self._vars[item] = value
        self._attrs._clear()

    def __getstate__(self):
        return {"vars": {k: v for k, v in self._vars.items() if isinstance(v, BASE_TYPES)}}

    def __setstate__(self, state: dict[str, any]):
        self._vars.update(state["vars"])

    def __iter__(self):
        return iter(self._attrs)

    @property
    def _ref(self) -> str:
        """
        Return a full path on the hub to this mod
        """
        ref = self.__name__
        root = self._attrs._parent
        while hasattr(root, "_subname"):
            ref = f"{root._subname}.{ref}"
            root = root._parent
        return ref
