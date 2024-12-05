import os


async def _async_func():
    return True


__func_alias__ = {
    "list_": "list",
    "cpu_count": os.cpu_count,
    "λ": lambda: 0,
    "async_func_wrap": _async_func,
}


async def list_(hub):
    return ["list"]
