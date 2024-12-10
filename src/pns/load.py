import sys
import asyncio
import pns.contract
import pns.data

import importlib.util
VIRTUAL = "__virtual__"
CONFIG = "conf.yaml"



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

async def prep_mod(hub, sub, name:str, mod) -> pns.data.LoadedMod:
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

        if ret is False or (len(ret)>1 and ret[0] is False):
            raise NotImplementedError(f"{sub.__ref__}.{name} virtual failed: {ret[1]}")

    return pns.data.LoadedMod(name, module=mod, parent=sub, root=hub)
