import sys
import asyncio
import pns.contract

import importlib.util
VIRTUAL = "__virtual__"
INIT = "__init__"
CONFIG = "conf.yaml"

class LoadedMod(pns.data.Namespace):
    def __getattr__(self, name:str):
        obj = getattr(self.mod, name)
        if asyncio.iscoroutinefunction(obj):
            func = obj
            return pns.contract.create_contracted(
                self._,
                contracts=self.__.contracts,
                func=func,
                ref=self.ref,
                parent=self.__,
                name=func.__name__,
                # Add the root hub to the function call if "hub" is an argument to the function
                implicit_hub=func.__code__.co_varnames and (func.__code__.co_varnames[0] == "hub"),
            )
        return obj

def load_module(path: str):
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

async def prep_mod(hub, sub, name:str, mod) -> LoadedMod:
    # Execute the __virtual__ function if present
    if hasattr(mod, VIRTUAL):
        virtual = pns.contract.Contracted(
            hub,
            contracts=[],
            func=getattr(mod, VIRTUAL),
            ref=f"{sub.ref}.{name}.{VIRTUAL}",
            parent=mod,
            name=VIRTUAL,
        )
        ret = virtual()
        if asyncio.iscoroutine(ret):
            ret = await ret

    # Execute the __init__ function if present
    if hasattr(mod, INIT):
        func = getattr(mod, INIT)
        if asyncio.iscoroutinefunction(func):
            init = pns.contract.Contracted(
                hub,
                contracts=[],
                func=func,
                ref=f"{sub.ref}.{name}.{INIT}",
                parent=mod,
                name=INIT,
            )
            ret = init()
            if asyncio.iscoroutine(ret):
                await ret

    return LoadedMod(name, module=mod, tree=sub, root=hub)
