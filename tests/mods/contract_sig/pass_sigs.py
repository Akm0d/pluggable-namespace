async def __virtual__(hub):
    return getattr(hub, "LOAD_PASS", False), "Plugin not enabled"


async def args(hub, no_type_param, typed_param: str, *_): ...


async def kwargs(hub, no_type_param=None, typed_param: str = "", **__): ...


async def args_kwargs(
    hub,
    no_type_param,
    typed_param: str,
    no_type_param_default=None,
    typed_param_default: str = "",
    *_,
    **__,
): ...


async def async_func(hub): ...
