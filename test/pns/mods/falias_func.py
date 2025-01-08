import os


async def __func_alias__(hub):
    out = {
        "list_": "list",
    }

    out["cpu_count"] = os.cpu_count
    out["λ"] = lambda: 0
    out["already_has_a_hub"] = hub.pop.sub.add
    out["async_func_wrap"] = _async_func

    return out


async def _async_func():
    return True


async def list_(hub):
    return ["list"]
