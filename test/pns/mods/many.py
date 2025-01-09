__virtualname__ = "all"
_contracts__ = "all"
__func_alias__ = {
    "list_": "list",
    "dict_": "dict",
}


async def list_(hub):
    return ["list"]


async def dict_(hub):
    return {}
